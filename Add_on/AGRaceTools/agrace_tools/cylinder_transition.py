# SPDX-FileCopyrightText: 2026 尾黒こう (Ryuban)
# SPDX-License-Identifier: GPL-3.0-or-later

import math

import bmesh
import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty
from mathutils import Matrix, Vector

from .translations import AGRACE_TRANSLATION_CONTEXT, tr


MODE_EDGE_TO_SEMI = "EDGE_TO_SEMI"
MODE_EDGE_TO_CIRCLE = "EDGE_TO_CIRCLE"
MODE_SEMI_TO_CIRCLE = "SEMI_TO_CIRCLE"

CONNECT_UPPER_INNER = "UPPER_INNER"
CONNECT_UPPER_OUTER = "UPPER_OUTER"

SURFACE_BOTH = "BOTH"
SURFACE_INNER = "INNER"
SURFACE_OUTER = "OUTER"

RADIUS_INNER = "INNER"
RADIUS_MIDDLE = "MIDDLE"
RADIUS_OUTER = "OUTER"

EPSILON = 1.0e-6
SEAM_TOLERANCE = 1.0e-5
DEFAULT_ARC_ANGLE = math.radians(90.0)
MIN_ARC_ANGLE = math.radians(10.0)
MAX_ARC_ANGLE = math.radians(180.0)
_UPDATING_OPERATOR_CUSTOM_ANGLE = False
SECTION_Y_TOLERANCE = 1.0e-2
UV_NORMAL_MIN = 0.4
UV_NORMAL_MAX = 1.0
UV_RECEIVER_MIN = 0.2
UV_RECEIVER_MAX = 0.4
UV_SIDE_MIN = 0.1
UV_SIDE_MAX = 0.199
UV_CAP_MIN = 0.0
UV_CAP_MAX = 0.1


class CylinderTransitionError(RuntimeError):
    def __init__(self, code, message, **values):
        super().__init__(message)
        self.code = code
        self.message = message
        self.values = values

    def localized(self):
        return tr(self.message).format(**self.values)

    def english(self):
        return self.message.format(**self.values)


def smootherstep(t):
    return 6.0 * t**5 - 15.0 * t**4 + 10.0 * t**3


def lerp(a, b, t):
    return a + (b - a) * t


def normalized_angle_delta(start, end):
    return (end - start + math.pi) % (2.0 * math.pi) - math.pi


def lerp_angle(start, end, t):
    return start + normalized_angle_delta(start, end) * t


def align_angle_to_reference(angle, reference):
    return reference + normalized_angle_delta(reference, angle)


def guided_angle_components(start, guide, end):
    guide = align_angle_to_reference(guide, start)
    end = align_angle_to_reference(end, guide)
    control = 2.0 * guide - 0.5 * (start + end)
    return start, control, end


def quadratic_bezier_value(start, control, end, weight):
    inverse = 1.0 - weight
    return (
        inverse * inverse * start
        + 2.0 * inverse * weight * control
        + weight * weight * end
    )


def guided_angle(start, guide, end, weight):
    return quadratic_bezier_value(
        *guided_angle_components(start, guide, end), weight
    )


def quadratic_bezier_minimum(start, control, end):
    minimum = min(start, end)
    denominator = start - 2.0 * control + end
    if abs(denominator) > EPSILON:
        weight = (start - control) / denominator
        if 0.0 < weight < 1.0:
            minimum = min(
                minimum,
                quadratic_bezier_value(start, control, end, weight),
            )
    return minimum


def validate_guided_angle_order(source_angles, guide_angles, end_angles, direction):
    components = [
        guided_angle_components(start, guide, end)
        for start, guide, end in zip(source_angles, guide_angles, end_angles)
    ]
    for first, second in zip(components, components[1:]):
        separation = tuple(
            direction * (second_value - first_value)
            for first_value, second_value in zip(first, second)
        )
        if quadratic_bezier_minimum(*separation) <= EPSILON:
            raise CylinderTransitionError(
                "CT035",
                "Adjust the selected edge shape or Radius so its vertex order does not reverse during the transition through the virtual semicircle.",
            )


def vector_xz(angle, length=1.0):
    return Vector((math.cos(angle) * length, 0.0, math.sin(angle) * length))


def xz_radius(point, center_z):
    return math.hypot(point.x, point.z - center_z)


def xz_angle(point, center_z):
    return math.atan2(point.z - center_z, point.x)


def radius_side(radius, target_radius):
    difference = radius - target_radius
    if difference < -SEAM_TOLERANCE:
        return -1
    if difference > SEAM_TOLERANCE:
        return 1
    return 0


def validate_radius_convergence(
    radius,
    target_radius,
    start_side,
    closest_gap,
    code,
    message,
):
    current_side = radius_side(radius, target_radius)
    current_gap = abs(radius - target_radius)
    crossed_target = (
        current_side != 0
        and (start_side == 0 or current_side != start_side)
    )
    moved_away = current_gap > closest_gap + SEAM_TOLERANCE
    if crossed_target or moved_away:
        raise CylinderTransitionError(code, message)
    return min(closest_gap, current_gap)


def selected_edge_components(bm):
    selected_edges = [edge for edge in bm.edges if edge.select and not edge.hide]
    if not selected_edges:
        raise CylinderTransitionError("CT003", "Select one or two open half-width edge chains.")

    remaining = set(selected_edges)
    components = []
    while remaining:
        start_edge = remaining.pop()
        component = {start_edge}
        stack = [start_edge]
        while stack:
            edge = stack.pop()
            for vertex in edge.verts:
                for linked_edge in vertex.link_edges:
                    if linked_edge in remaining:
                        remaining.remove(linked_edge)
                        component.add(linked_edge)
                        stack.append(linked_edge)
        components.append(component)
    return components


def order_vertices_from_seam(edges, scale):
    adjacency = {}
    for edge in edges:
        v0, v1 = edge.verts
        adjacency.setdefault(v0, []).append(v1)
        adjacency.setdefault(v1, []).append(v0)

    endpoints = [vertex for vertex, neighbours in adjacency.items() if len(neighbours) == 1]
    if len(endpoints) == 0:
        raise CylinderTransitionError(
            "CT005", "Closed loops are not supported. Select open edge chains."
        )
    if len(endpoints) != 2:
        raise CylinderTransitionError(
            "CT007", "A selected edge chain is branched. Select one continuous chain."
        )

    def working_x(vertex):
        return vertex.co.x * scale.x

    start = min(
        endpoints,
        key=lambda vertex: (
            abs(working_x(vertex)),
            vertex.co.z * scale.z,
            vertex.co.y * scale.y,
            vertex.index,
        ),
    )
    if abs(working_x(start)) > SEAM_TOLERANCE:
        raise CylinderTransitionError(
            "CT010", "Place the center-side endpoint of each selected edge chain at local X = 0."
        )

    ordered = []
    previous = None
    current = start
    while True:
        ordered.append(current)
        candidates = [vertex for vertex in adjacency[current] if vertex != previous]
        if not candidates:
            break
        if len(candidates) > 1:
            raise CylinderTransitionError(
                "CT007", "A selected edge chain is branched. Select one continuous chain."
            )
        previous, current = current, candidates[0]
    return ordered


def decompose_working_transform(obj):
    if any(component <= 0.0 for component in obj.scale):
        raise CylinderTransitionError(
            "CT018", "Negative or zero object scale is not supported."
        )

    location, rotation, scale = obj.matrix_world.decompose()
    no_scale = Matrix.Translation(location) @ rotation.to_matrix().to_4x4()
    scale_matrix = Matrix.Diagonal((scale.x, scale.y, scale.z, 1.0))
    reconstructed = no_scale @ scale_matrix
    difference = max(
        abs(obj.matrix_world[row][column] - reconstructed[row][column])
        for row in range(4)
        for column in range(4)
    )
    if difference > 1.0e-5:
        raise CylinderTransitionError(
            "CT019", "Sheared object transforms are not supported."
        )
    return Vector((scale.x, scale.y, scale.z)), no_scale


