# SPDX-FileCopyrightText: 2026 尾黒こう (Ryuban)
# SPDX-License-Identifier: GPL-3.0-or-later

from collections import Counter
import re

import bpy

from .translations import AGRACE_TRANSLATION_CONTEXT, tr


STATUS_RENAMED = "RENAMED"
STATUS_UNCHANGED = "UNCHANGED"
STATUS_EMPTY = "EMPTY"
STATUS_LINKED = "LINKED"
STATUS_ERROR = "ERROR"


def selected_scene_objects(context, include_hidden):
    """Return selected objects in the Scene Collection order captured before renaming."""
    result = []
    seen = set()
    for obj in context.scene.collection.all_objects:
        pointer = obj.as_pointer()
        if pointer in seen:
            continue
        seen.add(pointer)
        try:
            selected = obj.select_get(view_layer=context.view_layer)
            visible = obj.visible_get(view_layer=context.view_layer)
        except RuntimeError:
            continue
        if selected and (include_hidden or visible):
            result.append(obj)
    return result


def new_record(obj, desired_name):
    return {
        "object": obj,
        "original_name": obj.name,
        "desired_name": desired_name,
        "final_name": obj.name,
        "status": None,
        "detail": "",
    }


def build_records(objects, operation, text):
    records = []
    for obj in objects:
        if operation == "BASE":
            desired_name = text
        elif operation == "PREPEND":
            desired_name = text + obj.name
        elif operation == "APPEND":
            desired_name = obj.name + text
        elif operation == "REMOVE":
            desired_name = obj.name.replace(text, "")
        else:
            raise ValueError(f"Unknown rename operation: {operation}")

        record = new_record(obj, desired_name)
        if obj.library is not None or not obj.is_editable:
            record["status"] = STATUS_LINKED
            record["detail"] = "Linked or non-editable object"
        elif operation != "BASE" and desired_name == obj.name:
            record["status"] = STATUS_UNCHANGED
            record["detail"] = "The object name does not contain the requested text"
        elif not desired_name:
            record["status"] = STATUS_EMPTY
            record["detail"] = "Removing the text would leave an empty object name"
        records.append(record)
    return records


def build_renumber_records(objects):
    records = []
    for obj in objects:
        match = re.match(r"^(.*)\.(\d{3,})$", obj.name)
        base_name = match.group(1) if match is not None and match.group(1) else obj.name
        # Request the same root for every member, including the unsuffixed object.
        # apply_records frees all target names first and lets Blender allocate suffixes.
        record = new_record(obj, base_name)
        if obj.library is not None or not obj.is_editable:
            record["status"] = STATUS_LINKED
            record["detail"] = "Linked or non-editable object"
        records.append(record)
    return records


def temporary_name(obj, ordinal):
    return f"__AGRACE_OBJECT_RENAME_{obj.as_pointer():X}_{ordinal}__"


def put_on_temporary_names(records):
    for ordinal, record in enumerate(records):
        obj = record["object"]
        requested = temporary_name(obj, ordinal)
        obj.rename(requested, mode="NEVER")
        if obj.name != requested:
            raise RuntimeError(f"Could not assign temporary name to '{record['original_name']}'")


def expected_name_without_external_collision(desired_name, occurrence):
    if occurrence == 0:
        return desired_name
    match = re.match(r"^(.*)\.(\d{3,})$", desired_name)
    if match:
        root, digits = match.groups()
        number = int(digits) + occurrence
        return f"{root}.{number:0{max(3, len(digits))}d}"
    return f"{desired_name}.{occurrence:03d}"


def restore_original_names(records):
    put_on_temporary_names(records)
    for record in records:
        obj = record["object"]
        obj.rename(record["original_name"], mode="NEVER")
        if obj.name != record["original_name"]:
            raise RuntimeError(f"Could not restore original name '{record['original_name']}'")


def apply_records(records):
    active = [record for record in records if record["status"] is None]
    if not active:
        return 0

    occurrences = Counter()
    try:
        put_on_temporary_names(active)
        for record in active:
            obj = record["object"]
            desired_name = record["desired_name"]
            occurrence = occurrences[desired_name]
            expected_name = expected_name_without_external_collision(desired_name, occurrence)
            occurrences[desired_name] += 1

            obj.rename(desired_name, mode="NEVER")
            record["final_name"] = obj.name
            if obj.name == record["original_name"]:
                record["status"] = STATUS_UNCHANGED
                record["detail"] = "The object already had its assigned sequential name"
            else:
                record["status"] = STATUS_RENAMED
                record["detail"] = "Object renamed"

            if obj.name != expected_name:
                print(
                    "[AGRace Tools][OR101] Unselected name collision(s) were skipped / "
                    f"選択外の名前被りをスキップ: requested '{expected_name}', assigned '{obj.name}'"
                )
    except Exception as error:
        try:
            restore_original_names(active)
            detail = f"{error}; original names restored"
        except Exception as rollback_error:
            detail = f"{error}; rollback also failed: {rollback_error}"
        for record in active:
            record["status"] = STATUS_ERROR
            record["detail"] = detail
        raise RuntimeError(detail) from error
    return sum(record["status"] == STATUS_RENAMED for record in active)


