# SPDX-FileCopyrightText: 2026 尾黒こう (Ryuban)
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import bmesh
from bpy.props import BoolProperty, FloatProperty, IntProperty
from mathutils import Vector

from .cylinder_transition import resolve_destination_collection
from .translations import tr


SEAM_TOLERANCE = 1.0e-5
UV_NORMAL_MIN = 0.4
UV_NORMAL_MAX = 1.0
UV_RECEIVER_MIN = 0.2
UV_RECEIVER_MAX = 0.4
SURFACE_UPPER = "UPPER"
SURFACE_LOWER = "LOWER"


class SmoothTransitionError(RuntimeError):
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


def bulge_envelope(t):
    return 64.0 * t**3 * (1.0 - t) ** 3


def lerp(a, b, t):
    return a + (b - a) * t


def clamp_between(value, a, b):
    return max(min(a, b), min(max(a, b), value))


def selected_edge_components(bm):
    selected_edges = [edge for edge in bm.edges if edge.select and not edge.hide]
    if not selected_edges:
        raise SmoothTransitionError("ST003", "Select two or four separate open edge chains.")

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


def order_vertices_from_edges(edges):
    adjacency = {}
    for edge in edges:
        v0, v1 = edge.verts
        adjacency.setdefault(v0, []).append(v1)
        adjacency.setdefault(v1, []).append(v0)

    endpoints = [vertex for vertex, neighbours in adjacency.items() if len(neighbours) == 1]
    if len(endpoints) == 0:
        raise SmoothTransitionError(
            "ST005", "Closed loops are not supported. Select open edge chains."
        )
    if len(endpoints) != 2:
        raise SmoothTransitionError(
            "ST007", "A selected edge chain is branched. Select one continuous chain."
        )

    # A deterministic start avoids face winding changing with Python set order.
    start = min(endpoints, key=lambda vertex: (vertex.co.x, vertex.co.z, vertex.co.y, vertex.index))
    ordered = []
    previous = None
    current = start
    while True:
        ordered.append(current)
        candidates = [vertex for vertex in adjacency[current] if vertex != previous]
        if not candidates:
            break
        if len(candidates) > 1:
            raise SmoothTransitionError(
                "ST007", "A selected edge chain is branched. Select one continuous chain."
            )
        previous, current = current, candidates[0]
    return ordered


def align_vertex_order(loop_a, loop_b):
    if len(loop_a) != len(loop_b):
        raise SmoothTransitionError(
            "ST006",
            "The two edge chains do not have the same vertex count. Counts: {a} / {b}",
            a=len(loop_a),
            b=len(loop_b),
        )
    reversed_b = list(reversed(loop_b))
    normal_distance = sum((a.co - b.co).length_squared for a, b in zip(loop_a, loop_b))
    reversed_distance = sum((a.co - b.co).length_squared for a, b in zip(loop_a, reversed_b))
    return reversed_b if reversed_distance < normal_distance else loop_b


def seam_z_sign(loop):
    seam_vertices = [vertex for vertex in loop if abs(vertex.co.x) <= SEAM_TOLERANCE]
    if not seam_vertices:
        raise SmoothTransitionError(
            "ST010", "Place the center-side endpoint of each selected edge chain at local X = 0."
        )
    seam_z = sum(vertex.co.z for vertex in seam_vertices) / len(seam_vertices)
    if abs(seam_z) <= SEAM_TOLERANCE:
        raise SmoothTransitionError(
            "ST011", "Place the edge to connect above or below local Z = 0 so its surface side can be determined."
        )
    return 1.0 if seam_z > 0.0 else -1.0


def calculate_surface_pair(
    loop_a,
    loop_b,
    normal_sign,
    ring_count,
    outward_bulge,
    squared_x_weight,
):
    if len(loop_a) != len(loop_b):
        raise SmoothTransitionError(
            "ST006",
            "The two edge chains do not have the same vertex count. Counts: {a} / {b}",
            a=len(loop_a),
            b=len(loop_b),
        )

    average_y_a = sum(vertex.co.y for vertex in loop_a) / len(loop_a)
    average_y_b = sum(vertex.co.y for vertex in loop_b) / len(loop_b)
    if abs(average_y_a - average_y_b) <= 1.0e-6:
        raise SmoothTransitionError(
            "ST009", "Separate the two edge chains along the object's local Y axis."
        )

    flat_loop, half_loop = (loop_a, loop_b) if average_y_a < average_y_b else (loop_b, loop_a)
    half_loop = align_vertex_order(flat_loop, half_loop)

    max_abs_x = max(abs(vertex.co.x) for vertex in flat_loop + half_loop)
    rings = []
    for ring_index in range(ring_count + 1):
        t = ring_index / ring_count
        shape_weight = smootherstep(t)
        outward_weight = bulge_envelope(t)
        ring = []

        for flat_vertex, half_vertex in zip(flat_loop, half_loop):
            p0 = flat_vertex.co.copy()
            p1 = half_vertex.co.copy()
            if ring_index == 0:
                position = p0
            elif ring_index == ring_count:
                position = p1
            else:
                x = lerp(p0.x, p1.x, shape_weight)
                y = lerp(p0.y, p1.y, t)
                z = clamp_between(lerp(p0.z, p1.z, shape_weight), p0.z, p1.z)

                if outward_bulge != 0.0 and max_abs_x > 1.0e-6:
                    x_weight = max(0.0, min(1.0, abs(x) / max_abs_x))
                    if squared_x_weight:
                        x_weight *= x_weight
                    outward_sign = 1.0 if x > 1.0e-6 else -1.0 if x < -1.0e-6 else 0.0
                    x += outward_sign * outward_bulge * outward_weight * x_weight
                position = Vector((x, y, z))

            ring.append(Vector(position))

        rings.append(ring)

    return {
        "rings": rings,
        "normal_sign": normal_sign,
        "section_vertices": len(rings[0]),
        "regular_section_vertices": len(flat_loop),
    }


