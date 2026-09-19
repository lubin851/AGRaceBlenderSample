# SPDX-FileCopyrightText: 2026 尾黒こう (Ryuban)
# SPDX-License-Identifier: GPL-3.0-or-later

from collections import Counter, defaultdict

import bpy

from .translations import tr


TARGET_OBJECT_TYPES = {"MESH", "CURVE"}
REFERENCE_OBJECT_TYPES = {"MESH", "CURVE", "SURFACE", "FONT"}

STATUS_READY = "READY"
STATUS_RENAMED = "RENAMED"
STATUS_UNCHANGED = "UNCHANGED"
STATUS_SHARED = "SHARED"
STATUS_LINKED = "LINKED"
STATUS_COLLISION = "COLLISION"
STATUS_ERROR = "ERROR"


def scene_target_objects(scene):
    objects = {}
    for obj in scene.collection.all_objects:
        if obj.type in TARGET_OBJECT_TYPES and obj.data is not None:
            objects[obj.as_pointer()] = obj
    return sorted(objects.values(), key=lambda obj: obj.name_full.casefold())


def data_object_references():
    references = defaultdict(list)
    for obj in bpy.data.objects:
        if obj.type in REFERENCE_OBJECT_TYPES and obj.data is not None:
            references[obj.data.as_pointer()].append(obj)
    return references


def new_record(obj, status, detail):
    data = obj.data
    return {
        "object": obj,
        "data": data,
        "namespace": "MESH" if obj.type == "MESH" else "CURVE",
        "object_type": obj.type,
        "status": status,
        "object_name": obj.name,
        "data_name": data.name,
        "target_name": obj.name,
        "detail": detail,
    }


def build_rename_plan(scene):
    scene_objects = scene_target_objects(scene)
    scene_pointers = {obj.as_pointer() for obj in scene_objects}
    all_references = data_object_references()
    records = []
    candidates = []

    for obj in scene_objects:
        data = obj.data
        if data.name == obj.name:
            records.append(new_record(obj, STATUS_UNCHANGED, "Already has the same name"))
            continue
        if data.library is not None or data.override_library is not None or not data.is_editable:
            records.append(new_record(obj, STATUS_LINKED, "Linked, overridden, or non-editable data"))
            continue

        references = all_references.get(data.as_pointer(), [])
        if len(references) > 1 or data.users > 1:
            ref_names = []
            for reference in sorted(references, key=lambda item: item.name_full.casefold()):
                scope = "scene" if reference.as_pointer() in scene_pointers else "outside scene"
                ref_names.append(f"{reference.name_full} ({scope})")
            detail = "Shared data; references: " + (", ".join(ref_names) or "unavailable")
            if data.users > len(references):
                detail += f"; Blender users: {data.users}"
            records.append(new_record(obj, STATUS_SHARED, detail))
            continue

        record = new_record(obj, STATUS_READY, "Can be renamed safely")
        records.append(record)
        candidates.append(record)

    target_counts = Counter((record["namespace"], record["target_name"]) for record in candidates)
    active = []
    for record in candidates:
        key = (record["namespace"], record["target_name"])
        if target_counts[key] > 1:
            record["status"] = STATUS_COLLISION
            record["detail"] = f"Multiple objects request the data name '{record['target_name']}'"
        else:
            active.append(record)

    local_data = {
        **{("MESH", mesh.name): mesh for mesh in bpy.data.meshes if mesh.library is None},
        **{("CURVE", curve.name): curve for curve in bpy.data.curves if curve.library is None},
    }

    changed = True
    while changed:
        changed = False
        active_pointers = {record["data"].as_pointer() for record in active}
        still_active = []
        for record in active:
            occupant = local_data.get((record["namespace"], record["target_name"]))
            occupant_is_self = occupant is record["data"]
            occupant_will_move = occupant is not None and occupant.as_pointer() in active_pointers
            if occupant is not None and not occupant_is_self and not occupant_will_move:
                record["status"] = STATUS_COLLISION
                record["detail"] = f"Excluded data '{occupant.name_full}' already uses the requested name"
                changed = True
            else:
                still_active.append(record)
        active = still_active
    return records


