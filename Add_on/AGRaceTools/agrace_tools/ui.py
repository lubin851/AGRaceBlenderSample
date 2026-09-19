# SPDX-FileCopyrightText: 2026 尾黒こう (Ryuban)
# SPDX-License-Identifier: GPL-3.0-or-later

import unicodedata

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, StringProperty

from .cylinder_transition import (
    CONNECT_UPPER_INNER,
    CONNECT_UPPER_OUTER,
    DEFAULT_ARC_ANGLE,
    MAX_ARC_ANGLE,
    MIN_ARC_ANGLE,
    MODE_EDGE_TO_CIRCLE,
    MODE_EDGE_TO_SEMI,
    MODE_SEMI_TO_CIRCLE,
    RADIUS_INNER,
    RADIUS_MIDDLE,
    RADIUS_OUTER,
    SURFACE_BOTH,
    SURFACE_INNER,
    SURFACE_OUTER,
    inspect_selection,
    rounded_arc_angle,
)
from .edge_curve import ROW_OUTERMOST, ROW_SECOND
from .translations import AGRACE_TRANSLATION_CONTEXT, tr, tr_agrace


_UPDATING_CYLINDER_CUSTOM_ANGLE = False


def update_cylinder_custom_angle(settings, _context):
    global _UPDATING_CYLINDER_CUSTOM_ANGLE
    if _UPDATING_CYLINDER_CUSTOM_ANGLE:
        return
    rounded = rounded_arc_angle(settings.cylinder_custom_angle)
    if abs(settings.cylinder_custom_angle - rounded) > 1.0e-12:
        _UPDATING_CYLINDER_CUSTOM_ANGLE = True
        try:
            settings.cylinder_custom_angle = rounded
        finally:
            _UPDATING_CYLINDER_CUSTOM_ANGLE = False


