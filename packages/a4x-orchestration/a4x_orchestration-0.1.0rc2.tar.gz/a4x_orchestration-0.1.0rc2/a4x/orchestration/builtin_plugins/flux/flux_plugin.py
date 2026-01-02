# Copyright 2025 Global Computing Lab.
# See top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception

import os
import subprocess
from pathlib import Path
from typing import Any, Dict, Tuple

from a4x.orchestration.file import File
from a4x.orchestration.plugin import Plugin
from a4x.orchestration.site import Directory, Scheduler
from a4x.orchestration.task import Task
from a4x.orchestration.workflow import Workflow
from jinja2 import Environment, FileSystemLoader


class FluxPlugin(Plugin):
    def __init__(self, wflow: Workflow):
        super().__init__("flux", wflow)
        self._validate_sites()
        template_dir = (Path(__file__).parent / "templates").expanduser().resolve()
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            lstrip_blocks=True,
            trim_blocks=True,
        )
        self.task_script_template = self.jinja_env.get_template("task_script.sh.in")
        self.batch_script_py_template = self.jinja_env.get_template(
            "batch_script.py.in"
        )
        self.batch_script_sh_template = self.jinja_env.get_template(
            "batch_script.sh.in"
        )
        self.out_dir = None
        self.use_shell_launcher = None
        if self.plugin_settings is not None:
            self.out_dir = self.plugin_settings["out_dir"]
            self.use_shell_launcher = self.plugin_settings["launcher_uses_shell"]

    def execute(
        self,
        alternate_shell: str = None,
        alternate_python_interpreter: str = None,
        dry_run: bool = False,
    ):
        if self.out_dir is None or self.use_shell_launcher is None:
            raise RuntimeError(
                "Cannot execute a workflow with Flux because the Flux plugin does not know where the generated scripts are"
            )
        launcher_command = []
        if self.use_shell_launcher:
            if alternate_shell is not None:
                launcher_command.append(alternate_shell)
            launcher_command.append(str(Path(self.out_dir) / "launch.sh"))
        else:
            if alternate_python_interpreter is not None:
                launcher_command.append(alternate_python_interpreter)
            launcher_command.append(str(Path(self.out_dir) / "launch.py"))
        print("Launching workflow:")
        if dry_run:
            print("Dry run enabled. Would have run the following command:")
            print(
                " ".join(launcher_command),
            )
        else:
            print(
                subprocess.run(
                    launcher_command,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                ).stdout
            )

    def create_plugin_settings_for_a4x_config(self) -> Dict[str, Any]:
        return {
            "out_dir": str(self.out_dir),
            "launcher_uses_shell": self.use_shell_launcher,
        }

    def configure_plugin(
        self, script_out_dir: os.PathLike, use_shell_launcher=True, exist_ok=False
    ):
        self.use_shell_launcher = use_shell_launcher
        self.out_dir = Path(script_out_dir).expanduser().resolve()
        self.out_dir.mkdir(parents=True, exist_ok=exist_ok)
        shell_path = str(self.a4x_wflow.annotations.get("shell", "/usr/bin/env bash"))
        out_file_map = {}
        for task_tuple in self.a4x_wflow.graph.nodes(data="task"):
            _, task = task_tuple
            task_name, out_file, out_file_contents = self._generate_task_script(
                self.out_dir, task, shell_path
            )
            out_file_map[task_name] = out_file
            self._write_flux_file(out_file, out_file_contents)
        submit_script_path, submit_script_contents = self._generate_batch_submit_script(
            self.out_dir, out_file_map, self.use_shell_launcher, shell_path
        )
        self._write_flux_file(submit_script_path, submit_script_contents)

    def _write_flux_file(self, out_file: Path, contents: str):
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(contents)

    def _validate_sites(self):
        for site in self.a4x_wflow.sites:
            if site.scheduler != Scheduler.FLUX:
                raise ValueError(
                    f"The workflow ('{self.a4x_wflow.name}') has a site ('{site.name}') with a non-Flux scheduler ('{site.scheduler}')."
                )
        for _, task in self.a4x_wflow.graph.nodes(data="task"):
            if task.site is not None and task.site.scheduler != Scheduler.FLUX:
                raise ValueError(
                    f"INTERNAL ERROR: a task has a site ('{task.site.name}') with a non-Flux scheduler ('{task.site.scheduler}'), but the site is not in the workflow."
                )

    def _resolve_files_for_task(self, task: Task):
        for fi in task.inputs:
            if not fi.is_resolved:
                fi.resolve()
        for fo in task.outputs:
            if not fo.is_resolved:
                fo.resolve()
        for cmd in task.commands:
            for fa in cmd.args:
                if isinstance(fa, File) and fa.is_resolved:
                    fa.resolve()
            if isinstance(cmd.command_or_exe, File):
                cmd.command_or_exe.resolve()
        if isinstance(task.stdin, File):
            task.stdin.resolve()
        if isinstance(task.stdout, File):
            task.stdout.resolve()
        if isinstance(task.stderr, File):
            task.stderr.resolve()

    def _generate_task_script(
        self, script_out_dir: Path, task: Task, shell_path: str
    ) -> Tuple[str, Path, str]:
        self._resolve_files_for_task(task)
        out_file = script_out_dir / f"{task.task_name}_script.sh"
        config = {"shell": shell_path, "commands": []}
        for cmd in task.commands:
            cmd_object = {"command": "", "description": cmd.description}
            if cmd.is_block_command:
                cmd_object["command"] = cmd.command_or_exe
            else:
                single_cmd_components = cmd.generate_parallel_launch(Scheduler.FLUX)
                single_cmd_components.append(
                    cmd.command_or_exe
                    if isinstance(cmd.command_or_exe, str)
                    else str(cmd.command_or_exe.path)
                )
                single_cmd_components.extend(
                    [str(a.path) if isinstance(a, File) else a for a in cmd.args]
                )
                cmd_object["command"] = " ".join(
                    [str(c) for c in single_cmd_components]
                )
            config["commands"].append(cmd_object)
        rendered_script = self.task_script_template.render(config)
        return (task.task_name, out_file, rendered_script)

    def _generate_batch_submit_script(
        self,
        script_out_dir: Path,
        out_file_map: Dict[str, Path],
        use_shell_launcher: bool,
        shell_path: str,
    ):
        config = {
            "tasks": [],
            "task_submit_info": [],
        }
        for task in self.a4x_wflow.get_tasks_in_topological_order():
            resources = task.get_resources()
            if resources is None:
                num_slots = 1
                num_cores = None
                num_gpus = None
                num_nodes = None
                exclusive = False
            else:
                try:
                    num_slots = resources.num_slots_per_node * resources.num_nodes
                except Exception:
                    raise ValueError(
                        "Number of nodes and slots are required to use the Flux plugin"
                    )
                num_cores = resources.resources_per_slot.cores
                num_gpus = resources.resources_per_slot.gpus
                num_nodes = resources.num_nodes
                exclusive = resources.exclusive
            duration = None
            cwd = None
            task_output = None
            task_error = None
            if task.duration is not None:
                duration = (
                    task.duration
                    if isinstance(task.duration, int)
                    else f'"{task.duration}"'
                )
            environment = (
                task.environment
                if isinstance(task.environment, dict) and len(task.environment) > 0
                else None
            )
            if task.cwd is not None:
                if isinstance(task.cwd, Directory):
                    cwd = task.cwd.path.expanduser().resolve()
                else:
                    cwd = task.cwd.expanduser().resolve()
            if task.stdout is not None:
                if isinstance(task.stdout, File):
                    task_output = str(task.stdout.path)
                else:
                    task_output = str(task.stdout.expanduser().resolve())
            if task.stderr is not None:
                if isinstance(task.std, File):
                    task_error = str(task.stderr.path)
                else:
                    task_error = str(task.stderr.expanduser().resolve())
            queue = task.queue
            bank = None  # TODO add support for banks in 'Task'
            task_config = {
                "script": str(out_file_map[task.task_name]),
                "num_slots": num_slots,
                "task_name": task.task_name,
                "num_cores": num_cores,
                "num_gpus": num_gpus,
                "num_nodes": num_nodes,
                "exclusive": exclusive,
                "duration": duration,
                "environment": environment,
                "cwd": cwd,
                "output": task_output,
                "error": task_error,
                "queue": queue,
                "bank": bank,
            }
            task_info = {
                "task_name": task.task_name,
                "dependencies": list(self.a4x_wflow.graph.predecessors(task.task_name)),
            }
            config["tasks"].append(task_config)
            config["task_submit_info"].append(task_info)
        script_out_path = script_out_dir
        rendered_script = None
        if use_shell_launcher:
            config["shell"] = shell_path
            script_out_path = script_out_path / "launch.sh"
            rendered_script = self.batch_script_sh_template.render(config)
        else:
            script_out_path = script_out_path / "launch.py"
            rendered_script = self.batch_script_py_template.render(config)
        return script_out_path, rendered_script