def to_working_position(vertex, scale):
    position = Vector(
        (
            vertex.co.x * scale.x,
            vertex.co.y * scale.y,
            vertex.co.z * scale.z,
        )
    )
    if abs(position.x) <= SEAM_TOLERANCE:
        position.x = 0.0
    return position


def validate_source_chain(points):
    if len(points) < 2:
        raise CylinderTransitionError("CT011", "An edge chain needs at least two vertices.")
    y_min = min(point.y for point in points)
    y_max = max(point.y for point in points)
    if y_max - y_min > SECTION_Y_TOLERANCE + EPSILON:
        raise CylinderTransitionError(
            "CT012", "Align the local Y coordinates of the selected edge-chain vertices."
        )
    if abs(points[0].x) > SEAM_TOLERANCE:
        raise CylinderTransitionError(
            "CT010", "Place the center-side endpoint of each selected edge chain at local X = 0."
        )
    if any(point.x < -SEAM_TOLERANCE for point in points):
        raise CylinderTransitionError(
            "CT013", "Place the center-side endpoint at local X = 0 and keep the entire selected edge chain on the local +X side."
        )


def inspect_selection(context):
    obj = context.edit_object
    if obj is None or obj.type != "MESH":
        return {"count": 0, "counts": (), "message": tr("Enter Mesh Edit Mode to inspect edge chains.")}
    try:
        scale, _matrix = decompose_working_transform(obj)
        bm = bmesh.from_edit_mesh(obj.data)
        components = selected_edge_components(bm)
        ordered = [order_vertices_from_seam(component, scale) for component in components]
        return {
            "count": len(ordered),
            "counts": tuple(len(chain) for chain in ordered),
            "message": "",
        }
    except CylinderTransitionError as error:
        return {"count": 0, "counts": (), "message": error.localized()}


def derive_radii(radius, radius_reference, thickness):
    if radius <= 0.0:
        raise CylinderTransitionError("CT020", "Radius must be greater than zero.")
    if thickness <= 0.0:
        raise CylinderTransitionError("CT021", "Thickness must be greater than zero.")

    if radius_reference == RADIUS_INNER:
        inner = radius
        middle = radius + thickness * 0.5
        outer = radius + thickness
    elif radius_reference == RADIUS_MIDDLE:
        inner = radius - thickness * 0.5
        middle = radius
        outer = radius + thickness * 0.5
    else:
        inner = radius - thickness
        middle = radius - thickness * 0.5
        outer = radius

    if inner <= EPSILON:
        raise CylinderTransitionError(
            "CT022", "Increase Radius or reduce Thickness so the inner radius is greater than zero."
        )
    return inner, middle, outer


def rounded_arc_angle(custom_angle):
    degrees = round(math.degrees(custom_angle), 1)
    degrees = max(10.0, min(180.0, degrees))
    return math.radians(degrees)


def normalized_arc_angle(use_custom_angle, custom_angle):
    if not use_custom_angle:
        return DEFAULT_ARC_ANGLE
    return rounded_arc_angle(custom_angle)


def update_operator_custom_angle(operator, _context):
    global _UPDATING_OPERATOR_CUSTOM_ANGLE
    if _UPDATING_OPERATOR_CUSTOM_ANGLE:
        return
    rounded = rounded_arc_angle(operator.custom_angle)
    if abs(operator.custom_angle - rounded) > 1.0e-12:
        _UPDATING_OPERATOR_CUSTOM_ANGLE = True
        try:
            operator.custom_angle = rounded
        finally:
            _UPDATING_OPERATOR_CUSTOM_ANGLE = False


def arc_is_circle(arc_angle):
    return abs(arc_angle - math.pi) <= EPSILON


def arc_angles(vertex_count, connection, sweep_angle):
    if vertex_count < 2:
        raise CylinderTransitionError("CT023", "Half-width Vertex Count must be at least 2.")
    if sweep_angle == "SEMI":
        sweep_angle = DEFAULT_ARC_ANGLE
    elif sweep_angle == "CIRCLE":
        sweep_angle = math.pi
    contact = -math.pi * 0.5 if connection == CONNECT_UPPER_INNER else math.pi * 0.5
    direction = 1.0 if connection == CONNECT_UPPER_INNER else -1.0
    end = contact + direction * sweep_angle
    return [lerp(contact, end, index / (vertex_count - 1)) for index in range(vertex_count)]


def arc_ring(angles, radius, center_z, y):
    return [
        Vector((math.cos(angle) * radius, y, center_z + math.sin(angle) * radius))
        for angle in angles
    ]


def unwrap_and_validate_angles(points, center_z, direction):
    raw = [xz_angle(point, center_z) for point in points]
    unwrapped = [raw[0]]
    for angle in raw[1:]:
        previous = unwrapped[-1]
        delta = normalized_angle_delta(previous, angle)
        current = previous + delta
        if direction * (current - previous) <= EPSILON:
            raise CylinderTransitionError(
                "CT024",
                "Adjust the selected edge shape so its vertex order does not reverse around the circle center.",
            )
        unwrapped.append(current)
    return unwrapped


def direction_for_angles(angles):
    delta = angles[-1] - angles[0]
    return 1.0 if delta > 0.0 else -1.0


def interpolate_hint(source_hint, target_hint, weight):
    source_angle = math.atan2(source_hint.z, source_hint.x)
    target_angle = math.atan2(target_hint.z, target_hint.x)
    return vector_xz(lerp_angle(source_angle, target_angle, weight))


def build_single_stage(
    source,
    source_hints,
    center_z,
    target_radius,
    target_angles,
    target_y,
    divisions,
    surface,
):
    if divisions < 1:
        raise CylinderTransitionError("CT025", "Y Divisions must be at least 1.")
    direction = direction_for_angles(target_angles)
    source_angles = unwrap_and_validate_angles(source, center_z, direction)
    source_radii = [xz_radius(point, center_z) for point in source]
    radius_sides = [radius_side(radius, target_radius) for radius in source_radii]
    closest_gaps = [abs(radius - target_radius) for radius in source_radii]

    rings = []
    hints = []
    source_y = sum(point.y for point in source) / len(source)
    for division in range(divisions + 1):
        t = division / divisions
        weight = smootherstep(t)
        y = lerp(source_y, target_y, t)
        ring = []
        ring_hints = []
        for index, (source_point, radius0, angle0, angle1) in enumerate(
            zip(source, source_radii, source_angles, target_angles)
        ):
            radius = target_radius + (radius0 - target_radius) * (1.0 - weight)
            closest_gaps[index] = validate_radius_convergence(
                radius,
                target_radius,
                radius_sides[index],
                closest_gaps[index],
                "CT026",
                "The generated surface crosses its target circle or moves away from it before the end.",
            )
            angle = lerp(angle0, angle1, weight)
            position = Vector(
                (math.cos(angle) * radius, y, center_z + math.sin(angle) * radius)
            )
            radial = vector_xz(angle)
            target_hint = -radial if surface == SURFACE_INNER else radial
            hint = interpolate_hint(source_hints[index], target_hint, weight)
            ring.append(source_point.copy() if division == 0 else position)
            ring_hints.append(source_hints[index].copy() if division == 0 else hint)
        rings.append(ring)
        hints.append(ring_hints)
    return rings, hints


