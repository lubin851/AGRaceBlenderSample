# SPDX-FileCopyrightText: 2026 尾黒こう (Ryuban)
# SPDX-License-Identifier: GPL-3.0-or-later

import math

import bpy
from bpy.props import EnumProperty
from mathutils import Matrix, Vector

from .cylinder_transition import (
    CylinderTransitionError,
    MODE_EDGE_TO_CIRCLE,
    MODE_EDGE_TO_SEMI,
    MODE_SEMI_TO_CIRCLE,
    SEAM_TOLERANCE,
    SURFACE_BOTH,
    SURFACE_INNER,
    SURFACE_OUTER,
    calculate_cylinder_transition,
)
from .smooth_transition import (
    SURFACE_LOWER,
    SURFACE_UPPER,
    SmoothTransitionError,
    calculate_smooth_transition,
)
from .translations import tr


ROW_OUTERMOST = "OUTERMOST"
ROW_SECOND = "SECOND"
BOUNDARY_SEMI = "SEMI"
BOUNDARY_CIRCLE = "CIRCLE"


class EdgeCurveError(RuntimeError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message

    def localized(self):
        return tr(self.message)


def surface_path(calculation, surface, row):
    rings = calculation["surface_rings"][surface]
    hints = calculation["surface_hints"][surface]
    column = -1 if row == ROW_OUTERMOST else -2
    if len(rings[0]) < abs(column):
        raise EdgeCurveError("EC005", "The requested reference row is unavailable. Choose another available row.")

    points = [ring[column].copy() for ring in rings]
    normals = surface_normals(
        rings,
        hints,
        column,
        calculation["raycast_receiver"],
    )
    return points, normals


def smooth_surface_path(calculation, row, surface_key=None):
    if surface_key is None:
        if len(calculation["surfaces"]) != 1:
            raise EdgeCurveError("EC010", "Choose an upper or lower Y-axis surface.")
        surface_key = next(iter(calculation["surfaces"]))
    surface = calculation["surfaces"].get(surface_key)
    if surface is None:
        raise EdgeCurveError("EC010", "The requested Y-axis surface is unavailable.")
    rings = surface["rings"]
    column = -1 if row == ROW_OUTERMOST else -2
    if len(rings[0]) < abs(column):
        raise EdgeCurveError("EC005", "The requested reference row is unavailable. Choose another available row.")
    hints = [
        [Vector((0.0, 0.0, surface["normal_sign"])) for _point in ring]
        for ring in rings
    ]
    points = [ring[column].copy() for ring in rings]
    normals = surface_normals(
        rings,
        hints,
        column,
        calculation["raycast_receiver"],
    )
    return points, normals


def neighboring_tangent(values, index):
    if index == 0:
        tangent = values[1] - values[0]
    elif index == len(values) - 1:
        tangent = values[-1] - values[-2]
    else:
        tangent = values[index + 1] - values[index - 1]
    if tangent.length <= SEAM_TOLERANCE:
        raise EdgeCurveError("EC008", "The cylinder surface contains an invalid tangent.")
    return tangent.normalized()


def surface_normals(rings, hints, column, raycast_receiver):
    column_index = column if column >= 0 else len(rings[0]) + column
    if column_index <= 0 or column_index >= len(rings[0]):
        raise EdgeCurveError("EC005", "The requested reference row is unavailable. Choose another available row.")

    face_path_values = []
    section_tangents = []
    for ring in rings:
        inside_index = column_index - 1
        while inside_index >= 0:
            candidate = ring[column_index] - ring[inside_index]
            if candidate.length > SEAM_TOLERANCE:
                break
            inside_index -= 1
        if inside_index < 0:
            raise EdgeCurveError("EC008", "The cylinder surface contains an invalid tangent.")
        section_tangents.append(ring[column_index] - ring[inside_index])
        face_path_values.append((ring[column_index] + ring[inside_index]) * 0.5)

    normals = []
    previous = None
    for ring_index, ring in enumerate(rings):
        path_tangent = neighboring_tangent(face_path_values, ring_index)
        section_tangent = section_tangents[ring_index]
        section_tangent.normalize()

        normal = section_tangent.cross(path_tangent)
        if normal.length <= SEAM_TOLERANCE:
            raise EdgeCurveError("EC008", "The cylinder surface contains an invalid tangent.")
        normal.normalize()
        if previous is None:
            if normal.dot(hints[ring_index][column_index]) < 0.0:
                normal.negate()
        elif normal.dot(previous) < 0.0:
            normal.negate()
        normals.append(normal)
        previous = normal
    return normals


def projected_normal(vector, tangent):
    projected = vector - tangent * vector.dot(tangent)
    if projected.length <= SEAM_TOLERANCE:
        return None
    return projected.normalized()


def boundary_kind(
    mode,
    index,
    last_index,
    arc_angle=math.pi * 0.5,
    source_arc_is_circle=False,
    target_arc_is_circle=False,
):
    if index == 0 and mode == MODE_SEMI_TO_CIRCLE:
        if source_arc_is_circle:
            return BOUNDARY_CIRCLE
        if abs(arc_angle - math.pi * 0.5) <= SEAM_TOLERANCE:
            return BOUNDARY_SEMI
        return None
    if index != last_index:
        return None
    if mode == MODE_EDGE_TO_SEMI:
        if target_arc_is_circle:
            return BOUNDARY_CIRCLE
        if abs(arc_angle - math.pi * 0.5) <= SEAM_TOLERANCE:
            return BOUNDARY_SEMI
        return None
    if mode in {MODE_EDGE_TO_CIRCLE, MODE_SEMI_TO_CIRCLE}:
        return BOUNDARY_CIRCLE
    return None


def boundary_tilt(estimated_tilt):
    quarter_turn = math.pi * 0.5
    snapped = round(estimated_tilt / quarter_turn) * quarter_turn
    return snapped + quarter_turn


def create_curve_object(
    output_matrix,
    destination_collection,
    surface,
    row,
    points,
    normals,
    mode=None,
    arc_angle=math.pi * 0.5,
    source_arc_is_circle=False,
    target_arc_is_circle=False,
    object_name=None,
    generator="cylinder_edge_curve",
    metadata=None,
):
    suffix = "Inner" if surface == SURFACE_INNER else "Outer"
    object_name = object_name or f"CylinderEdgeCurve{suffix}"
    curve_data = bpy.data.curves.new(object_name, type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 12
    curve_data.twist_smooth = 8
    curve_data.twist_mode = "Z_UP"
    spline = curve_data.splines.new(type="BEZIER")
    spline.bezier_points.add(len(points) - 1)

    local_points = [output_matrix @ point for point in points]
    normal_matrix = output_matrix.to_3x3()
    local_normals = []
    for normal in normals:
        transformed = normal_matrix @ normal
        if transformed.length <= SEAM_TOLERANCE:
            raise EdgeCurveError("EC009", "The edge curve contains an invalid normal.")
        local_normals.append(transformed.normalized())

    tangents = []
    for index, point in enumerate(local_points):
        if index == 0:
            tangent = local_points[1] - point
        elif index == len(local_points) - 1:
            tangent = point - local_points[index - 1]
        else:
            tangent = local_points[index + 1] - local_points[index - 1]
        if tangent.length <= SEAM_TOLERANCE:
            raise EdgeCurveError("EC007", "The edge curve contains overlapping consecutive points.")
        tangents.append(tangent.normalized())

    previous_tilt = None
    for index, bezier_point in enumerate(spline.bezier_points):
        point = local_points[index]
        tangent = tangents[index]
        previous_length = (
            (point - local_points[index - 1]).length
            if index > 0
            else (local_points[1] - point).length
        )
        next_length = (
            (local_points[index + 1] - point).length
            if index < len(local_points) - 1
            else (point - local_points[index - 1]).length
        )
        bezier_point.co = point
        bezier_point.handle_left_type = "FREE"
        bezier_point.handle_right_type = "FREE"
        bezier_point.handle_left = point - tangent * (previous_length / 3.0)
        bezier_point.handle_right = point + tangent * (next_length / 3.0)

        reference = projected_normal(Vector((0.0, 0.0, 1.0)), tangent)
        if reference is None:
            reference = projected_normal(Vector((1.0, 0.0, 0.0)), tangent)
        target = projected_normal(local_normals[index], tangent)
        tilt = 0.0
        if reference is not None and target is not None:
            tilt = math.atan2(
                tangent.dot(reference.cross(target)), reference.dot(target)
            )
        kind = boundary_kind(
            mode,
            index,
            len(local_points) - 1,
            arc_angle,
            source_arc_is_circle,
            target_arc_is_circle,
        )
        if kind is None:
            tilt += math.pi * 0.5
        else:
            tilt = boundary_tilt(tilt)
        if previous_tilt is not None:
            delta = (tilt - previous_tilt + math.pi) % (math.pi * 2.0) - math.pi
            tilt = previous_tilt + delta
        bezier_point.tilt = tilt
        previous_tilt = tilt

    curve_obj = bpy.data.objects.new(object_name, curve_data)
    destination_collection.objects.link(curve_obj)
    curve_obj.matrix_world = Matrix.Identity(4)
    curve_obj["agrace_generator"] = generator
    if surface is not None:
        curve_obj["agrace_surface"] = surface
    curve_obj["agrace_reference_row"] = row
    if metadata:
        for key, value in metadata.items():
            curve_obj[key] = value

    return curve_obj


def requested_surfaces(target):
    if target == SURFACE_BOTH:
        return (SURFACE_INNER, SURFACE_OUTER)
    return (target,)


class CURVE_OT_agrace_edge_curve(bpy.types.Operator):
    bl_idname = "curve.agrace_edge_curve"
    bl_label = "Generate Curve Along Edge"
    bl_description = "Generate a Bezier curve using the current Cylinder Smooth Transition settings"
    bl_options = {"REGISTER", "UNDO"}

    target: EnumProperty(
        name="Curve Surfaces",
        items=(
            (SURFACE_BOTH, "Both Sides", "Generate curves for every available inner and outer surface"),
            (SURFACE_INNER, "Inner", "Generate the inner-surface curve if available"),
            (SURFACE_OUTER, "Outer", "Generate the outer-surface curve if available"),
        ),
        default=SURFACE_BOTH,
    )
    row: EnumProperty(
        name="Reference Row",
        items=(
            (ROW_OUTERMOST, "Outermost", "Use the outermost longitudinal edge row"),
            (ROW_SECOND, "Second from Outermost", "Use the second longitudinal edge row from the outside"),
        ),
        default=ROW_OUTERMOST,
    )

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        settings = context.window_manager.agrace_tools
        settings.edge_curve_target = self.target
        settings.edge_curve_row = self.row
        reference_obj = context.active_object
        if (
            reference_obj is not None
            and reference_obj.get("agrace_generator") == "cylinder_edge_curve"
        ):
            reference_obj = None
        created = []
        try:
            calculation = calculate_cylinder_transition(
                context,
                settings.cylinder_mode,
                settings.cylinder_y_length,
                settings.cylinder_y_divisions,
                settings.cylinder_vertex_count,
                settings.cylinder_connection,
                settings.cylinder_radius,
                settings.cylinder_radius_reference,
                settings.cylinder_thickness,
                settings.cylinder_surface_mode,
                settings.cylinder_single_surface,
                settings.cylinder_raycast_receiver,
                settings.cylinder_use_custom_angle,
                settings.cylinder_custom_angle,
            )
            for surface in requested_surfaces(self.target):
                if surface not in calculation["surface_rings"]:
                    continue
                points, normals = surface_path(calculation, surface, self.row)
                created.append(
                    create_curve_object(
                        calculation["output_matrix"],
                        calculation["destination_collection"],
                        surface,
                        self.row,
                        points,
                        normals,
                        calculation["mode"],
                        calculation["arc_angle"],
                        calculation["source_arc_is_circle"],
                        calculation["target_arc_is_circle"],
                    )
                )
        except (EdgeCurveError, CylinderTransitionError) as error:
            for curve_obj in created:
                curve_data = curve_obj.data
                bpy.data.objects.remove(curve_obj, do_unlink=True)
                if curve_data.users == 0:
                    bpy.data.curves.remove(curve_data)
            message = f"[{error.code}] {error.localized()}"
            settings.edge_curve_status = message
            self.report({"ERROR"}, message)
            return {"CANCELLED"}

        if not created:
            message = tr("No requested cylinder surfaces are available.")
            settings.edge_curve_status = message
            self.report({"INFO"}, message)
            return {"CANCELLED"}

        if context.mode == "OBJECT":
            for curve_obj in created:
                curve_obj.select_set(True)
            if reference_obj is not None:
                reference_obj.select_set(True)
            context.view_layer.objects.active = reference_obj
        message = tr("Edge curve generation complete: {count} curve object(s).").format(
            count=len(created)
        )
        settings.edge_curve_status = message
        self.report({"INFO"}, message)
        return {"FINISHED"}


class CURVE_OT_agrace_smooth_edge_curve(bpy.types.Operator):
    bl_idname = "curve.agrace_smooth_edge_curve"
    bl_label = "Generate Y-Axis Curve Along Edge"
    bl_description = "Generate a Bezier curve using the current Y-Axis Smooth Transition settings"
    bl_options = {"REGISTER", "UNDO"}

    row: EnumProperty(
        name="Reference Row",
        items=(
            (ROW_OUTERMOST, "Outermost", "Use the outermost longitudinal edge row"),
            (ROW_SECOND, "Second from Outermost", "Use the second longitudinal edge row from the outside"),
        ),
        default=ROW_OUTERMOST,
    )

    @classmethod
    def poll(cls, context):
        valid = context.edit_object is not None and context.edit_object.type == "MESH"
        if not valid:
            cls.poll_message_set(tr("Select a Mesh object and enter Edit Mode."))
        return valid

    def execute(self, context):
        settings = context.window_manager.agrace_tools
        settings.smooth_curve_row = self.row
        reference_obj = context.active_object
        if (
            reference_obj is not None
            and reference_obj.get("agrace_generator") == "smooth_edge_curve"
        ):
            reference_obj = None
        created = []
        try:
            calculation = calculate_smooth_transition(
                context,
                settings.ring_count,
                settings.outward_bulge,
                settings.use_squared_x_weight,
                settings.smooth_raycast_receiver,
            )
            multiple = len(calculation["surfaces"]) > 1
            for surface_key in (SURFACE_UPPER, SURFACE_LOWER):
                if surface_key not in calculation["surfaces"]:
                    continue
                surface = calculation["surfaces"][surface_key]
                points, normals = smooth_surface_path(
                    calculation, self.row, surface_key
                )
                suffix = "Upper" if surface_key == SURFACE_UPPER else "Lower"
                created.append(
                    create_curve_object(
                        calculation["output_matrix"],
                        calculation["destination_collection"],
                        None,
                        self.row,
                        points,
                        normals,
                        object_name=(
                            f"YSmoothEdgeCurve{suffix}"
                            if multiple
                            else "YSmoothEdgeCurve"
                        ),
                        generator="smooth_edge_curve",
                        metadata={
                            "agrace_normal_sign": surface["normal_sign"],
                            "agrace_y_surface": surface_key,
                        },
                    )
                )
        except (EdgeCurveError, SmoothTransitionError) as error:
            for curve_obj in created:
                curve_data = curve_obj.data
                bpy.data.objects.remove(curve_obj, do_unlink=True)
                if curve_data.users == 0:
                    bpy.data.curves.remove(curve_data)
            message = f"[{error.code}] {error.localized()}"
            settings.smooth_curve_status = message
            self.report({"ERROR"}, message)
            return {"CANCELLED"}

        if context.mode == "OBJECT":
            for curve_obj in created:
                curve_obj.select_set(True)
            if reference_obj is not None:
                reference_obj.select_set(True)
            context.view_layer.objects.active = reference_obj
        message = tr("Y-axis edge curve generation complete.")
        settings.smooth_curve_status = message
        self.report({"INFO"}, message)
        return {"FINISHED"}
