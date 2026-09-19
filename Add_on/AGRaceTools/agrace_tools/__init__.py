# SPDX-FileCopyrightText: 2026 尾黒こう (Ryuban)
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.props import PointerProperty

from .name_sync import (
    OBJECT_OT_agrace_analyze_data_names,
    OBJECT_OT_agrace_sync_data_names,
)
from .object_renamer import (
    OBJECT_OT_agrace_append_selected_names,
    OBJECT_OT_agrace_prepend_selected_names,
    OBJECT_OT_agrace_renumber_selected_names,
    OBJECT_OT_agrace_remove_selected_name_text,
    OBJECT_OT_agrace_rename_selected_base,
)
from .cylinder_transition import MESH_OT_agrace_cylinder_transition
from .edge_curve import CURVE_OT_agrace_edge_curve, CURVE_OT_agrace_smooth_edge_curve
from .smooth_transition import MESH_OT_agrace_smooth_transition
from .translations import TRANSLATIONS
from .ui import (
    AGRACE_PG_settings,
    VIEW3D_PT_agrace_cylinder_transition,
    VIEW3D_PT_agrace_data_name_sync,
    VIEW3D_PT_agrace_edge_curve,
    VIEW3D_PT_agrace_object_renamer,
    VIEW3D_PT_agrace_smooth_edge_curve,
    VIEW3D_PT_agrace_smooth_transition,
    VIEW3D_PT_agrace_tools,
)


CLASSES = (
    AGRACE_PG_settings,
    MESH_OT_agrace_smooth_transition,
    MESH_OT_agrace_cylinder_transition,
    CURVE_OT_agrace_edge_curve,
    CURVE_OT_agrace_smooth_edge_curve,
    OBJECT_OT_agrace_analyze_data_names,
    OBJECT_OT_agrace_sync_data_names,
    OBJECT_OT_agrace_rename_selected_base,
    OBJECT_OT_agrace_prepend_selected_names,
    OBJECT_OT_agrace_append_selected_names,
    OBJECT_OT_agrace_renumber_selected_names,
    OBJECT_OT_agrace_remove_selected_name_text,
    VIEW3D_PT_agrace_tools,
    VIEW3D_PT_agrace_smooth_transition,
    VIEW3D_PT_agrace_smooth_edge_curve,
    VIEW3D_PT_agrace_cylinder_transition,
    VIEW3D_PT_agrace_edge_curve,
    VIEW3D_PT_agrace_object_renamer,
    VIEW3D_PT_agrace_data_name_sync,
)


def register():
    bpy.app.translations.register(__package__, TRANSLATIONS)
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.agrace_tools = PointerProperty(type=AGRACE_PG_settings)


def unregister():
    if hasattr(bpy.types.WindowManager, "agrace_tools"):
        del bpy.types.WindowManager.agrace_tools
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
    bpy.app.translations.unregister(__package__)