def build_paired_stage(
    inner_source,
    outer_source,
    center_z,
    inner_radius,
    middle_radius,
    outer_radius,
    target_angles,
    target_y,
    divisions,
):
    source_middle = [(inner + outer) * 0.5 for inner, outer in zip(inner_source, outer_source)]
    source_delta = [outer - inner for inner, outer in zip(inner_source, outer_source)]
    for delta in source_delta:
        if delta.length <= EPSILON:
            raise CylinderTransitionError("CT027", "Upper and lower edges overlap.")

    direction = direction_for_angles(target_angles)
    source_angles = unwrap_and_validate_angles(source_middle, center_z, direction)
    source_radii = [xz_radius(point, center_z) for point in source_middle]
    inner_start_radii = [xz_radius(point, center_z) for point in inner_source]
    outer_start_radii = [xz_radius(point, center_z) for point in outer_source]
    inner_radius_sides = [radius_side(radius, inner_radius) for radius in inner_start_radii]
    outer_radius_sides = [radius_side(radius, outer_radius) for radius in outer_start_radii]
    inner_closest_gaps = [abs(radius - inner_radius) for radius in inner_start_radii]
    outer_closest_gaps = [abs(radius - outer_radius) for radius in outer_start_radii]

    thickness = outer_radius - inner_radius
    source_y = sum(point.y for point in source_middle) / len(source_middle)
    inner_rings = []
    outer_rings = []
    inner_hints = []
    outer_hints = []

    for division in range(divisions + 1):
        t = division / divisions
        weight = smootherstep(t)
        y = lerp(source_y, target_y, t)
        inner_ring = []
        outer_ring = []
        inner_hint_ring = []
        outer_hint_ring = []

        for index, (radius0, angle0, angle1, delta0) in enumerate(
            zip(source_radii, source_angles, target_angles, source_delta)
        ):
            radius = middle_radius + (radius0 - middle_radius) * (1.0 - weight)
            angle = lerp(angle0, angle1, weight)
            middle = Vector(
                (math.cos(angle) * radius, y, center_z + math.sin(angle) * radius)
            )
            source_delta_angle = math.atan2(delta0.z, delta0.x)
            delta_angle = lerp_angle(source_delta_angle, angle1, weight)
            delta_length = lerp(delta0.length, thickness, weight)
            delta = vector_xz(delta_angle, delta_length)
            inner = middle - delta * 0.5
            outer = middle + delta * 0.5

            if division == 0:
                inner = inner_source[index].copy()
                outer = outer_source[index].copy()
                delta = delta0.copy()

            inner_closest_gaps[index] = validate_radius_convergence(
                xz_radius(inner, center_z),
                inner_radius,
                inner_radius_sides[index],
                inner_closest_gaps[index],
                "CT028",
                "The generated inner surface crosses its target circle or moves away from it before the end.",
            )
            outer_closest_gaps[index] = validate_radius_convergence(
                xz_radius(outer, center_z),
                outer_radius,
                outer_radius_sides[index],
                outer_closest_gaps[index],
                "CT029",
                "The generated outer surface crosses its target circle or moves away from it before the end.",
            )

            outward = delta.normalized()
            inner_ring.append(inner)
            outer_ring.append(outer)
            inner_hint_ring.append(-outward)
            outer_hint_ring.append(outward)

        inner_rings.append(inner_ring)
        outer_rings.append(outer_ring)
        inner_hints.append(inner_hint_ring)
        outer_hints.append(outer_hint_ring)

    return inner_rings, outer_rings, inner_hints, outer_hints


def build_direct_single_transition(
    source,
    source_hints,
    center_z,
    target_radius,
    semi_angles,
    circle_angles,
    target_y,
    divisions,
    surface,
):
    if divisions < 2:
        raise CylinderTransitionError(
            "CT016", "This generation type needs at least {count} Y divisions.", count=2
        )
    direction = direction_for_angles(circle_angles)
    source_angles = unwrap_and_validate_angles(source, center_z, direction)
    validate_guided_angle_order(source_angles, semi_angles, circle_angles, direction)
    source_radii = [xz_radius(point, center_z) for point in source]
    radius_sides = [radius_side(radius, target_radius) for radius in source_radii]
    closest_gaps = [abs(radius - target_radius) for radius in source_radii]

    source_y = sum(point.y for point in source) / len(source)
    rings = []
    hints = []
    previous_angles = None
    for division in range(divisions + 1):
        t = division / divisions
        weight = smootherstep(t)
        y = lerp(source_y, target_y, t)
        ring = []
        ring_hints = []
        ring_angles = []

        for index, (source_point, radius0, angle0, semi_angle, circle_angle) in enumerate(
            zip(source, source_radii, source_angles, semi_angles, circle_angles)
        ):
            angle = guided_angle(angle0, semi_angle, circle_angle, weight)
            radius = target_radius + (radius0 - target_radius) * (1.0 - weight)
            closest_gaps[index] = validate_radius_convergence(
                radius,
                target_radius,
                radius_sides[index],
                closest_gaps[index],
                "CT026",
                "The generated surface crosses its target circle or moves away from it before the end.",
            )
            position = Vector(
                (math.cos(angle) * radius, y, center_z + math.sin(angle) * radius)
            )
            radial = vector_xz(circle_angle)
            target_hint = -radial if surface == SURFACE_INNER else radial
            hint = interpolate_hint(source_hints[index], target_hint, weight)
            ring.append(source_point.copy() if division == 0 else position)
            ring_hints.append(source_hints[index].copy() if division == 0 else hint)
            ring_angles.append(angle)

        for first, second in zip(ring_angles, ring_angles[1:]):
            if direction * (second - first) <= EPSILON:
                raise CylinderTransitionError(
                    "CT036", "Adjust the selected edge shape or Radius so its vertex order does not reverse during the transition to the circle."
                )
        if previous_angles is not None:
            for previous, current in zip(previous_angles, ring_angles):
                if not math.isfinite(current - previous):
                    raise CylinderTransitionError("CT037", "The continuous transition is invalid.")
        previous_angles = ring_angles
        rings.append(ring)
        hints.append(ring_hints)
    return rings, hints


