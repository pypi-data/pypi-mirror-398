from typing import Any, Dict

from a4x.orchestration.site import PersistencyType, Scheduler, StorageType
from jsonschema import Draft202012Validator, ValidationError
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

_annotation_schema = {
    "title": "Annotatable",
    "description": "An object that can accept arbitrary user annotations",
    "$id": "a4x-orchestration-config:annotation",
    "type": "object",
    "properites": {"annotations": {"type": "object"}},
}

_string_or_directory_schema = {
    "anyOf": [
        {"type": "string"},
        {
            "type": "object",
            "properties": {
                "site": {"type": "string"},
                "directory": {"type": "string"},
            },
            "required": ["site", "directory"],
        },
    ]
}

_schedulable_schema = {
    "title": "Scheduable",
    "description": "An object that contains information related to scheduling",
    "$id": "a4x-orchestration-config:schedulable",
    "$ref": "a4x-orchestration-config:annotation",
    "type": "object",
    "properties": {
        "duration": {"type": ["integer", "string"]},
        "queue": {"type": "string"},
        "cwd": {
            **_string_or_directory_schema,
        },
        "environment": {
            "type": "object",
        },
        "stdin": {"type": "string"},
        "stdout": {"type": "string"},
        "stderr": {"type": "string"},
        "resources": {
            "type": "object",
            "properties": {
                "num_procs": {"type": "integer", "exclusiveMinimum": 0},
                "cores_per_proc": {"type": "integer", "exclusiveMinimum": 0},
                "gpus_per_proc": {"type": "integer", "exclusiveMinimum": 0},
                "num_nodes": {"type": "integer", "exclusiveMinimum": 0},
                "exclusive": {"type": "boolean"},
                "exclusive_node_per_proc": {"type": "boolean"},
            },
            "required": ["num_procs"],
        },
        "resources_w_slot": {
            "type": "object",
            "properties": {
                "num_procs": {"type": "integer", "exclusiveMinimum": 0},
                "num_nodes": {
                    "anyOf": [
                        {"type": "null"},
                        {"type": "integer", "exclusiveMinimum": 0},
                    ]
                },
                "num_slots_per_node": {
                    "anyOf": [
                        {"type": "null"},
                        {"type": "integer", "exclusiveMinimum": 0},
                    ]
                },
                "exclusive": {"type": "boolean"},
                "slot": {
                    "type": "object",
                    "properties": {
                        "num_nodes": {
                            "anyOf": [
                                {"type": "null"},
                                {"type": "integer", "exclusiveMinimum": 0},
                            ]
                        },
                        "num_cores": {
                            "anyOf": [
                                {"type": "null"},
                                {"type": "integer", "exclusiveMinimum": 0},
                            ]
                        },
                        "num_gpus": {
                            "anyOf": [
                                {"type": "null"},
                                {"type": "integer", "exclusiveMinimum": 0},
                            ]
                        },
                    },
                    "minProperties": 1,
                },
            },
            "required": ["num_procs", "slot"],
        },
    },
}

_ANNOTATION_SCHEMA_RESOURCE = Resource(
    contents=_annotation_schema, specification=DRAFT202012
)
_SCHEDULABLE_SCHEMA_RESOURCE = Resource(
    contents=_schedulable_schema, specification=DRAFT202012
)
_SCHEMA_REGISTRY = Registry().with_resources(
    [
        (_annotation_schema["$id"], _ANNOTATION_SCHEMA_RESOURCE),
        (_schedulable_schema["$id"], _SCHEDULABLE_SCHEMA_RESOURCE),
    ]
)

_directory_schema = {
    "title": "Directory",
    "description": "A directory on a Site",
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "path": {"type": "string"},
        "storage_type": {
            "anyOf": [
                {"type": "null"},
                {"enum": [member.value for member in StorageType]},
            ]
        },
        "persistency": {
            "anyOf": [
                {"type": "null"},
                {"enum": [member.value for member in PersistencyType]},
            ]
        },
    },
    "required": ["name", "path"],
}

_site_schema = {
    "title": "Site",
    "description": "A system or other site where tasks can run or data can be stored",
    "$ref": "a4x-orchestration-config:annotation",
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "scheduler": {
            "anyOf": [
                {"type": "null"},
                {"enum": [member.value for member in Scheduler]},
            ]
        },
        "directories": {"type": "array", "items": {**_directory_schema}},
    },
    "required": ["name"],
}

_site_list_schema = {
    "title": "Site List",
    "description": "A list of all sites in a workflow",
    "type": "array",
    "items": {**_site_schema},
}

_file_schema = {
    "title": "File",
    "description": "A file in the workflow, optionally associated with a directory and site",
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "site": {"type": ["string", "null"]},
        "directory": {"type": ["string", "null"]},
    },
    "required": ["name"],
}

_file_list_schema = {
    "title": "File List",
    "description": "A list of all files in a workflow",
    "type": "array",
    "items": {**_file_schema},
}

_command_schema = {
    "title": "Command",
    "description": "A command within a task",
    "$ref": "a4x-orchestration-config:schedulable",
    "type": "object",
    "properties": {
        "cmd": {
            "type": "string",
        },
        "args": {
            "type": "array",
            "items": {
                "anyOf": [
                    {"type": "string"},
                    {"type": "number"},
                    {
                        "type": "object",
                        "properties": {
                            "type": {"enum": ["file", "directory"]},
                            "val": {**_string_or_directory_schema},
                        },
                        "required": ["type", "val"],
                    },
                ]
            },
        },
        "description": {"type": "string"},
    },
    "required": ["cmd"],
}

_task_schema = {
    "title": "Task",
    "description": "A task in a workflow",
    "$ref": "a4x-orchestration-config:schedulable",
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "commands": {
            "type": "array",
            "items": {
                **_command_schema,
            },
        },
        "dependencies": {"type": "array", "items": {"type": "string"}},
        "site": {"type": ["string", "null"]},
        "inputs": {"type": "array", "items": {"type": "string"}},
        "outputs": {"type": "array", "items": {"type": "string"}},
        "output_extra_kwargs": {
            "type": "object",
        },
        "input_extra_kwargs": {"type": "object"},
    },
    "required": ["name", "commands"],
}

_task_list_schema = {
    "title": "Task List",
    "description": "A list of all tasks in a workflow",
    "type": "array",
    "items": {**_task_schema},
}

_workflow_schema = {
    "title": "Workflow",
    "description": "The entire workflow",
    "type": "object",
    "properties": {
        "workflow": {
            "type": "object",
            "$ref": "a4x-orchestration-config:annotation",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "sites": {
                    **_site_list_schema,
                },
                "files": {**_file_list_schema},
                "tasks": {**_task_list_schema},
                "environment": {"type": "object"},
            },
            "required": ["name", "tasks"],
        },
    },
    "required": ["workflow"],
}


def validate_config_contents(config: Dict[str, Any]):
    validator = Draft202012Validator(_workflow_schema, registry=_SCHEMA_REGISTRY)
    errors = list(validator.iter_errors(config))
    if len(errors) > 0:
        err_msg = "An error occured while parsing the A4X-Orchestration config:\n\n"
        for err in errors:
            err_msg += "----------------\n"
            err_msg += f"Error Message: {err.message}\n"
            err_msg += f"Cause: {err.cause}\n"
            err_msg += f"Failed Keyword: {err.validator}\n"
            err_msg += f"Config Path: {err.path}\n"
            err_msg += f"Schema Path: {err.schema_path}\n"
            err_msg += "----------------\n\n"
        raise ValidationError(err_msg)