def print_report(records, heading):
    counts = Counter(record["status"] for record in records)
    print("\n" + "=" * 72)
    print(f"AGRace Tools - Object Renamer: {heading}")
    print(
        f"Targets {len(records)} / Renamed {counts[STATUS_RENAMED]} / "
        f"Unchanged {counts[STATUS_UNCHANGED]} / "
        f"Empty {counts[STATUS_EMPTY]} / "
        f"Linked {counts[STATUS_LINKED]} / Error {counts[STATUS_ERROR]}"
    )
    print("-" * 72)
    for record in records:
        if record["status"] == STATUS_UNCHANGED:
            continue
        print(
            f"[{record['status']}] Object: {record['original_name']} -> {record['final_name']} | "
            f"Requested: {record['desired_name']}"
        )
        if record["detail"]:
            print(f"    {record['detail']}")
    print("=" * 72)


def redraw_interface(context):
    screen = getattr(context, "screen", None)
    if screen is not None:
        for area in screen.areas:
            area.tag_redraw()
        return
    area = getattr(context, "area", None)
    if area is not None:
        area.tag_redraw()


def run_rename(self, context, operation, text):
    settings = context.window_manager.agrace_tools
    if operation != "RENUMBER" and not text:
        message = tr("Enter text for the object renamer.")
        settings.object_rename_status = message
        redraw_interface(context)
        self.report({"WARNING"}, message)
        return {"CANCELLED"}

    objects = selected_scene_objects(context, settings.object_rename_include_hidden)
    if not objects:
        message = tr("Select at least one object in Object Mode.")
        settings.object_rename_status = message
        redraw_interface(context)
        self.report({"WARNING"}, message)
        return {"CANCELLED"}

    if operation == "RENUMBER":
        records = build_renumber_records(objects)
    else:
        records = build_records(objects, operation, text)
    try:
        renamed = apply_records(records)
    except RuntimeError as error:
        print_report(records, "Error")
        print(f"[AGRace Tools][OR999] {error}")
        message = tr("Object rename failed. Original names were restored.")
        settings.object_rename_status = message
        redraw_interface(context)
        self.report({"ERROR"}, message)
        return {"CANCELLED"}

    print_report(records, "Result")
    counts = Counter(record["status"] for record in records)
    skipped = len(records) - renamed - counts[STATUS_UNCHANGED]
    message = tr("Object rename complete: {renamed} renamed, {unchanged} unchanged, {skipped} skipped.").format(
        renamed=renamed,
        unchanged=counts[STATUS_UNCHANGED],
        skipped=skipped,
    )
    settings.object_rename_status = message
    redraw_interface(context)
    self.report({"INFO"}, message)
    return {"FINISHED"}


class ObjectRenamerOperatorMixin:
    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"


class OBJECT_OT_agrace_rename_selected_base(ObjectRenamerOperatorMixin, bpy.types.Operator):
    bl_idname = "object.agrace_rename_selected_base"
    bl_label = "Rename Sequentially"
    bl_description = "Rename selected objects in the captured Scene Collection order using Blender numeric suffixes"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        return run_rename(self, context, "BASE", context.window_manager.agrace_tools.object_rename_base_text)


class OBJECT_OT_agrace_prepend_selected_names(ObjectRenamerOperatorMixin, bpy.types.Operator):
    bl_idname = "object.agrace_prepend_selected_names"
    bl_label = "Add to Beginning"
    bl_description = "Add the entered text to the beginning of every selected object name"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        return run_rename(self, context, "PREPEND", context.window_manager.agrace_tools.object_rename_edit_text)


class OBJECT_OT_agrace_append_selected_names(ObjectRenamerOperatorMixin, bpy.types.Operator):
    bl_idname = "object.agrace_append_selected_names"
    bl_label = "Add to End"
    bl_translation_context = AGRACE_TRANSLATION_CONTEXT
    bl_description = "Add the entered text to the end of every selected object name"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        return run_rename(self, context, "APPEND", context.window_manager.agrace_tools.object_rename_edit_text)


class OBJECT_OT_agrace_renumber_selected_names(ObjectRenamerOperatorMixin, bpy.types.Operator):
    bl_idname = "object.agrace_renumber_selected_names"
    bl_label = "Renumber Sequential Numbers"
    bl_description = "Renumber Blender-style numeric suffixes by captured Scene Collection order"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        return run_rename(self, context, "RENUMBER", "")


class OBJECT_OT_agrace_remove_selected_name_text(ObjectRenamerOperatorMixin, bpy.types.Operator):
    bl_idname = "object.agrace_remove_selected_name_text"
    bl_label = "Remove Matching Text"
    bl_description = "Remove every case-sensitive exact occurrence of the entered text from selected object names"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        return run_rename(self, context, "REMOVE", context.window_manager.agrace_tools.object_rename_edit_text)