def build_direct_paired_transition(
    inner_source,
    outer_source,
    center_z,
    inner_radius,
    middle_radius,
    outer_radius,
    semi_angles,
    circle_angles,
    target_y,
    divisions,
):
    if divisions < 2:
        raise CylinderTransitionError(
            "CT016", "This generation type needs at least {count} Y divisions.", count=2
        )
    source_middle = [(inner + outer) * 0.5 for inner, outer in zip(inner_source, outer_source)]
    source_delta = [outer - inner for inner, outer in zip(inner_source, outer_source)]
    for delta in source_delta:
        if delta.length <= EPSILON:
            raise CylinderTransitionError("CT027", "Upper and lower edges overlap.")

    direction = direction_for_angles(circle_angles)
    source_angles = unwrap_and_validate_angles(source_middle, center_z, direction)
    validate_guided_angle_order(source_angles, semi_angles, circle_angles, direction)
    source_radii = [xz_radius(point, center_z) for point in source_middle]
    inner_start_radii = [xz_radius(point, center_z) for point in inner_source]
    outer_start_radii = [xz_radius(point, center_z) for point in outer_source]
    inner_radius_sides = [radius_side(radius, inner_radius) for radius in inner_start_radii]
    outer_radius_sides = [radius_side(radius, outer_radius) for radius in outer_start_radii]
    inner_closest_gaps = [abs(radius - inner_radius) for radius in inner_start_radii]
    outer_closest_gaps = [abs(radius - outer_radius) for radius in outer_start_radii]

    thickness = outer_radius - inner_radius
    source_y = sum(point.y for point in source_middle) / len(source_middle)
    inner_rings = []
    outer_rings = []
    inner_hints = []
    outer_hints = []

    for division in range(divisions + 1):
        t = division / divisions
        weight = smootherstep(t)
        y = lerp(source_y, target_y, t)
        inner_ring = []
        outer_ring = []
        inner_hint_ring = []
        outer_hint_ring = []
        ring_angles = []

        for index, (radius0, angle0, semi_angle, circle_angle, delta0) in enumerate(
            zip(source_radii, source_angles, semi_angles, circle_angles, source_delta)
        ):
            angle = guided_angle(angle0, semi_angle, circle_angle, weight)
            radius = middle_radius + (radius0 - middle_radius) * (1.0 - weight)
            middle = Vector(
                (math.cos(angle) * radius, y, center_z + math.sin(angle) * radius)
            )

            delta_start = math.atan2(delta0.z, delta0.x)
            delta_angle = guided_angle(delta_start, semi_angle, circle_angle, weight)
            delta_length = lerp(delta0.length, thickness, weight)
            delta = vector_xz(delta_angle, delta_length)
            inner = middle - delta * 0.5
            outer = middle + delta * 0.5

            if division == 0:
                inner = inner_source[index].copy()
                outer = outer_source[index].copy()
                delta = delta0.copy()

            inner_closest_gaps[index] = validate_radius_convergence(
                xz_radius(inner, center_z),
                inner_radius,
                inner_radius_sides[index],
                inner_closest_gaps[index],
                "CT028",
                "The generated inner surface crosses its target circle or moves away from it before the end.",
            )
            outer_closest_gaps[index] = validate_radius_convergence(
                xz_radius(outer, center_z),
                outer_radius,
                outer_radius_sides[index],
                outer_closest_gaps[index],
                "CT029",
                "The generated outer surface crosses its target circle or moves away from it before the end.",
            )

            outward = delta.normalized()
            inner_ring.append(inner)
            outer_ring.append(outer)
            inner_hint_ring.append(-outward)
            outer_hint_ring.append(outward)
            ring_angles.append(angle)

        for first, second in zip(ring_angles, ring_angles[1:]):
            if direction * (second - first) <= EPSILON:
                raise CylinderTransitionError(
                    "CT036", "Adjust the selected edge shape or Radius so its vertex order does not reverse during the transition to the circle."
                )
        inner_rings.append(inner_ring)
        outer_rings.append(outer_ring)
        inner_hints.append(inner_hint_ring)
        outer_hints.append(outer_hint_ring)

    return inner_rings, outer_rings, inner_hints, outer_hints


def combine_stages(first, second):
    return first + second[1:]


def receiver_extension_delta(ring):
    second = ring[-1]
    third = ring[-2]
    direction = second - third
    direction.y = 0.0
    if direction.length <= EPSILON:
        raise CylinderTransitionError(
            "CT041",
            "The second and third outermost vertices overlap, so the raycast receiver direction cannot be calculated.",
        )
    return direction.normalized() * 3.0


def clamp_receiver_to_mirror_seam(second, candidate):
    if second.x <= SEAM_TOLERANCE:
        result = second.copy()
        result.x = 0.0
        return result
    denominator = second.x - candidate.x
    if denominator <= EPSILON:
        result = candidate.copy()
        result.x = 0.0
        return result
    factor = max(0.0, min(1.0, second.x / denominator))
    result = second.lerp(candidate, factor)
    result.x = 0.0
    return result


def receiver_vertical_delta(connection):
    vertical_sign = 1.0 if connection == CONNECT_UPPER_INNER else -1.0
    return Vector((0.0, 0.0, 3.0 * vertical_sign))


def arc_receiver_delta(arc_angle, connection):
    vertical_sign = 1.0 if connection == CONNECT_UPPER_INNER else -1.0
    return Vector(
        (
            math.cos(arc_angle) * 3.0,
            0.0,
            math.sin(arc_angle) * 3.0 * vertical_sign,
        )
    )


def append_raycast_receiver_rings(
    rings,
    hints,
    source_special,
    mode,
    source_arc_delta=None,
    target_arc_delta=None,
    source_is_circle=False,
    target_is_circle=False,
):
    ring_total = len(rings) - 1
    crossed_mirror_seam = source_is_circle

    if source_special is not None and not source_is_circle:
        source_delta = source_special - rings[0][-1]
        if source_delta.length <= EPSILON:
            raise CylinderTransitionError(
                "CT038", "The raycast receiver vertex overlaps the preceding vertex."
            )

    for ring_index, (ring, hint_ring) in enumerate(zip(rings, hints)):
        t = ring_index / ring_total
        weight = smootherstep(t)
        extension_delta = receiver_extension_delta(ring)

        if ring_index == 0 and source_is_circle:
            special = ring[-1].copy()
        elif ring_index == 0 and source_special is not None:
            special = source_special.copy()
        elif mode == MODE_EDGE_TO_SEMI and target_arc_delta is not None:
            delta = extension_delta.lerp(target_arc_delta, weight)
            special = ring[-1] + delta
        elif mode == MODE_SEMI_TO_CIRCLE and source_arc_delta is not None:
            delta = source_arc_delta.lerp(extension_delta, weight)
            special = ring[-1] + delta
        else:
            special = ring[-1] + extension_delta

        if target_is_circle and ring_index == ring_total:
            crossed_mirror_seam = True
        elif special.x <= SEAM_TOLERANCE:
            crossed_mirror_seam = True
        if crossed_mirror_seam:
            special = clamp_receiver_to_mirror_seam(ring[-1], special)

        ring.append(special)
        hint_ring.append(hint_ring[-1].copy())


def polygon_normal(points):
    normal = Vector((0.0, 0.0, 0.0))
    for index, point in enumerate(points):
        following = points[(index + 1) % len(points)]
        normal.x += (point.y - following.y) * (point.z + following.z)
        normal.y += (point.z - following.z) * (point.x + following.x)
        normal.z += (point.x - following.x) * (point.y + following.y)
    return normal


def append_oriented_face(vertices, faces, face_uvs, indices, uvs, desired, code):
    points = [vertices[index] for index in indices]
    normal = polygon_normal(points)
    if normal.length <= EPSILON:
        raise CylinderTransitionError(code, "A generated face has nearly zero area.")
    if normal.dot(desired) < 0.0:
        indices = tuple(reversed(indices))
        uvs = tuple(reversed(uvs))
    faces.append(tuple(indices))
    face_uvs.append(tuple(uvs))


def append_consistent_face_group(vertices, faces, face_uvs, specifications, code):
    score = 0.0
    checked = []
    for indices, uvs, desired in specifications:
        points = [vertices[index] for index in indices]
        normal = polygon_normal(points)
        if normal.length <= EPSILON:
            raise CylinderTransitionError(code, "A generated face has nearly zero area.")
        checked.append((indices, uvs, desired, normal))
        if desired.length > EPSILON:
            score += normal.normalized().dot(desired.normalized())

    reverse_group = score < 0.0
    for indices, uvs, _desired, _normal in checked:
        if reverse_group:
            indices = tuple(reversed(indices))
            uvs = tuple(reversed(uvs))
        faces.append(tuple(indices))
        face_uvs.append(tuple(uvs))