class AGRACE_PG_settings(bpy.types.PropertyGroup):
    ring_count: IntProperty(name="Ring Count", description="Number of divisions along the local Y direction", default=40, min=1, max=1000)
    outward_bulge: FloatProperty(name="Outward Bulge", description="Adds extra outward curvature around the middle; 0 to 1 is recommended", default=0.0, soft_min=0.0, soft_max=1.0)
    use_squared_x_weight: BoolProperty(name="Reduce Center Influence", description="Reduces bulge influence around local X = 0", default=True)
    smooth_raycast_receiver: BoolProperty(
        name="Treat Outermost Face as Raycast Receiver",
        description="Treat the face between the local +X outermost and second outermost rows as a raycast receiver",
        default=False,
    )
    smooth_generate_uv: BoolProperty(
        name="Generate UV",
        description="Generate a UV map using the AGRace category bands",
        default=True,
    )
    smooth_curve_row: EnumProperty(
        name="Reference Row",
        items=(
            (ROW_OUTERMOST, "Outermost", "Use the outermost longitudinal edge row"),
            (ROW_SECOND, "Second from Outermost", "Use the second longitudinal edge row from the outside"),
        ),
        default=ROW_OUTERMOST,
    )
    smooth_status: StringProperty(default="")
    smooth_curve_status: StringProperty(default="")
    cylinder_mode: EnumProperty(
        name="Generation Type",
        items=(
            (MODE_EDGE_TO_SEMI, "Edge to Semicircle", "Transition selected half-width edges to a semicircle"),
            (MODE_EDGE_TO_CIRCLE, "Edge to Circle", "Transition selected half-width edges to a full circle through a semicircle"),
            (MODE_SEMI_TO_CIRCLE, "Semicircle to Circle", "Generate from a semicircle at the origin to a full circle"),
        ),
        default=MODE_EDGE_TO_SEMI,
    )
    cylinder_y_length: FloatProperty(name="Y Length", description="Length along the local +Y direction", default=80.0, min=0.001, unit="LENGTH")
    cylinder_y_divisions: IntProperty(name="Y Divisions", description="Number of face rows along local Y", default=40, min=1, max=1000)
    cylinder_vertex_count: IntProperty(name="Half-width Vertex Count", description="Number of vertices generated on the local +X half", default=31, min=2, max=1000)
    cylinder_use_custom_angle: BoolProperty(
        name="Custom Angle",
        description="Use a custom angle for explicit semicircle sections",
        default=False,
    )
    cylinder_custom_angle: FloatProperty(
        name="Angle",
        description="Half-width arc angle used instead of the 90 degree semicircle",
        default=DEFAULT_ARC_ANGLE,
        min=MIN_ARC_ANGLE,
        max=MAX_ARC_ANGLE,
        precision=1,
        step=1,
        unit="ROTATION",
        update=update_cylinder_custom_angle,
    )
    cylinder_connection: EnumProperty(
        name="Upper / Lower Edge Connection",
        items=(
            (CONNECT_UPPER_INNER, "Upper: Inner / Lower: Outer", "Place the reference circle above the edge midpoint"),
            (CONNECT_UPPER_OUTER, "Upper: Outer / Lower: Inner", "Place the reference circle below the edge midpoint"),
        ),
        default=CONNECT_UPPER_INNER,
    )
    cylinder_radius: FloatProperty(name="Radius", description="Radius value interpreted by Radius Reference", default=17.5, min=0.001, unit="LENGTH")
    cylinder_radius_reference: EnumProperty(
        name="Radius Reference",
        items=(
            (RADIUS_INNER, "Inner", "Treat Radius as the inner radius"),
            (RADIUS_MIDDLE, "Thickness Middle", "Treat Radius as the radius at the middle of the thickness"),
            (RADIUS_OUTER, "Outer", "Treat Radius as the outer radius"),
        ),
        default=RADIUS_MIDDLE,
    )
    cylinder_thickness: FloatProperty(name="Thickness", description="Generated wall thickness", default=1.0, min=0.001, unit="LENGTH", translation_context=AGRACE_TRANSLATION_CONTEXT)
    cylinder_surface_mode: EnumProperty(
        name="Surfaces",
        items=(
            (SURFACE_BOTH, "Both", "Generate inner and outer surfaces"),
            (SURFACE_INNER, "Inner Only", "Generate only the inner surface"),
            (SURFACE_OUTER, "Outer Only", "Generate only the outer surface"),
        ),
        default=SURFACE_BOTH,
    )
    cylinder_single_surface: EnumProperty(
        name="Selected Edge Connects To",
        items=(
            (SURFACE_INNER, "Inner Circle", "Connect the selected edge to the inner circle"),
            (SURFACE_OUTER, "Outer Circle", "Connect the selected edge to the outer circle"),
        ),
        default=SURFACE_INNER,
    )
    cylinder_generate_sides: BoolProperty(name="Generate Sides", description="Connect inner and outer surfaces at boundaries not closed by the X Mirror", default=True)
    cylinder_generate_caps: BoolProperty(name="Generate End Sections", description="Close the start and end sections between inner and outer surfaces", default=True)
    cylinder_generate_uv: BoolProperty(name="Generate UV", description="Generate a uniform grid UV map", default=True)
    cylinder_raycast_receiver: BoolProperty(
        name="Treat Outermost Face as Raycast Receiver",
        description="Generate a special outer boundary from the outermost regular edge direction",
        default=False,
    )
    cylinder_status: StringProperty(default="")
    edge_curve_target: EnumProperty(
        name="Curve Surfaces",
        items=(
            (SURFACE_BOTH, "Both Sides", "Generate curves for every available inner and outer surface"),
            (SURFACE_INNER, "Inner", "Generate the inner-surface curve if available"),
            (SURFACE_OUTER, "Outer", "Generate the outer-surface curve if available"),
        ),
        default=SURFACE_BOTH,
    )
    edge_curve_row: EnumProperty(
        name="Reference Row",
        items=(
            (ROW_OUTERMOST, "Outermost", "Use the outermost longitudinal edge row"),
            (ROW_SECOND, "Second from Outermost", "Use the second longitudinal edge row from the outside"),
        ),
        default=ROW_OUTERMOST,
    )
    edge_curve_status: StringProperty(default="")
    object_rename_base_text: StringProperty(
        name="New Name",
        description="Base name assigned to selected objects in Scene Collection order",
        default="",
    )
    object_rename_edit_text: StringProperty(
        name="Text",
        description="Text to add to or remove from selected object names",
        default="",
    )
    object_rename_include_hidden: BoolProperty(
        name="Include Hidden Selected Objects",
        description="Include selected objects that are hidden in the current View Layer",
        default=False,
    )
    object_rename_status: StringProperty(default="")
    name_status: StringProperty(default="")


def character_display_width(character):
    return 2 if unicodedata.east_asian_width(character) in {"W", "F", "A"} else 1


