from typing import Any, Dict, List, Tuple

from a4x.orchestration.annotations import AnnotationType
from a4x.orchestration.command import Command
from a4x.orchestration.config.validation import validate_config_contents
from a4x.orchestration.file import File
from a4x.orchestration.resources import Resources, SchedulableWork, Slot
from a4x.orchestration.site import (
    PersistencyType,
    Scheduler,
    Site,
    StorageType,
)
from a4x.orchestration.task import Task
from a4x.orchestration.utils import StrCompatPathLike, StrCompatPathLikeForIsInstance
from a4x.orchestration.workflow import Workflow
from ruamel.yaml import YAML


def _build_annotatable(
    annotatable_object: AnnotationType, annotatable_config: Dict[str, Any]
):
    if "annotations" in annotatable_config:
        annotatable_object.annotations = annotatable_config["annotations"].copy()


def _build_sites_and_directories(
    site_list: List[Dict[str, Any]],
) -> Dict[str, Site]:
    sites = {}
    for site_config in site_list:
        sched = Scheduler.UNKNOWN
        if "scheduler" in site_config and site_config["scheduler"] is not None:
            sched = site_config["scheduler"]
        curr_site = Site(site_config["name"], sched)
        if "directories" in site_config:
            for dir_config in site_config["directories"]:
                storage_type = StorageType.UNKNOWN
                if "storage_type" in dir_config:
                    storage_type = dir_config["storage_type"]
                persistency = PersistencyType.UNKNOWN
                if "persistency" in dir_config:
                    persistency = dir_config["persistency"]
                curr_site.add_directory(
                    dir_config["name"],
                    dir_config["path"],
                    storage_type,
                    persistency,
                )
        _build_annotatable(curr_site, site_config)
        sites[curr_site.name] = curr_site
    return sites


def _build_files(
    file_list: List[Dict[str, Any]], sites: Dict[str, Site]
) -> Dict[str, File]:
    files = {}
    for file_config in file_list:
        site = None
        if "site" in file_config and file_config["site"] is not None:
            if file_config["site"] in sites:
                site = sites[file_config["site"]]
            else:
                raise KeyError(
                    "In the 'files' section of the config, 'site' must match a Site 'name' field in the 'sites' section of the config"
                )
        directory = None
        if "directory" in file_config and file_config["directory"] is not None:
            if site is not None:
                try:
                    directory = site[file_config["directory"]]
                except KeyError:
                    raise KeyError(
                        "In the 'files' section of the config, 'directory' must match a Directory 'name' field in the 'sites' section of the config"
                    )
            else:
                raise KeyError(
                    "In the 'files' section of the config, 'directory' can only be used if 'site' is used"
                )
        files[file_config["name"]] = File(file_config["name"], directory)
    return files