def append_surface_grid(
    vertices,
    faces,
    face_uvs,
    rings,
    hints,
    surface_key,
    collapse_last=False,
    raycast_receiver=False,
):
    ring_count = len(rings)
    vertex_count = len(rings[0])
    indices = []
    for ring_index, ring in enumerate(rings):
        index_ring = []
        for vertex_index, point in enumerate(ring):
            if (
                collapse_last
                and ring_index == ring_count - 1
                and vertex_index == vertex_count - 1
            ):
                index_ring.append(index_ring[-1])
                continue
            index_ring.append(len(vertices))
            vertices.append(point.copy())
        indices.append(index_ring)

    specifications = []
    normal_last_vertex = vertex_count - 2 if raycast_receiver else vertex_count - 1
    normal_divisions = max(1, normal_last_vertex)
    for ring_index in range(ring_count - 1):
        u0 = ring_index / (ring_count - 1)
        u1 = (ring_index + 1) / (ring_count - 1)
        for vertex_index in range(vertex_count - 1):
            is_receiver_face = raycast_receiver and vertex_index == vertex_count - 2
            if is_receiver_face:
                v0 = UV_RECEIVER_MIN
                v1 = UV_RECEIVER_MAX
            else:
                v0 = lerp(
                    UV_NORMAL_MIN,
                    UV_NORMAL_MAX,
                    vertex_index / normal_divisions,
                )
                v1 = lerp(
                    UV_NORMAL_MIN,
                    UV_NORMAL_MAX,
                    (vertex_index + 1) / normal_divisions,
                )
            if (
                collapse_last
                and ring_index == ring_count - 2
                and vertex_index == vertex_count - 2
                ):
                face_indices = (
                    indices[ring_index][vertex_index],
                    indices[ring_index][vertex_index + 1],
                    indices[ring_index + 1][vertex_index],
                )
                uv_coordinates = ((u0, v0), (u0, v1), (u1, v0))
            else:
                face_indices = (
                    indices[ring_index][vertex_index],
                    indices[ring_index][vertex_index + 1],
                    indices[ring_index + 1][vertex_index + 1],
                    indices[ring_index + 1][vertex_index],
                )
                uv_coordinates = ((u0, v0), (u0, v1), (u1, v1), (u1, v0))
            desired = (
                hints[ring_index][vertex_index]
                + hints[ring_index][vertex_index + 1]
                + hints[ring_index + 1][vertex_index + 1]
                + hints[ring_index + 1][vertex_index]
            )
            specifications.append((face_indices, uv_coordinates, desired))
    append_consistent_face_group(
        vertices, faces, face_uvs, specifications, "CT030"
    )
    return indices


def append_closure_faces(
    vertices,
    faces,
    face_uvs,
    inner_indices,
    outer_indices,
    inner_rings,
    outer_rings,
    generate_sides,
    generate_caps,
    collapse_last=False,
    sharp_edges=None,
):
    ring_count = len(inner_rings)
    vertex_count = len(inner_rings[0])

    if generate_sides:
        boundary = vertex_count - 1
        boundary_is_mirror = all(
            abs(inner_rings[ring][boundary].x) <= SEAM_TOLERANCE
            and abs(outer_rings[ring][boundary].x) <= SEAM_TOLERANCE
            for ring in range(ring_count)
        )
        if not boundary_is_mirror:
            specifications = []
            for ring in range(ring_count - 1):
                u0 = ring / (ring_count - 1)
                u1 = (ring + 1) / (ring_count - 1)
                mid_boundary = (
                    inner_rings[ring][boundary]
                    + outer_rings[ring][boundary]
                    + inner_rings[ring + 1][boundary]
                    + outer_rings[ring + 1][boundary]
                ) * 0.25
                previous = max(0, boundary - 1)
                mid_previous = (
                    inner_rings[ring][previous]
                    + outer_rings[ring][previous]
                    + inner_rings[ring + 1][previous]
                    + outer_rings[ring + 1][previous]
                ) * 0.25
                desired = mid_boundary - mid_previous
                face_indices = (
                        inner_indices[ring][boundary],
                        outer_indices[ring][boundary],
                        outer_indices[ring + 1][boundary],
                        inner_indices[ring + 1][boundary],
                )
                specifications.append(
                    (
                        face_indices,
                        (
                            (u0, UV_SIDE_MIN),
                            (u0, UV_SIDE_MAX),
                            (u1, UV_SIDE_MAX),
                            (u1, UV_SIDE_MIN),
                        ),
                        desired,
                    )
                )
                if sharp_edges is not None:
                    sharp_edges.add(
                        tuple(sorted((inner_indices[ring][boundary], inner_indices[ring + 1][boundary])))
                    )
                    sharp_edges.add(
                        tuple(sorted((outer_indices[ring][boundary], outer_indices[ring + 1][boundary])))
                    )
            append_consistent_face_group(
                vertices, faces, face_uvs, specifications, "CT031"
            )

    if generate_caps:
        for ring, desired_y in ((0, -1.0), (ring_count - 1, 1.0)):
            desired = Vector((0.0, desired_y, 0.0))
            specifications = []
            for vertex_index in range(vertex_count - 1):
                if collapse_last and ring == ring_count - 1 and vertex_index == vertex_count - 2:
                    continue
                v0 = vertex_index / (vertex_count - 1)
                v1 = (vertex_index + 1) / (vertex_count - 1)
                face_indices = (
                        inner_indices[ring][vertex_index],
                        inner_indices[ring][vertex_index + 1],
                        outer_indices[ring][vertex_index + 1],
                        outer_indices[ring][vertex_index],
                )
                specifications.append(
                    (
                        face_indices,
                        (
                            (v0, UV_CAP_MIN),
                            (v1, UV_CAP_MIN),
                            (v1, UV_CAP_MAX),
                            (v0, UV_CAP_MAX),
                        ),
                        desired,
                    )
                )
                if sharp_edges is not None:
                    sharp_edges.add(
                        tuple(sorted((inner_indices[ring][vertex_index], inner_indices[ring][vertex_index + 1])))
                    )
                    sharp_edges.add(
                        tuple(sorted((outer_indices[ring][vertex_index], outer_indices[ring][vertex_index + 1])))
                    )
            append_consistent_face_group(
                vertices, faces, face_uvs, specifications, "CT032"
            )


def create_mesh_object(
    context,
    output_matrix,
    destination_collection,
    surface_rings,
    surface_hints,
    generate_sides,
    generate_caps,
    generate_uv,
    collapse_last=False,
    raycast_receiver=False,
):
    vertices = []
    faces = []
    face_uvs = []
    grid_indices = {}
    sharp_edges = set()

    for surface in (SURFACE_INNER, SURFACE_OUTER):
        if surface in surface_rings:
            grid_indices[surface] = append_surface_grid(
                vertices,
                faces,
                face_uvs,
                surface_rings[surface],
                surface_hints[surface],
                surface,
                collapse_last=collapse_last,
                raycast_receiver=raycast_receiver,
            )

    if SURFACE_INNER in surface_rings and SURFACE_OUTER in surface_rings:
        append_closure_faces(
            vertices,
            faces,
            face_uvs,
            grid_indices[SURFACE_INNER],
            grid_indices[SURFACE_OUTER],
            surface_rings[SURFACE_INNER],
            surface_rings[SURFACE_OUTER],
            generate_sides,
            generate_caps,
            collapse_last=collapse_last,
            sharp_edges=sharp_edges,
        )

    mesh = bpy.data.meshes.new("CylinderTransitionMesh")
    new_obj = bpy.data.objects.new("CylinderTransition", mesh)
    destination_collection.objects.link(new_obj)
    new_obj.matrix_world = output_matrix

    try:
        mesh.from_pydata([tuple(vertex) for vertex in vertices], [], faces)
        mesh.update(calc_edges=True)

        for polygon in mesh.polygons:
            polygon.use_smooth = True

        for edge in mesh.edges:
            edge.use_edge_sharp = tuple(sorted(edge.vertices)) in sharp_edges

        surface_attribute = mesh.attributes.new(
            name="agrace_surface", type="INT", domain="POINT"
        )
        ring_attribute = mesh.attributes.new(
            name="agrace_ring", type="INT", domain="POINT"
        )
        column_attribute = mesh.attributes.new(
            name="agrace_column", type="INT", domain="POINT"
        )
        assigned = set()
        for surface, surface_value in ((SURFACE_INNER, 1), (SURFACE_OUTER, 2)):
            for ring_index, index_ring in enumerate(grid_indices.get(surface, ())):
                for column_index, vertex_index in enumerate(index_ring):
                    if vertex_index in assigned:
                        continue
                    assigned.add(vertex_index)
                    surface_attribute.data[vertex_index].value = surface_value
                    ring_attribute.data[vertex_index].value = ring_index
                    column_attribute.data[vertex_index].value = column_index

        new_obj["agrace_generator"] = "cylinder_transition"
        new_obj["agrace_ring_count"] = len(next(iter(surface_rings.values())))
        new_obj["agrace_section_vertices"] = len(next(iter(surface_rings.values()))[0])
        new_obj["agrace_has_inner"] = SURFACE_INNER in surface_rings
        new_obj["agrace_has_outer"] = SURFACE_OUTER in surface_rings
        new_obj["agrace_raycast_receiver"] = bool(raycast_receiver)
        new_obj["agrace_collapsed_receiver"] = bool(collapse_last)

        if generate_uv:
            uv_layer = mesh.uv_layers.new(name="AGRaceUV")
            for polygon, polygon_uvs in zip(mesh.polygons, face_uvs):
                for loop_index, uv in zip(polygon.loop_indices, polygon_uvs):
                    uv_layer.data[loop_index].uv = uv

        mirror = new_obj.modifiers.new(name="X Mirror", type="MIRROR")
        mirror.use_axis[0] = True
        mirror.use_clip = True
        mirror.use_mirror_merge = True
        mirror.merge_threshold = SEAM_TOLERANCE
        if generate_uv and hasattr(mirror, "use_mirror_v"):
            mirror.use_mirror_v = False

        if context.mode == "OBJECT":
            for selected in context.selected_objects:
                selected.select_set(False)
            new_obj.select_set(True)
            context.view_layer.objects.active = new_obj
    except Exception:
        bpy.data.objects.remove(new_obj, do_unlink=True)
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
        raise

    return new_obj, len(vertices), len(faces)