def calculate_smooth_transition(
    context,
    ring_count,
    outward_bulge,
    squared_x_weight,
    raycast_receiver=False,
):
    if ring_count < 1:
        raise SmoothTransitionError("ST008", "Ring Count must be at least 1.")

    obj = context.edit_object
    if obj is None or obj.type != "MESH":
        raise SmoothTransitionError("ST002", "Mesh must be in Edit Mode.")

    bm = bmesh.from_edit_mesh(obj.data)
    components = selected_edge_components(bm)
    if len(components) not in {2, 4}:
        raise SmoothTransitionError(
            "ST004",
            "Select exactly two or four separate edge chains. Found: {count}",
            count=len(components),
        )

    loops = [order_vertices_from_edges(component) for component in components]
    counts = {len(loop) for loop in loops}
    if len(counts) != 1:
        raise SmoothTransitionError(
            "ST014", "All selected edge chains must have the same vertex count."
        )
    if raycast_receiver and next(iter(counts)) < 2:
        raise SmoothTransitionError(
            "ST013", "Raycast receiver input needs at least two vertices."
        )

    grouped = {SURFACE_UPPER: [], SURFACE_LOWER: []}
    for loop in loops:
        key = SURFACE_UPPER if seam_z_sign(loop) > 0.0 else SURFACE_LOWER
        grouped[key].append(loop)

    if len(components) == 2:
        available = [key for key, values in grouped.items() if len(values) == 2]
        if len(available) != 1:
            raise SmoothTransitionError(
                "ST012", "Place both edges to connect on the local +Z side or both on the local -Z side."
            )
    elif any(len(grouped[key]) != 2 for key in (SURFACE_UPPER, SURFACE_LOWER)):
        raise SmoothTransitionError(
            "ST015",
            "When selecting four edge chains, place two on the local +Z side and two on the local -Z side.",
        )

    surfaces = {}
    for key, normal_sign in ((SURFACE_UPPER, 1.0), (SURFACE_LOWER, -1.0)):
        if len(grouped[key]) != 2:
            continue
        surfaces[key] = calculate_surface_pair(
            grouped[key][0],
            grouped[key][1],
            normal_sign,
            ring_count,
            outward_bulge,
            squared_x_weight,
        )

    calculation = {
        "output_matrix": obj.matrix_world.copy(),
        "destination_collection": resolve_destination_collection(context, obj),
        "surfaces": surfaces,
        "raycast_receiver": bool(raycast_receiver),
        "surface_count": len(surfaces),
        "section_vertices": next(iter(surfaces.values()))["section_vertices"],
    }
    if len(surfaces) == 1:
        only_surface = next(iter(surfaces.values()))
        calculation.update(only_surface)
    return calculation