def counts_for(records):
    return Counter(record["status"] for record in records)


def print_report(records, heading):
    counts = counts_for(records)
    print("\n" + "=" * 72)
    print(f"AGRace Tools - Mesh / Curve Data Name Sync: {heading}")
    print(
        f"Targets {len(records)} / Ready {counts[STATUS_READY]} / Renamed {counts[STATUS_RENAMED]} / "
        f"Unchanged {counts[STATUS_UNCHANGED]} / Shared {counts[STATUS_SHARED]} / "
        f"Linked {counts[STATUS_LINKED]} / Collision {counts[STATUS_COLLISION]} / Error {counts[STATUS_ERROR]}"
    )
    print("-" * 72)
    for record in records:
        if record["status"] == STATUS_UNCHANGED:
            continue
        print(
            f"[{record['status']}] {record['object_type']} Object: {record['object_name']} | "
            f"Data: {record['data_name']} -> {record['target_name']}"
        )
        print(f"    {record['detail']}")
    print("=" * 72)


def temporary_name(data, ordinal):
    return f"__AGRACE_DATA_NAME_SYNC_{data.as_pointer():X}_{ordinal}__"


def put_on_temporary_names(records):
    for ordinal, record in enumerate(records):
        record["data"].name = temporary_name(record["data"], ordinal)


def restore_original_names(records, original_names):
    put_on_temporary_names(records)
    for record in records:
        record["data"].name = original_names[record["data"].as_pointer()]


def apply_rename_plan(records):
    ready = [record for record in records if record["status"] == STATUS_READY]
    if not ready:
        return 0
    original_names = {record["data"].as_pointer(): record["data_name"] for record in ready}
    try:
        put_on_temporary_names(ready)
        for record in ready:
            record["data"].name = record["target_name"]
        mismatches = [record for record in ready if record["data"].name != record["target_name"]]
        if mismatches:
            raise RuntimeError("Final data names did not match the requested names: " + ", ".join(record["object_name"] for record in mismatches))
    except Exception as error:
        try:
            restore_original_names(ready, original_names)
            detail = f"{error}; original names restored"
        except Exception as rollback_error:
            detail = f"{error}; rollback also failed: {rollback_error}"
        for record in ready:
            record["status"] = STATUS_ERROR
            record["detail"] = detail
        raise RuntimeError(detail) from error

    for record in ready:
        record["status"] = STATUS_RENAMED
        record["detail"] = "Renamed to match the object"
    return len(ready)


class OBJECT_OT_agrace_analyze_data_names(bpy.types.Operator):
    bl_idname = "object.agrace_analyze_data_names"
    bl_label = "Analyze Changes"
    bl_description = "Analyze safe Mesh and Curve data-name changes without modifying data"

    def execute(self, context):
        records = build_rename_plan(context.scene)
        print_report(records, "Analysis")
        counts = counts_for(records)
        ready = counts[STATUS_READY]
        skipped = len(records) - ready - counts[STATUS_UNCHANGED]
        message = tr("Analysis complete: {ready} change(s), {skipped} skipped.").format(ready=ready, skipped=skipped)
        context.window_manager.agrace_tools.name_status = message
        self.report({"INFO"}, message)
        return {"FINISHED"}


class OBJECT_OT_agrace_sync_data_names(bpy.types.Operator):
    bl_idname = "object.agrace_sync_data_names"
    bl_label = "Safely Sync Names"
    bl_description = "Rename safe local single-user Mesh and Curve data to match object names"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        records = build_rename_plan(context.scene)
        print_report(records, "Preflight")
        try:
            renamed = apply_rename_plan(records)
        except RuntimeError as error:
            print_report(records, "Error")
            print(f"[AGRace Tools][NS999] {error}")
            message = tr("Name sync failed. Original names were restored.")
            context.window_manager.agrace_tools.name_status = message
            self.report({"ERROR"}, message)
            return {"CANCELLED"}

        print_report(records, "Result")
        message = tr("Name sync complete: {renamed} data-block(s) renamed.").format(renamed=renamed)
        context.window_manager.agrace_tools.name_status = message
        self.report({"INFO"}, message)
        return {"FINISHED"}
