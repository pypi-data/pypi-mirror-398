from typing import Any, Dict, List, Set, Tuple

from a4x.orchestration.annotations import AnnotationType
from a4x.orchestration.command import Command
from a4x.orchestration.config.validation import validate_config_contents
from a4x.orchestration.file import File
from a4x.orchestration.resources import SchedulableWork
from a4x.orchestration.site import (
    Directory,
    PersistencyType,
    Site,
    StorageType,
)
from a4x.orchestration.task import Task
from a4x.orchestration.utils import StrCompatPathLike
from a4x.orchestration.workflow import Workflow
from ruamel.yaml import YAML


def _build_annotatable(
    in_progress_config_object: Dict[str, Any], annotatable_object: AnnotationType
):
    if len(annotatable_object.annotations_attr) > 0:
        in_progress_config_object["annotations"] = (
            annotatable_object.annotations_attr.copy()
        )


def _build_sites_object(sites: List[Site]) -> List[Dict[str, Any]]:
    sites_object = []
    for site in sites:
        curr_site_object = {
            "name": site.name,
            "scheduler": str(site.scheduler),
            "directories": [],
        }
        for dir_name, directory in site.items():
            dir_obj = {
                "name": dir_name,
                "path": str(directory.path),
            }
            if directory.storage_type == StorageType.LOCAL:
                dir_obj["storage_type"] = "local"
            elif directory.storage_type == StorageType.SHARED:
                dir_obj["storage_type"] = "shared"
            else:
                dir_obj["storage_type"] = "unknown"
            if directory.persistency == PersistencyType.PERSISTENT:
                dir_obj["persistency"] = "persistent"
            elif directory.persistency == PersistencyType.SCRATCH:
                dir_obj["persistency"] = "scratch"
            else:
                dir_obj["persistency"] = "unknown"
            curr_site_object["directories"].append(dir_obj)
        if len(curr_site_object["directories"]) == 0:
            del curr_site_object["directories"]
        _build_annotatable(curr_site_object, site)
        sites_object.append(curr_site_object)
    return sites_object


def _validate_site_and_directory(
    obj: Dict[str, Any],
    site_dict: Dict[str, Dict[str, Any]],
    object_type: str,
):
    if obj["site"] is not None:
        if obj["site"] in site_dict:
            if (
                "directory" in obj
                and obj["directory"] is not None
                and "directories" in site_dict[obj["site"]]
            ):
                site_dirs = [d["name"] for d in site_dict[obj["site"]]["directories"]]
                if obj["directory"] not in site_dirs:
                    raise ValueError(
                        f"The {object_type} '{obj['name']}' is associated with a directory '{obj['directory']}' that is not recognized for site '{obj['site']}'"
                    )
            else:
                raise ValueError(
                    f"The {object_type} '{obj['name']}' is in directory '{obj['directory']}' in site '{obj['site']}, but that site does not have any recognized directories"
                )
        else:
            raise ValueError(
                f"The {object_type} '{obj['name']}' is associated with site '{obj['site']}', but that site does not exist in the workflow"
            )