def create_smooth_transition_object(calculation, generate_uv):
    mesh = bpy.data.meshes.new("SmoothTransitionMesh")
    new_obj = bpy.data.objects.new("SmoothTransition", mesh)
    calculation["destination_collection"].objects.link(new_obj)
    new_obj.matrix_world = calculation["output_matrix"]

    vertices = []
    faces = []
    face_uvs = []
    for surface in calculation["surfaces"].values():
        rings = surface["rings"]
        section_vertices = len(rings[0])
        surface_offset = len(vertices)
        vertices.extend(point.copy() for ring in rings for point in ring)
        normal_last_vertex = (
            section_vertices - 2
            if calculation["raycast_receiver"]
            else section_vertices - 1
        )
        normal_divisions = max(1, normal_last_vertex)
        for ring_index in range(len(rings) - 1):
            base_a = surface_offset + ring_index * section_vertices
            base_b = surface_offset + (ring_index + 1) * section_vertices
            u0 = ring_index / (len(rings) - 1)
            u1 = (ring_index + 1) / (len(rings) - 1)
            for vertex_index in range(section_vertices - 1):
                is_receiver = (
                    calculation["raycast_receiver"]
                    and vertex_index == section_vertices - 2
                )
                if is_receiver:
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
                face = (
                    base_a + vertex_index,
                    base_a + vertex_index + 1,
                    base_b + vertex_index + 1,
                    base_b + vertex_index,
                )
                face_uv = ((u0, v0), (u0, v1), (u1, v1), (u1, v0))
                if surface["normal_sign"] < 0.0:
                    face = tuple(reversed(face))
                    face_uv = tuple(reversed(face_uv))
                faces.append(face)
                face_uvs.append(face_uv)

    try:
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        if generate_uv:
            uv_layer = mesh.uv_layers.new(name="AGRaceUV")
            for polygon, polygon_uvs in zip(mesh.polygons, face_uvs):
                for loop_index, uv in zip(polygon.loop_indices, polygon_uvs):
                    uv_layer.data[loop_index].uv = uv
        new_obj["agrace_generator"] = "smooth_transition"
        new_obj["agrace_ring_count"] = len(next(iter(calculation["surfaces"].values()))["rings"])
        new_obj["agrace_section_vertices"] = calculation["section_vertices"]
        new_obj["agrace_raycast_receiver"] = calculation["raycast_receiver"]
        new_obj["agrace_has_upper"] = SURFACE_UPPER in calculation["surfaces"]
        new_obj["agrace_has_lower"] = SURFACE_LOWER in calculation["surfaces"]
        new_obj["agrace_surface_count"] = calculation["surface_count"]
        if calculation["surface_count"] == 1:
            new_obj["agrace_normal_sign"] = calculation["normal_sign"]
    except Exception:
        bpy.data.objects.remove(new_obj, do_unlink=True)
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
        raise
    return new_obj


def generate_smooth_transition(
    context,
    ring_count,
    outward_bulge,
    squared_x_weight,
    raycast_receiver=False,
    generate_uv=True,
):
    calculation = calculate_smooth_transition(
        context,
        ring_count,
        outward_bulge,
        squared_x_weight,
        raycast_receiver,
    )
    new_obj = create_smooth_transition_object(calculation, generate_uv)

    return {
        "object": new_obj,
        "section_vertices": calculation["section_vertices"],
        "rings": len(next(iter(calculation["surfaces"].values()))["rings"]),
        "surfaces": calculation["surface_count"],
    }


class MESH_OT_agrace_smooth_transition(bpy.types.Operator):
    bl_idname = "mesh.agrace_smooth_transition"
    bl_label = "Generate Smooth Transition"
    bl_description = "Generate an AGRace-specific transition between two open edge chains separated along local Y"
    bl_options = {"REGISTER", "UNDO"}

    ring_count: IntProperty(name="Ring Count", description="Number of divisions along the local Y direction", default=40, min=1, max=1000)
    outward_bulge: FloatProperty(name="Outward Bulge", description="Adds extra outward curvature around the middle; 0 to 1 is recommended", default=0.0, soft_min=0.0, soft_max=1.0)
    use_squared_x_weight: BoolProperty(name="Reduce Center Influence", description="Reduces bulge influence around local X = 0", default=True)
    raycast_receiver: BoolProperty(
        name="Treat Outermost Face as Raycast Receiver",
        description="Treat the face between the local +X outermost and second outermost rows as a raycast receiver",
        default=False,
    )
    generate_uv: BoolProperty(
        name="Generate UV",
        description="Generate a UV map using the AGRace category bands",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        valid = context.edit_object is not None and context.edit_object.type == "MESH"
        if not valid:
            cls.poll_message_set(tr("Select a Mesh object and enter Edit Mode."))
        return valid

    def execute(self, context):
        settings = context.window_manager.agrace_tools
        settings.ring_count = self.ring_count
        settings.outward_bulge = self.outward_bulge
        settings.use_squared_x_weight = self.use_squared_x_weight
        settings.smooth_raycast_receiver = self.raycast_receiver
        settings.smooth_generate_uv = self.generate_uv
        try:
            result = generate_smooth_transition(
                context,
                self.ring_count,
                self.outward_bulge,
                self.use_squared_x_weight,
                self.raycast_receiver,
                self.generate_uv,
            )
        except SmoothTransitionError as error:
            localized = f"[{error.code}] {error.localized()}"
            settings.smooth_status = localized
            print(f"[AGRace Tools][{error.code}] {error.english()}")
            self.report({"ERROR"}, localized)
            return {"CANCELLED"}
        except Exception as error:
            settings.smooth_status = tr("Unexpected error. See the console for details.")
            print(f"[AGRace Tools][ST999] {type(error).__name__}: {error}")
            self.report({"ERROR"}, settings.smooth_status)
            return {"CANCELLED"}

        message = tr(
            "Smooth transition created: {vertices} vertices per section, {rings} rings."
        ).format(vertices=result["section_vertices"], rings=result["rings"])
        settings.smooth_status = message
        print(f"[AGRace Tools] Created {result['object'].name}: {result['section_vertices']} vertices per section, {result['rings']} rings")
        self.report({"INFO"}, message)
        return {"FINISHED"}