def _build_schedulable(
    schedulable_object: SchedulableWork,
    schedulable_config: Dict[str, Any],
    sites: Dict[str, Site],
    files: Dict[str, File],
):
    if "duration" in schedulable_config:
        schedulable_object.duration = schedulable_config["duration"]
    if "queue" in schedulable_config:
        schedulable_object.queue = schedulable_config["queue"]
    if "cwd" in schedulable_config:
        cwd = schedulable_config["cwd"]
        if not isinstance(cwd, str):
            try:
                site = sites[schedulable_config["cwd"]["site"]]
            except KeyError:
                raise KeyError(
                    "In the 'cwd' field, 'site' must match a Site 'name' field in the 'sites' section of the config"
                )
            if site is not None:
                try:
                    cwd = site[schedulable_config["cwd"]["directory"]]
                except KeyError:
                    raise KeyError(
                        "In the 'cwd' field, 'directory' must match a Directory 'name' field in the 'sites' section of the config"
                    )
            else:
                raise KeyError(
                    "INTERNAL ERROR: In the 'cwd' field, 'directory' can only be used if 'site' is used. This shouldn't happen unless something's wrong with jsonschema"
                )
        schedulable_object.cwd = cwd
    if "environment" in schedulable_config:
        schedulable_object.environment = schedulable_config["environment"].copy()
    if "stdin" in schedulable_config:
        if schedulable_config["stdin"] in files:
            schedulable_object.stdin = files[schedulable_config["stdin"]]
        else:
            schedulable_object.stdin = schedulable_config["stdin"]
    if "stdout" in schedulable_config:
        if schedulable_config["stdout"] in files:
            schedulable_object.stdout = files[schedulable_config["stdout"]]
        else:
            schedulable_object.stdout = schedulable_config["stdout"]
    if "stderr" in schedulable_config:
        if schedulable_config["stderr"] in files:
            schedulable_object.stderr = files[schedulable_config["stderr"]]
        else:
            schedulable_object.stderr = schedulable_config["stderr"]
    if "resources" in schedulable_config and "resources_w_slot" in schedulable_config:
        raise KeyError(
            "An A4X-Orchestration config cannot have both 'resources' and 'resources_w_slot' in a schedulable entry"
        )
    if "resources" in schedulable_config:
        resource_args = schedulable_config["resources"].copy()
        if "exclusive" in resource_args:
            resource_args["allocate_nodes_exclusively"] = resource_args["exclusive"]
            del resource_args["exclusive"]
        schedulable_object.set_resources(**resource_args)
    if "resources_w_slot" in schedulable_config:
        slot = Slot(**schedulable_config["resources_w_slot"]["slot"])
        resource_args = {
            "num_procs": schedulable_config["resources_w_slot"]["num_procs"],
            "per_proc_resources": slot,
        }
        if (
            "num_nodes" in schedulable_config["resources_w_slot"]
            and schedulable_config["resources_w_slot"]["num_nodes"] is not None
        ):
            resource_args["num_nodes"] = schedulable_config["resources_w_slot"][
                "num_nodes"
            ]
        if "exclusive" in schedulable_config["resources_w_slot"]:
            resource_args["exclusive"] = schedulable_config["resources_w_slot"][
                "exclusive"
            ]
        schedulable_object.jobspec_settings.resources = Resources(**resource_args)
    _build_annotatable(schedulable_object, schedulable_config)


def _build_commands(
    command_list: List[Dict[str, Any]], sites: Dict[str, Site], files: Dict[str, File]
) -> List[Command]:
    commands = []
    for command_config in command_list:
        args = []
        if "args" in command_config:
            for arg in command_config["args"]:
                if not isinstance(arg, dict):
                    args.append(arg)
                elif arg["type"] == "file":
                    if not isinstance(arg["val"], str):
                        raise TypeError(
                            "INTERNAL ERROR: When representing a file in the 'commands' block, the 'val' key must have a string value. This should only occur if jsonschema fails"
                        )
                    try:
                        args.append(files[arg["val"]])
                    except KeyError:
                        raise KeyError(
                            f"No file named {arg['val']} recognized. Files must be specified in the 'files' block"
                        )
                else:
                    if not isinstance(arg["val"], dict):
                        raise TypeError(
                            "INTERNAL ERROR: When representing a directory in the 'commands' block, the 'val' key must be an object with 'site' and 'directory' keys. This should only occur if jsonschema fails"
                        )
                    try:
                        site = sites[arg["val"]["site"]]
                    except KeyError:
                        raise KeyError(
                            f"No site named {arg['val']['site']} recognized. Sites and directories must be specified in the 'sites' block"
                        )
                    try:
                        args.append(site[arg["val"]["directory"]])
                    except KeyError:
                        raise KeyError(
                            f"No directory named {arg['val']['directory']} recognized for site {arg['val']['site']}. Sites and directories must be specified in the 'sites' block"
                        )
        cmd = (
            files[command_config["cmd"]]
            if command_config["cmd"] in files
            else command_config["cmd"]
        )
        curr_command = Command(cmd, *args)
        if "description" in command_config:
            curr_command.description = command_config["description"]
        _build_schedulable(curr_command, command_config, sites, files)
        commands.append(curr_command)
    return commands