def _build_files_object(
    file_list: List[File], site_dict: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    files_object = []
    for file in file_list:
        curr_file_object = {
            "name": str(file.path_attr),
        }
        if file.directory is not None:
            curr_file_object["directory"] = str(file.directory.identifier)
            if file.directory.site is None:
                curr_file_object["site"] = None
            else:
                curr_file_object["site"] = file.directory.site.name
        else:
            curr_file_object["site"] = None
            curr_file_object["directory"] = None
        _validate_site_and_directory(curr_file_object, site_dict, "file")
        files_object.append(curr_file_object)
    return files_object


def _build_schedulable(
    in_progress_config_object: Dict[str, Any],
    schedulable_object: SchedulableWork,
    site_dict: Dict[str, Dict[str, Any]],
    file_dict: Dict[str, Dict[str, Any]],
):
    resources = schedulable_object.get_resources()
    if resources is not None:
        slot_object = {
            "num_nodes": resources.resources_per_slot.nodes,
            "num_cores": resources.resources_per_slot.cores,
            "num_gpus": resources.resources_per_slot.gpus,
        }
        resources_object = {
            "num_procs": resources.num_procs,
            "num_nodes": resources.num_nodes,
            "num_slots_per_node": resources.num_slots_per_node,
            "exclusive": resources.exclusive,
            "slot": slot_object,
        }
        if (
            resources_object["num_nodes"] is not None
            and slot_object["num_nodes"] is not None
        ):
            raise ValueError(
                "There are conflicting numbers of nodes in the Resources object and its corresponding Slot object"
            )
        in_progress_config_object["resources_w_slot"] = resources_object
    if schedulable_object.duration is not None:
        in_progress_config_object["duration"] = schedulable_object.duration
    if schedulable_object.queue is not None:
        in_progress_config_object["queue"] = schedulable_object.queue
    if schedulable_object.cwd is not None:
        if isinstance(schedulable_object.cwd, Directory):
            cwd_obj = {"directory": schedulable_object.cwd.identifier}
            if schedulable_object.cwd.site is not None:
                cwd_obj["site"] = schedulable_object.cwd.site.name
            else:
                cwd_obj["site"] = None
            _validate_site_and_directory(cwd_obj, site_dict, "cwd")
            in_progress_config_object["cwd"] = cwd_obj
        else:
            in_progress_config_object["cwd"] = str(schedulable_object.cwd)
    if (
        schedulable_object.environment is not None
        and len(schedulable_object.environment) > 0
    ):
        in_progress_config_object["environment"] = schedulable_object.environment.copy()
    if schedulable_object.stdin is not None:
        if isinstance(schedulable_object.stdin, File):
            if str(schedulable_object.stdin.path_attr) not in file_dict:
                raise ValueError(
                    f"The file '{schedulable_object.stdin.path_attr}' for stdin does not match a recognized File object"
                )
            in_progress_config_object["stdin"] = str(schedulable_object.stdin.path_attr)
        else:
            in_progress_config_object["stdin"] = str(schedulable_object.stdin)
    if schedulable_object.stdout is not None:
        if isinstance(schedulable_object.stdout, File):
            if str(schedulable_object.stdout.path_attr) not in file_dict:
                raise ValueError(
                    f"The file '{schedulable_object.stdout.path_attr}' for stdout does not match a recognized File object"
                )
            in_progress_config_object["stdout"] = str(
                schedulable_object.stdout.path_attr
            )
        else:
            in_progress_config_object["stdout"] = str(schedulable_object.stdout)
    if schedulable_object.stderr is not None:
        if isinstance(schedulable_object.stderr, File):
            if str(schedulable_object.stderr.path_attr) not in file_dict:
                raise ValueError(
                    f"The file '{schedulable_object.stderr.path_attr}' for stderr does not match a recognized File object"
                )
            in_progress_config_object["stderr"] = str(
                schedulable_object.stderr.path_attr
            )
        else:
            in_progress_config_object["stderr"] = str(schedulable_object.stderr)
    _build_annotatable(in_progress_config_object, schedulable_object)


def _build_commands_object(
    cmds: List[Command],
    site_dict: Dict[str, Dict[str, Any]],
    file_dict: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    command_list = []
    for command in cmds:
        command_obj = {
            "cmd": command.command_or_exe
            if not isinstance(command.command_or_exe, File)
            else str(command.command_or_exe.path_attr),
            "args": [],
        }
        if command.description is not None:
            command_obj["description"] = command.description
        for cmd_arg in command.args:
            if isinstance(cmd_arg, File):
                if str(cmd_arg.path_attr) not in file_dict:
                    raise ValueError(
                        f"The file '{cmd_arg.path_attr}' in args does not match a recognized File object"
                    )
                command_obj["args"].append(
                    {"type": "file", "val": str(cmd_arg.path_attr)}
                )
            elif isinstance(cmd_arg, Directory):
                arg_dir_dict = {
                    "directory": cmd_arg.identifier,
                }
                if cmd_arg.site is not None:
                    arg_dir_dict["site"] = cmd_arg.site.name
                else:
                    arg_dir_dict["site"] = None
                _validate_site_and_directory(arg_dir_dict, site_dict, "args")
                command_obj["args"].append({"type": "directory", "val": arg_dir_dict})
            else:
                command_obj["args"].append(cmd_arg)
        if len(command_obj["args"]) == 0:
            del command_obj["args"]
        _build_schedulable(command_obj, command, site_dict, file_dict)
        command_list.append(command_obj)
    return command_list


def _build_tasks_object(
    tasks: List[Task],
    task_dependencies: Dict[str, List[str]],
    site_dict: Dict[str, Dict[str, Any]],
    file_dict: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    task_list = []
    for task in tasks:
        task_obj = {
            "name": task.task_name,
            "commands": _build_commands_object(task.commands, site_dict, file_dict),
            "inputs": [],
            "outputs": [],
            "input_extra_kwargs": task.add_input_extra_kwargs.copy(),
            "output_extra_kwargs": task.add_output_extra_kwargs.copy(),
        }
        if task.description is None and task.description != "":
            task_obj["description"] = task.description
        if task.site is not None:
            if task.site.name not in site_dict:
                raise ValueError(
                    f"The site '{task.site.name}' specified for task '{task.task_name}', but that site is not recognized in the workflow"
                )
            task_obj["site"] = task.site.name
        for input_file in task.inputs:
            if str(input_file.path_attr) not in file_dict:
                raise ValueError(
                    f"The file '{input_file.path_attr}' is an input for task '{task.task_name}', but that file is not recognized in the workflow"
                )
            task_obj["inputs"].append(str(input_file.path_attr))
        for output_file in task.outputs:
            if str(output_file.path_attr) not in file_dict:
                raise ValueError(
                    f"The file '{output_file.path_attr}' is an output for task '{task.task_name}', but that file is not recognized in the workflow"
                )
            task_obj["outputs"].append(str(output_file.path_attr))
        if len(task_obj["inputs"]) == 0:
            del task_obj["inputs"]
        if len(task_obj["input_extra_kwargs"]) == 0:
            del task_obj["input_extra_kwargs"]
        if len(task_obj["outputs"]) == 0:
            del task_obj["outputs"]
        if len(task_obj["output_extra_kwargs"]) == 0:
            del task_obj["output_extra_kwargs"]
        if task.task_name in task_dependencies:
            task_obj["dependencies"] = task_dependencies[task.task_name]
        if (
            not isinstance(task_obj["dependencies"], (list, tuple))
            or len(task_obj["dependencies"]) == 0
        ):
            del task_obj["dependencies"]
        _build_schedulable(task_obj, task, site_dict, file_dict)
        task_list.append(task_obj)
    return task_list


def _search_for_sites_and_files_from_tasks(
    sites: Set[Site], tasks: List[Task]
) -> Tuple[Set[Site], Set[File]]:
    files = set()
    for task in tasks:
        if task.site is not None:
            sites.add(task.site)
        for input_file in task.inputs:
            files.add(input_file)
            if (
                input_file.directory is not None
                and input_file.directory.site is not None
            ):
                sites.add(input_file.directory.site)
        for output_file in task.outputs:
            files.add(output_file)
            if (
                output_file.directory is not None
                and output_file.directory.site is not None
            ):
                sites.add(output_file.directory.site)
        for cmd in task.commands:
            if isinstance(cmd.command_or_exe, File):
                files.add(cmd.command_or_exe)
                if (
                    cmd.command_or_exe.directory is not None
                    and cmd.command_or_exe.directory.site is not None
                ):
                    sites.add(cmd.command_or_exe.directory.site)
            for arg in cmd.args:
                if isinstance(arg, File):
                    files.add(arg)
                    if arg.directory is not None and arg.directory.site is not None:
                        sites.add(arg.directory.site)
                elif isinstance(arg, Directory):
                    if arg.site is not None:
                        sites.add(arg.site)
    for site in sites:
        for directory in site.values():
            files = files | directory.files
    return sites, files


def write_config(fname: StrCompatPathLike, wflow: Workflow):
    wflow_obj = {
        "name": wflow.name,
        "description": wflow.description if wflow.description is not None else "",
    }
    if len(wflow.environment) > 0:
        wflow_obj["environment"] = wflow.environment.copy()
    tasks = wflow.get_tasks_in_topological_order()
    if len(tasks) == 0:
        raise RuntimeError("Cannot convert a workflow with no tasks into a config")
    task_dependencies = {
        t.task_name: list(wflow.graph.predecessors(t.task_name)) for t in tasks
    }
    sites = wflow.sites
    sites, files = _search_for_sites_and_files_from_tasks(sites, tasks)
    wflow_obj["sites"] = _build_sites_object(sites)
    site_dict = {sc["name"]: sc.copy() for sc in wflow_obj["sites"]}
    wflow_obj["files"] = _build_files_object(files, site_dict)
    file_dict = {fc["name"]: fc.copy() for fc in wflow_obj["files"]}
    wflow_obj["tasks"] = _build_tasks_object(
        tasks, task_dependencies, site_dict, file_dict
    )
    if len(wflow_obj["sites"]) == 0:
        del wflow_obj["sites"]
    else:
        wflow_obj["sites"] = list(
            sorted(wflow_obj["sites"], key=lambda site: site["name"])
        )
    if len(wflow_obj["files"]) == 0:
        del wflow_obj["files"]
    else:
        wflow_obj["files"] = list(
            sorted(wflow_obj["files"], key=lambda file: file["name"])
        )
    if len(wflow_obj["tasks"]) == 0:
        raise RuntimeError(
            "INTERNAL ERROR: tasks exist in workflow, but they did not get serialized into the config"
        )
    _build_annotatable(wflow_obj, wflow)
    full_config = {"workflow": wflow_obj}
    validate_config_contents(full_config)
    yaml = YAML()
    with open(fname, "w") as f:
        yaml.dump(full_config, f)