def selected_outliner_collection(context):
    selected_ids = getattr(context, "selected_ids", ())
    collections = [item for item in selected_ids if isinstance(item, bpy.types.Collection)]
    if collections:
        return collections[0]

    screen = getattr(context, "screen", None)
    if screen is None:
        return None
    for area in screen.areas:
        if area.type != "OUTLINER":
            continue
        region = next((item for item in area.regions if item.type == "WINDOW"), None)
        if region is None:
            continue
        try:
            with context.temp_override(area=area, region=region):
                selected_ids = getattr(bpy.context, "selected_ids", ())
                collections = [
                    item for item in selected_ids if isinstance(item, bpy.types.Collection)
                ]
                if collections:
                    return collections[0]
        except RuntimeError:
            continue
    return None


def resolve_destination_collection(context, reference_obj):
    if reference_obj is not None:
        active_collection = context.collection
        if active_collection is not None and reference_obj.name in active_collection.objects:
            return active_collection
        if reference_obj.users_collection:
            return reference_obj.users_collection[0]
    outliner_collection = selected_outliner_collection(context)
    return outliner_collection or context.scene.collection


def selection_data(context, obj, scale):
    if context.edit_object is not obj:
        raise CylinderTransitionError("CT002", "Mesh must be in Edit Mode for this generation type.")
    bm = bmesh.from_edit_mesh(obj.data)
    components = selected_edge_components(bm)
    if len(components) not in {1, 2}:
        raise CylinderTransitionError(
            "CT004", "Select exactly one or two separate edge chains. Found: {count}", count=len(components)
        )
    ordered = [order_vertices_from_seam(component, scale) for component in components]
    chains = [[to_working_position(vertex, scale) for vertex in chain] for chain in ordered]
    for chain in chains:
        validate_source_chain(chain)

    if len(chains) == 2:
        if len(chains[0]) != len(chains[1]):
            raise CylinderTransitionError(
                "CT006",
                "The two edge chains do not have the same vertex count. Counts: {a} / {b}",
                a=len(chains[0]),
                b=len(chains[1]),
            )
        chains.sort(key=lambda chain: chain[0].z, reverse=True)
        if abs(chains[0][0].z - chains[1][0].z) <= SEAM_TOLERANCE:
            raise CylinderTransitionError(
                "CT014", "Separate the two edges to connect along local Z so the upper and lower edges can be determined."
            )
    return chains