def string_display_width(value):
    return sum(character_display_width(character) for character in value)


def display_tokens(message):
    tokens = []
    ascii_buffer = ""
    for character in message:
        is_ascii_word = ord(character) < 128 and not character.isspace()
        if is_ascii_word:
            ascii_buffer += character
            continue
        if ascii_buffer:
            tokens.append(ascii_buffer)
            ascii_buffer = ""
        tokens.append(character)
    if ascii_buffer:
        tokens.append(ascii_buffer)
    return tokens


def wrap_display_text(message, width):
    opening_punctuation = set("（([『「【〈《")
    closing_punctuation = set("、。，．・：；？！)]）』」】〉》")
    lines = []
    current = ""
    current_width = 0

    for token in display_tokens(message):
        if token == "\n":
            lines.append(current.rstrip())
            current = ""
            current_width = 0
            continue
        if token.isspace():
            if current and not current.endswith(" "):
                current += " "
                current_width += 1
            continue

        token_width = string_display_width(token)
        would_overflow = current and current_width + token_width > width
        if would_overflow and token in closing_punctuation:
            current += token
            current_width += token_width
            continue
        if would_overflow:
            if current.rstrip() and current.rstrip()[-1] in opening_punctuation:
                opening = current.rstrip()[-1]
                current = current.rstrip()[:-1].rstrip()
                if current:
                    lines.append(current)
                current = opening + token
                current_width = string_display_width(current)
                continue
            lines.append(current.rstrip())
            current = token
            current_width = token_width
        else:
            current += token
            current_width += token_width

    if current or not lines:
        lines.append(current.rstrip())
    return lines


def wrapped_labels(layout, message, icon="NONE", width=None):
    if width is None:
        region = getattr(bpy.context, "region", None)
        region_width = region.width if region is not None else 320
        width = max(8, int((region_width - 56) / 7))
    message = " ".join(str(message).splitlines())
    if string_display_width(message) > width:
        limit = max(1, width - character_display_width("…"))
        result = ""
        used = 0
        for character in message:
            character_width = character_display_width(character)
            if used + character_width > limit:
                break
            result += character
            used += character_width
        message = result.rstrip() + "…"
    layout.label(text=message, icon=icon)