def _validate_task_dependencies(
    tasks: Dict[str, Task], task_dependencies: Dict[str, List[str]]
):
    unrecognized_task_names = []
    for task_name, children_tasks in task_dependencies.items():
        if task_name not in tasks:
            unrecognized_task_names.append(task_name)
        for child_name in children_tasks:
            if child_name not in tasks:
                unrecognized_task_names.append(child_name)
    if len(unrecognized_task_names) > 0:
        unrecognized_task_names = [
            "  - {}".format(tn) for tn in unrecognized_task_names
        ]
        raise ValueError(
            "The following task names were used to define dependencies, but they do not exist in the 'tasks' block:\n"
            + "\n".join[unrecognized_task_names]
        )


def _build_tasks(
    task_list: List[Dict[str, Any]], sites: Dict[str, Site], files: Dict[str, File]
) -> Tuple[Dict[str, Task], Dict[str, List[str]]]:
    tasks = {}
    task_dependencies = {}
    for task_config in task_list:
        curr_task = Task(
            name=task_config["name"],
            description=task_config["description"]
            if "description" in task_config
            else "",
        )
        curr_task.extend(_build_commands(task_config["commands"], sites, files))
        _build_schedulable(curr_task, task_config, sites, files)
        if "site" in task_config and task_config["site"] is not None:
            try:
                site = sites[task_config["site"]]
            except KeyError:
                raise KeyError(
                    f"No site named {task_config['site']} recognized. Sites must be specified in the 'sites' block"
                )
            curr_task.set_site(site)
        if "inputs" in task_config:
            task_inputs = []
            for input_file in task_config["inputs"]:
                try:
                    task_inputs.append(files[input_file])
                except KeyError:
                    raise KeyError(
                        f"No file named {input_file} recognized. Files must be specified in the 'files' block"
                    )
            input_extra_kwargs = {}
            if "input_extra_kwargs" in task_config:
                input_extra_kwargs = task_config["input_extra_kwargs"]
            curr_task.add_inputs(*task_inputs, **input_extra_kwargs)
        if "outputs" in task_config:
            task_outputs = []
            for output_file in task_config["outputs"]:
                try:
                    task_outputs.append(files[output_file])
                except KeyError:
                    raise KeyError(
                        f"No file named {output_file} recognized. Files must be specified in the 'files' block"
                    )
            output_extra_kwargs = {}
            if "output_extra_kwargs" in task_config:
                output_extra_kwargs = task_config["output_extra_kwargs"]
            curr_task.add_outputs(*task_outputs, **output_extra_kwargs)
        task_dependencies[curr_task.task_name] = (
            task_config["dependencies"].copy() if "dependencies" in task_config else []
        )
        tasks[curr_task.task_name] = curr_task
    _validate_task_dependencies(tasks, task_dependencies)
    return tasks, task_dependencies


def read_config(fname: StrCompatPathLike) -> Workflow:
    if not isinstance(fname, StrCompatPathLikeForIsInstance):
        raise TypeError(
            "The 'fname' argument must be a string or a type compliant with os.PathLike"
        )
    config = None
    yaml = YAML()
    with open(fname, "r") as f:
        config = yaml.load(f)
    if config is None:
        raise RuntimeError(f"Cannot load YAML config from {fname}")
    validate_config_contents(config)
    wflow_config = config["workflow"]
    sites = {}
    if "sites" in wflow_config:
        sites = _build_sites_and_directories(wflow_config["sites"])
    files = {}
    if "files" in wflow_config:
        files = _build_files(wflow_config["files"], sites)
    tasks, task_dependencies = _build_tasks(wflow_config["tasks"], sites, files)
    wflow = Workflow(
        name=wflow_config["name"],
        description=wflow_config["description"]
        if "description" in wflow_config
        else "",
    )
    _build_annotatable(wflow, wflow_config)
    wflow.add_tasks(*list(tasks.values()))
    for child, parents in task_dependencies.items():
        for parent in parents:
            wflow.add_edge(tasks[parent], tasks[child])
    wflow.add_sites(*list(sites.values()))
    if "environment" in wflow_config:
        wflow.environment = wflow_config["environment"].copy()
    return wflow