def calculate_cylinder_transition(
    context,
    mode,
    y_length,
    y_divisions,
    vertex_count,
    connection,
    radius,
    radius_reference,
    thickness,
    surface_mode,
    single_surface,
    raycast_receiver,
    use_custom_angle=False,
    custom_angle=DEFAULT_ARC_ANGLE,
):
    arc_angle = normalized_arc_angle(use_custom_angle, custom_angle)
    custom_angle_applies = mode in {MODE_EDGE_TO_SEMI, MODE_SEMI_TO_CIRCLE}
    effective_arc_angle = arc_angle if custom_angle_applies else DEFAULT_ARC_ANGLE
    source_arc_is_circle = (
        mode == MODE_SEMI_TO_CIRCLE and arc_is_circle(effective_arc_angle)
    )
    target_arc_is_circle = (
        mode in {MODE_EDGE_TO_CIRCLE, MODE_SEMI_TO_CIRCLE}
        or (mode == MODE_EDGE_TO_SEMI and arc_is_circle(effective_arc_angle))
    )
    uses_direct_circle = mode == MODE_EDGE_TO_CIRCLE or (
        mode == MODE_EDGE_TO_SEMI and target_arc_is_circle
    )
    if y_length <= 0.0:
        raise CylinderTransitionError("CT015", "Y Length must be greater than zero.")
    minimum_divisions = 2 if uses_direct_circle else 1
    if y_divisions < minimum_divisions:
        raise CylinderTransitionError(
            "CT016",
            "This generation type needs at least {count} Y divisions.",
            count=minimum_divisions,
        )

    obj = None
    if mode != MODE_SEMI_TO_CIRCLE:
        obj = context.edit_object
        if obj is None or obj.type != "MESH":
            raise CylinderTransitionError(
                "CT002", "Mesh must be in Edit Mode for this generation type."
            )
        scale, output_matrix = decompose_working_transform(obj)
    else:
        active_obj = context.active_object
        if (
            active_obj is not None
            and active_obj.get("agrace_generator") == "cylinder_edge_curve"
        ):
            active_obj = None
        obj = active_obj if active_obj is not None and active_obj.select_get() else None
        scale = Vector((1.0, 1.0, 1.0))
        output_matrix = Matrix.Identity(4)
    destination_collection = resolve_destination_collection(context, obj)
    inner_radius, middle_radius, outer_radius = derive_radii(
        radius, radius_reference, thickness
    )

    chains = []
    if mode != MODE_SEMI_TO_CIRCLE:
        chains = selection_data(context, obj, scale)
        input_count = len(chains[0])
    else:
        input_count = vertex_count
        if input_count < 2:
            raise CylinderTransitionError("CT023", "Half-width Vertex Count must be at least 2.")
    raycast_receiver = bool(raycast_receiver) and not (
        source_arc_is_circle and target_arc_is_circle
    )
    count = (
        input_count
        if mode == MODE_SEMI_TO_CIRCLE
        else input_count - 1 if raycast_receiver else input_count
    )
    if raycast_receiver and count < 2:
        raise CylinderTransitionError(
            "CT039", "Raycast receiver input needs at least three vertices."
        )
    if target_arc_is_circle and count < 3:
        raise CylinderTransitionError(
            "CT034", "Circle generation needs at least 3 half-width vertices."
        )

    effective_surface_mode = surface_mode
    effective_connection = connection
    single_is_upper = None
    if len(chains) == 1:
        effective_surface_mode = single_surface
        seam_z = chains[0][0].z
        if abs(seam_z) <= SEAM_TOLERANCE:
            raise CylinderTransitionError(
                "CT042",
                "Place the edge to connect above or below local Z = 0 so its surface side can be determined.",
            )
        single_is_upper = seam_z > 0.0
        connects_as_upper_inner = (
            single_is_upper and single_surface == SURFACE_INNER
        ) or (not single_is_upper and single_surface == SURFACE_OUTER)
        effective_connection = (
            CONNECT_UPPER_INNER
            if connects_as_upper_inner
            else CONNECT_UPPER_OUTER
        )
    if len(chains) == 1 and surface_mode == SURFACE_BOTH:
        # The separate single-surface setting is authoritative for one chain.
        effective_surface_mode = single_surface

    if chains:
        start_y = sum(point.y for chain in chains for point in chain) / sum(
            len(chain) for chain in chains
        )
    else:
        start_y = 0.0
    base_z = 0.0

    center_z = (
        base_z + middle_radius
        if effective_connection == CONNECT_UPPER_INNER
        else base_z - middle_radius
    )
    end_y = start_y + y_length

    custom_arc_angles = arc_angles(count, effective_connection, effective_arc_angle)
    virtual_semi_angles = arc_angles(count, effective_connection, DEFAULT_ARC_ANGLE)
    circle_angles = arc_angles(count, effective_connection, math.pi)

    inner_source = None
    outer_source = None
    inner_special = None
    outer_special = None
    source_hints = {}
    if len(chains) == 2:
        upper, lower = chains
        if effective_connection == CONNECT_UPPER_INNER:
            inner_source, outer_source = upper, lower
        else:
            outer_source, inner_source = upper, lower
        if raycast_receiver:
            inner_special = inner_source[-1].copy()
            outer_special = outer_source[-1].copy()
            inner_source = inner_source[:-1]
            outer_source = outer_source[:-1]
    elif len(chains) == 1:
        if effective_surface_mode == SURFACE_INNER:
            inner_source = chains[0]
            if raycast_receiver:
                inner_special = inner_source[-1].copy()
                inner_source = inner_source[:-1]
            source_hints[SURFACE_INNER] = [
                Vector((0.0, 0.0, 1.0 if single_is_upper else -1.0))
                for _point in inner_source
            ]
        else:
            outer_source = chains[0]
            if raycast_receiver:
                outer_special = outer_source[-1].copy()
                outer_source = outer_source[:-1]
            source_hints[SURFACE_OUTER] = [
                Vector((0.0, 0.0, 1.0 if single_is_upper else -1.0))
                for _point in outer_source
            ]
    else:
        if effective_surface_mode in {SURFACE_BOTH, SURFACE_INNER}:
            inner_source = arc_ring(custom_arc_angles, inner_radius, center_z, start_y)
            source_hints[SURFACE_INNER] = [
                -vector_xz(angle) for angle in custom_arc_angles
            ]
        if effective_surface_mode in {SURFACE_BOTH, SURFACE_OUTER}:
            outer_source = arc_ring(custom_arc_angles, outer_radius, center_z, start_y)
            source_hints[SURFACE_OUTER] = [
                vector_xz(angle) for angle in custom_arc_angles
            ]
        if raycast_receiver:
            source_receiver_delta = arc_receiver_delta(
                effective_arc_angle, effective_connection
            )
            if inner_source is not None:
                inner_special = (
                    inner_source[-1].copy()
                    if source_arc_is_circle
                    else inner_source[-1] + source_receiver_delta
                )
            if outer_source is not None:
                outer_special = (
                    outer_source[-1].copy()
                    if source_arc_is_circle
                    else outer_source[-1] + source_receiver_delta
                )

    target_angles = custom_arc_angles if mode == MODE_EDGE_TO_SEMI else circle_angles
    surface_rings = {}
    surface_hints = {}

    if effective_surface_mode == SURFACE_BOTH:
        if inner_source is None or outer_source is None:
            raise CylinderTransitionError(
                "CT017", "Two edge chains are required to generate both surfaces."
            )
        if uses_direct_circle:
            direct = build_direct_paired_transition(
                inner_source,
                outer_source,
                center_z,
                inner_radius,
                middle_radius,
                outer_radius,
                virtual_semi_angles,
                circle_angles,
                end_y,
                y_divisions,
            )
            surface_rings[SURFACE_INNER] = direct[0]
            surface_rings[SURFACE_OUTER] = direct[1]
            surface_hints[SURFACE_INNER] = direct[2]
            surface_hints[SURFACE_OUTER] = direct[3]
        else:
            paired = build_paired_stage(
                inner_source,
                outer_source,
                center_z,
                inner_radius,
                middle_radius,
                outer_radius,
                target_angles,
                end_y,
                y_divisions,
            )
            surface_rings[SURFACE_INNER] = paired[0]
            surface_rings[SURFACE_OUTER] = paired[1]
            surface_hints[SURFACE_INNER] = paired[2]
            surface_hints[SURFACE_OUTER] = paired[3]
    else:
        surface = effective_surface_mode
        source = inner_source if surface == SURFACE_INNER else outer_source
        target_radius = inner_radius if surface == SURFACE_INNER else outer_radius
        if source is None:
            raise CylinderTransitionError("CT033", "The requested source surface is unavailable.")

        hints = source_hints.get(surface)
        if hints is None:
            is_upper = (
                (surface == SURFACE_INNER and effective_connection == CONNECT_UPPER_INNER)
                or (surface == SURFACE_OUTER and effective_connection == CONNECT_UPPER_OUTER)
            )
            source_normal = Vector((0.0, 0.0, 1.0 if is_upper else -1.0))
            hints = [source_normal.copy() for _point in source]

        if uses_direct_circle:
            direct = build_direct_single_transition(
                source,
                hints,
                center_z,
                target_radius,
                virtual_semi_angles,
                circle_angles,
                end_y,
                y_divisions,
                surface,
            )
            surface_rings[surface] = direct[0]
            surface_hints[surface] = direct[1]
        else:
            single = build_single_stage(
                source,
                hints,
                center_z,
                target_radius,
                target_angles,
                end_y,
                y_divisions,
                surface,
            )
            surface_rings[surface] = single[0]
            surface_hints[surface] = single[1]

    if raycast_receiver:
        for surface, special in (
            (SURFACE_INNER, inner_special),
            (SURFACE_OUTER, outer_special),
        ):
            if surface not in surface_rings:
                continue
            if special is None:
                raise CylinderTransitionError(
                    "CT040", "The raycast receiver source vertex is unavailable."
                )
            append_raycast_receiver_rings(
                surface_rings[surface],
                surface_hints[surface],
                special,
                mode,
                source_arc_delta=(
                    arc_receiver_delta(effective_arc_angle, effective_connection)
                    if mode == MODE_SEMI_TO_CIRCLE and not source_arc_is_circle
                    else None
                ),
                target_arc_delta=(
                    arc_receiver_delta(effective_arc_angle, effective_connection)
                    if mode == MODE_EDGE_TO_SEMI and not target_arc_is_circle
                    else None
                ),
                source_is_circle=source_arc_is_circle,
                target_is_circle=target_arc_is_circle,
            )

    collapse_receiver = raycast_receiver and target_arc_is_circle
    return {
        "output_matrix": output_matrix,
        "destination_collection": destination_collection,
        "surface_rings": surface_rings,
        "surface_hints": surface_hints,
        "effective_surface_mode": effective_surface_mode,
        "effective_connection": effective_connection,
        "mode": mode,
        "arc_angle": effective_arc_angle,
        "source_arc_is_circle": source_arc_is_circle,
        "target_arc_is_circle": target_arc_is_circle,
        "raycast_receiver": raycast_receiver,
        "collapse_receiver": collapse_receiver,
        "section_vertices": len(next(iter(surface_rings.values()))[0]),
        "rings": y_divisions + 1,
    }