class VIEW3D_PT_agrace_tools(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_agrace_tools"
    bl_label = "AGRace Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AGRace Tools"

    def draw(self, context):
        wrapped_labels(self.layout, tr("Tools distributed with AGRaceSDK."), "TOOL_SETTINGS")


class VIEW3D_PT_agrace_smooth_transition(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_agrace_smooth_transition"
    bl_label = "Y-Axis Smooth Transition"
    bl_parent_id = "VIEW3D_PT_agrace_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        settings = context.window_manager.agrace_tools

        guide = layout.box()
        for message in (
            "Place two edges in the same object and select them in Edit Mode.",
            "They connect along the Y axis.",
            "Select four edges to generate upper and lower surfaces together.",
        ):
            wrapped_labels(guide, tr(message))

        column = layout.column(align=True)
        column.use_property_split = True
        column.prop(settings, "ring_count")
        column.prop(settings, "outward_bulge")
        column.prop(settings, "use_squared_x_weight")
        column.prop(settings, "smooth_raycast_receiver")
        column.prop(settings, "smooth_generate_uv")

        operator = layout.operator(
            "mesh.agrace_smooth_transition",
            text=tr("Generate Smooth Transition (Separate Object)"),
            icon="MOD_SMOOTH",
        )
        operator.ring_count = settings.ring_count
        operator.outward_bulge = settings.outward_bulge
        operator.use_squared_x_weight = settings.use_squared_x_weight
        operator.raycast_receiver = settings.smooth_raycast_receiver
        operator.generate_uv = settings.smooth_generate_uv
        if settings.smooth_status:
            status = layout.box()
            status.label(text=tr("Status"), icon="INFO")
            wrapped_labels(status, settings.smooth_status)


class VIEW3D_PT_agrace_smooth_edge_curve(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_agrace_smooth_edge_curve"
    bl_label = "Y-Axis Edge Curve"
    bl_parent_id = "VIEW3D_PT_agrace_smooth_transition"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        settings = context.window_manager.agrace_tools

        column = layout.column(align=True)
        column.use_property_split = True
        column.prop(settings, "smooth_curve_row")

        operator = layout.operator(
            "curve.agrace_smooth_edge_curve",
            text=tr("Generate Curve Along Edge"),
            icon="CURVE_BEZCURVE",
        )
        operator.row = settings.smooth_curve_row

        if settings.smooth_curve_status:
            status = layout.box()
            status.label(text=tr("Status"), icon="INFO")
            wrapped_labels(status, settings.smooth_curve_status)


class VIEW3D_PT_agrace_cylinder_transition(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_agrace_cylinder_transition"
    bl_label = "Cylinder Smooth Transition"
    bl_parent_id = "VIEW3D_PT_agrace_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        settings = context.window_manager.agrace_tools

        guide = layout.box()
        for message in (
            "Semicircle to Circle generates directly.",
            "In Edit Mode, halve the arbitrary edge, place it on +X, and select it.",
        ):
            wrapped_labels(guide, tr(message))

        column = layout.column(align=True)
        column.use_property_split = True
        column.prop(settings, "cylinder_mode")
        column.prop(settings, "cylinder_y_length")
        column.prop(settings, "cylinder_y_divisions")

        vertex_row = column.row()
        vertex_row.enabled = settings.cylinder_mode == MODE_SEMI_TO_CIRCLE
        vertex_row.prop(settings, "cylinder_vertex_count")

        custom_toggle_row = column.row()
        custom_toggle_row.enabled = settings.cylinder_mode != MODE_EDGE_TO_CIRCLE
        custom_toggle_row.prop(settings, "cylinder_use_custom_angle")

        custom_angle_row = column.row()
        custom_angle_row.enabled = (
            settings.cylinder_mode != MODE_EDGE_TO_CIRCLE
            and settings.cylinder_use_custom_angle
        )
        custom_angle_row.prop(settings, "cylinder_custom_angle")

        column.prop(settings, "cylinder_raycast_receiver")

        selection = {"count": 0, "counts": (), "message": ""}
        if settings.cylinder_mode != MODE_SEMI_TO_CIRCLE:
            selection = inspect_selection(context)

        shape = layout.column(align=True)
        shape.use_property_split = True
        if selection["count"] == 1:
            shape.prop(settings, "cylinder_single_surface")
        else:
            shape.prop(settings, "cylinder_connection")
            shape.prop(settings, "cylinder_surface_mode")
        shape.prop(settings, "cylinder_radius")
        shape.prop(settings, "cylinder_radius_reference")
        shape.prop(settings, "cylinder_thickness")

        both_surfaces = (
            selection["count"] != 1 and settings.cylinder_surface_mode == SURFACE_BOTH
        )
        closure = layout.column(align=True)
        closure.enabled = both_surfaces
        closure.prop(settings, "cylinder_generate_sides")
        closure.prop(settings, "cylinder_generate_caps")
        layout.prop(settings, "cylinder_generate_uv")

        operator = layout.operator(
            "mesh.agrace_cylinder_transition",
            text=tr("Generate Cylinder Transition (Separate Object)"),
            icon="MESH_CYLINDER",
        )
        operator.mode = settings.cylinder_mode
        operator.y_length = settings.cylinder_y_length
        operator.y_divisions = settings.cylinder_y_divisions
        operator.vertex_count = settings.cylinder_vertex_count
        operator.use_custom_angle = settings.cylinder_use_custom_angle
        operator.custom_angle = settings.cylinder_custom_angle
        operator.connection = settings.cylinder_connection
        operator.radius = settings.cylinder_radius
        operator.radius_reference = settings.cylinder_radius_reference
        operator.thickness = settings.cylinder_thickness
        operator.surface_mode = settings.cylinder_surface_mode
        operator.single_surface = settings.cylinder_single_surface
        operator.generate_sides = settings.cylinder_generate_sides
        operator.generate_caps = settings.cylinder_generate_caps
        operator.generate_uv = settings.cylinder_generate_uv
        operator.raycast_receiver = settings.cylinder_raycast_receiver

        if settings.cylinder_mode != MODE_SEMI_TO_CIRCLE:
            selection_box = layout.box()
            selection_box.label(text=tr("Selection"), icon="EDGESEL")
            if selection["count"] == 1:
                wrapped_labels(
                    selection_box,
                    tr("One edge chain selected: {vertices} vertices.").format(
                        vertices=selection["counts"][0]
                    ),
                )
            elif selection["count"] == 2:
                wrapped_labels(
                    selection_box,
                    tr("Two edge chains selected: {a} / {b} vertices.").format(
                        a=selection["counts"][0], b=selection["counts"][1]
                    ),
                )
            elif selection["message"]:
                wrapped_labels(selection_box, selection["message"], "INFO")
            else:
                wrapped_labels(
                    selection_box,
                    tr("Select one or two open half-width edge chains."),
                    "INFO",
                )

        if settings.cylinder_status:
            status = layout.box()
            status.label(text=tr("Status"), icon="INFO")
            wrapped_labels(status, settings.cylinder_status)


class VIEW3D_PT_agrace_edge_curve(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_agrace_edge_curve"
    bl_label = "Cylinder Edge Curve"
    bl_parent_id = "VIEW3D_PT_agrace_cylinder_transition"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        settings = context.window_manager.agrace_tools

        column = layout.column(align=True)
        column.use_property_split = True
        column.prop(settings, "edge_curve_target")
        column.prop(settings, "edge_curve_row")

        operator = layout.operator(
            "curve.agrace_edge_curve",
            text=tr("Generate Curve Along Edge"),
            icon="CURVE_BEZCURVE",
        )
        operator.target = settings.edge_curve_target
        operator.row = settings.edge_curve_row

        if settings.edge_curve_status:
            status = layout.box()
            status.label(text=tr("Status"), icon="INFO")
            wrapped_labels(status, settings.edge_curve_status)


class VIEW3D_PT_agrace_object_renamer(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_agrace_object_renamer"
    bl_label = "Object Renamer"
    bl_parent_id = "VIEW3D_PT_agrace_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        settings = context.window_manager.agrace_tools

        wrapped_labels(layout, tr("Renames selected objects only in Object Mode."))
        layout.prop(settings, "object_rename_include_hidden")

        sequential = layout.box()
        sequential.label(text=tr("Sequential Rename"))
        sequential.prop(settings, "object_rename_base_text")
        button = sequential.column()
        button.enabled = context.mode == "OBJECT" and bool(settings.object_rename_base_text)
        button.operator(
            "object.agrace_rename_selected_base",
            text=tr("Rename Sequentially"),
            icon="SORTALPHA",
        )
        renumber = sequential.column()
        renumber.enabled = context.mode == "OBJECT"
        renumber.operator(
            "object.agrace_renumber_selected_names",
            text=tr("Renumber Sequential Numbers"),
            icon="SORTALPHA",
        )

        text_edit = layout.box()
        text_edit.label(text=tr("Add / Remove Text"))
        text_edit.prop(settings, "object_rename_edit_text")
        buttons = text_edit.column(align=True)
        buttons.enabled = context.mode == "OBJECT" and bool(settings.object_rename_edit_text)
        buttons.operator(
            "object.agrace_prepend_selected_names",
            text=tr("Add to Beginning"),
            icon="ADD",
        )
        buttons.operator(
            "object.agrace_append_selected_names",
            text=tr_agrace("Add to End"),
            icon="ADD",
        )
        buttons.operator(
            "object.agrace_remove_selected_name_text",
            text=tr("Remove Matching Text"),
            icon="REMOVE",
        )

        if settings.object_rename_status:
            status = layout.box()
            status.label(text=tr("Status"), icon="INFO")
            wrapped_labels(status, settings.object_rename_status)


class VIEW3D_PT_agrace_data_name_sync(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_agrace_data_name_sync"
    bl_label = "Mesh / Curve Data Name Sync"
    bl_parent_id = "VIEW3D_PT_agrace_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        settings = context.window_manager.agrace_tools
        wrapped_labels(
            layout,
            tr("Align local Mesh / Curve data names with their object names."),
        )

        buttons = layout.column(align=True)
        buttons.operator(
            "object.agrace_analyze_data_names",
            text=tr("Analyze Changes"),
            icon="VIEWZOOM",
        )
        buttons.operator(
            "object.agrace_sync_data_names",
            text=tr("Safely Sync Names"),
            icon="CHECKMARK",
        )

        wrapped_labels(layout, tr("Shared, linked, overridden, and colliding data are skipped."), "INFO")
        if settings.name_status:
            status = layout.box()
            status.label(text=tr("Status"), icon="INFO")
            wrapped_labels(status, settings.name_status)