def generate_cylinder_transition(
    context,
    mode,
    y_length,
    y_divisions,
    vertex_count,
    connection,
    radius,
    radius_reference,
    thickness,
    surface_mode,
    single_surface,
    generate_sides,
    generate_caps,
    generate_uv,
    raycast_receiver,
    use_custom_angle=False,
    custom_angle=DEFAULT_ARC_ANGLE,
):
    calculation = calculate_cylinder_transition(
        context,
        mode,
        y_length,
        y_divisions,
        vertex_count,
        connection,
        radius,
        radius_reference,
        thickness,
        surface_mode,
        single_surface,
        raycast_receiver,
        use_custom_angle,
        custom_angle,
    )
    new_obj, generated_vertices, generated_faces = create_mesh_object(
        context,
        calculation["output_matrix"],
        calculation["destination_collection"],
        calculation["surface_rings"],
        calculation["surface_hints"],
        generate_sides and calculation["effective_surface_mode"] == SURFACE_BOTH,
        generate_caps and calculation["effective_surface_mode"] == SURFACE_BOTH,
        generate_uv,
        collapse_last=calculation["collapse_receiver"],
        raycast_receiver=calculation["raycast_receiver"],
    )
    return {
        "object": new_obj,
        "vertices": generated_vertices,
        "faces": generated_faces,
        "section_vertices": calculation["section_vertices"],
        "rings": calculation["rings"],
    }


class MESH_OT_agrace_cylinder_transition(bpy.types.Operator):
    bl_idname = "mesh.agrace_cylinder_transition"
    bl_label = "Generate Cylinder Transition"
    bl_description = "Generate a half-width cylindrical transition with thickness, UVs, and an X Mirror modifier"
    bl_options = {"REGISTER", "UNDO"}

    mode: EnumProperty(
        name="Generation Type",
        items=(
            (MODE_EDGE_TO_SEMI, "Edge to Semicircle", "Transition selected half-width edges to a semicircle"),
            (MODE_EDGE_TO_CIRCLE, "Edge to Circle", "Transition selected half-width edges to a full circle through a semicircle"),
            (MODE_SEMI_TO_CIRCLE, "Semicircle to Circle", "Generate from a semicircle at the origin to a full circle"),
        ),
        default=MODE_EDGE_TO_SEMI,
    )
    y_length: FloatProperty(name="Y Length", description="Length along the local +Y direction", default=80.0, min=0.001, unit="LENGTH")
    y_divisions: IntProperty(name="Y Divisions", description="Number of face rows along local Y", default=40, min=1, max=1000)
    vertex_count: IntProperty(name="Half-width Vertex Count", description="Number of vertices generated on the local +X half", default=31, min=2, max=1000)
    use_custom_angle: BoolProperty(
        name="Custom Angle",
        description="Use a custom angle for explicit semicircle sections",
        default=False,
    )
    custom_angle: FloatProperty(
        name="Angle",
        description="Half-width arc angle used instead of the 90 degree semicircle",
        default=DEFAULT_ARC_ANGLE,
        min=MIN_ARC_ANGLE,
        max=MAX_ARC_ANGLE,
        precision=1,
        step=1,
        unit="ROTATION",
        update=update_operator_custom_angle,
    )
    connection: EnumProperty(
        name="Upper / Lower Edge Connection",
        items=(
            (CONNECT_UPPER_INNER, "Upper: Inner / Lower: Outer", "Place the reference circle above the edge midpoint"),
            (CONNECT_UPPER_OUTER, "Upper: Outer / Lower: Inner", "Place the reference circle below the edge midpoint"),
        ),
        default=CONNECT_UPPER_INNER,
    )
    radius: FloatProperty(name="Radius", description="Radius value interpreted by Radius Reference", default=17.5, min=0.001, unit="LENGTH")
    radius_reference: EnumProperty(
        name="Radius Reference",
        items=(
            (RADIUS_INNER, "Inner", "Treat Radius as the inner radius"),
            (RADIUS_MIDDLE, "Thickness Middle", "Treat Radius as the radius at the middle of the thickness"),
            (RADIUS_OUTER, "Outer", "Treat Radius as the outer radius"),
        ),
        default=RADIUS_MIDDLE,
    )
    thickness: FloatProperty(name="Thickness", description="Generated wall thickness", default=1.0, min=0.001, unit="LENGTH", translation_context=AGRACE_TRANSLATION_CONTEXT)
    surface_mode: EnumProperty(
        name="Surfaces",
        items=(
            (SURFACE_BOTH, "Both", "Generate inner and outer surfaces"),
            (SURFACE_INNER, "Inner Only", "Generate only the inner surface"),
            (SURFACE_OUTER, "Outer Only", "Generate only the outer surface"),
        ),
        default=SURFACE_BOTH,
    )
    single_surface: EnumProperty(
        name="Selected Edge Connects To",
        items=(
            (SURFACE_INNER, "Inner Circle", "Connect the selected edge to the inner circle"),
            (SURFACE_OUTER, "Outer Circle", "Connect the selected edge to the outer circle"),
        ),
        default=SURFACE_INNER,
    )
    generate_sides: BoolProperty(name="Generate Sides", description="Connect inner and outer surfaces at boundaries not closed by the X Mirror", default=True)
    generate_caps: BoolProperty(name="Generate End Sections", description="Close the start and end sections between inner and outer surfaces", default=True)
    generate_uv: BoolProperty(name="Generate UV", description="Generate a uniform grid UV map", default=True)
    raycast_receiver: BoolProperty(
        name="Treat Outermost Face as Raycast Receiver",
        description="Generate a special outer boundary from the outermost regular edge direction",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        settings = context.window_manager.agrace_tools
        for name in (
            "mode",
            "y_length",
            "y_divisions",
            "vertex_count",
            "use_custom_angle",
            "custom_angle",
            "connection",
            "radius",
            "radius_reference",
            "thickness",
            "surface_mode",
            "single_surface",
            "generate_sides",
            "generate_caps",
            "generate_uv",
            "raycast_receiver",
        ):
            setattr(settings, f"cylinder_{name}", getattr(self, name))

        try:
            result = generate_cylinder_transition(
                context,
                self.mode,
                self.y_length,
                self.y_divisions,
                self.vertex_count,
                self.connection,
                self.radius,
                self.radius_reference,
                self.thickness,
                self.surface_mode,
                self.single_surface,
                self.generate_sides,
                self.generate_caps,
                self.generate_uv,
                self.raycast_receiver,
                self.use_custom_angle,
                self.custom_angle,
            )
        except CylinderTransitionError as error:
            localized = f"[{error.code}] {error.localized()}"
            settings.cylinder_status = localized
            print(f"[AGRace Tools][{error.code}] {error.english()}")
            self.report({"ERROR"}, localized)
            return {"CANCELLED"}
        except Exception as error:
            settings.cylinder_status = tr("Unexpected error. See the console for details.")
            print(f"[AGRace Tools][CT999] {type(error).__name__}: {error}")
            self.report({"ERROR"}, settings.cylinder_status)
            return {"CANCELLED"}

        message = tr(
            "Cylinder transition created: {vertices} vertices, {faces} faces, {rings} rings."
        ).format(
            vertices=result["vertices"],
            faces=result["faces"],
            rings=result["rings"],
        )
        settings.cylinder_status = message
        print(
            f"[AGRace Tools] Created {result['object'].name}: "
            f"{result['vertices']} vertices, {result['faces']} faces, {result['rings']} rings"
        )
        self.report({"INFO"}, message)
        return {"FINISHED"}
