# Copyright 2025 Global Computing Lab.
# See top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import List

import networkx as nx
from a4x.orchestration.annotations import AnnotationType
from a4x.orchestration.site import Site
from a4x.orchestration.task import Task
from a4x.orchestration.utils import StrCompatPathLike


class Workflow(AnnotationType):
    def __init__(self, name: str, description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.graph = nx.DiGraph()
        self.task_inputs = set()
        self.task_outputs = set()
        self.sites = set()
        self.global_environ = {}

    def add_site(self, site: Site):
        if not isinstance(site, Site):
            raise TypeError("Sites must be of type 'a4x.orchestration.Site'")
        if site not in self.sites:
            self.sites.add(site)

    def add_sites(self, *sites):
        for s in sites:
            self.add_site(s)

    def add_task(self, task: Task):
        if not isinstance(task, Task):
            raise TypeError("Tasks provided to 'add_task' must be of type 'Task'")
        self.task_inputs.update(task.inputs)
        self.task_outputs.update(task.outputs)
        self.graph.add_node(task.task_name, task=task)
        if task.site is not None:
            self.add_site(task.site)

    def add_tasks(self, *tasks):
        for t in tasks:
            self.add_task(t)

    def add_edge(self, src_task: Task, dest_task: Task):
        if src_task.task_name not in self.graph:
            self.add_task(src_task)
        if dest_task.task_name not in self.graph:
            self.add_task(dest_task)
        self.graph.add_edge(src_task.task_name, dest_task.task_name)

    def add_dependency(self, task: Task, parents: List[Task], children: List[Task]):
        if not isinstance(task, Task):
            raise TypeError("Tasks provided to 'add_dependency' must be of type 'Task'")
        if task.task_name not in self.graph:
            self.add_task(task)
        for p in parents:
            if not isinstance(p, Task):
                raise TypeError(
                    "Tasks provided to 'add_dependency' must be of type 'Task'"
                )
            if p.task_name not in self.graph:
                self.add_task(p)
            self.add_edge(p, task)
        for c in children:
            if not isinstance(c, Task):
                raise TypeError(
                    "Tasks provided to 'add_dependency' must be of type 'Task'"
                )
            if c.task_name not in self.graph:
                self.add_task(c)
            self.add_edge(task, c)

    def generate_dependencies_from_task_inputs_outputs(self, override=True):
        if not override and self.num_edges != 0:
            raise RuntimeError(
                "Cannot generate task dependencies when dependencies already exist and 'override' is False"
            )
        elif override and self.num_edges != 0:
            self.graph.clear_edges()
        input_taskmap = {}
        for _, task in self.graph.nodes(data="task"):  # type: ignore
            for inp in task.inputs:
                if inp in input_taskmap.keys():
                    input_taskmap[inp].append(task)
                else:
                    input_taskmap[inp] = [task]
        for _, task in self.graph.nodes(data="task"):  # type: ignore
            for outp in task.outputs:
                if outp in input_taskmap.keys():
                    for child_task in input_taskmap[outp]:
                        self.add_edge(task, child_task)

    def get_task_by_name(self, name: str) -> Task:
        return dict(self.graph.nodes(data="task"))[name]

    def get_tasks_in_topological_order(self) -> List[Task]:
        return [
            self.graph.nodes[tn]["task"]
            for tn in nx.lexicographical_topological_sort(self.graph)
        ]

    def convert(self, plugin_key: str, ignore_builtin_plugins: bool = False, **kwargs):
        from a4x.orchestration import convert_to_plugin

        return convert_to_plugin(self, plugin_key, ignore_builtin_plugins, **kwargs)

    def resolve(self):
        for _, task in self.graph.nodes(data="task"):
            task._resolve_site()
            if task.site is not None:
                self.sites.add(task.site)
        for site in self.sites:
            site.resolve_site_files()

    @property
    def num_nodes(self) -> int:
        return self.graph.number_of_nodes()

    @property
    def num_edges(self) -> int:
        return self.graph.number_of_edges()

    def __len__(self) -> int:
        return self.num_nodes

    @property
    def task_inputs_from_graph(self):
        return {
            node_tup[0]: node_tup[1].inputs
            for node_tup in self.graph.nodes(data="task")  # type: ignore
        }

    @property
    def task_outputs_from_graph(self):
        return {
            node_tup[0]: node_tup[1].outputs
            for node_tup in self.graph.nodes(data="task")  # type: ignore
        }

    @property
    def root_tasks(self):
        root_task_names = [
            deg_tup[0] for deg_tup in self.graph.in_degree() if deg_tup[1] == 0
        ]
        return [self.graph.nodes[name]["task"] for name in root_task_names]

    @property
    def leaf_tasks(self):
        root_task_names = [
            deg_tup[0] for deg_tup in self.graph.out_degree() if deg_tup[1] == 0
        ]
        return [self.graph.nodes[name]["task"] for name in root_task_names]

    @property
    def environment(self):
        return self.global_environ

    @environment.setter
    def environment(self, environ):
        if not isinstance(environ, Mapping):
            raise TypeError("The 'environment' property must be a mapping type")
        self.global_environ = environ

    def __repr__(self):
        return f"Workflow({self.name})"

    def to_config(self, fpath: os.PathLike):
        from a4x.orchestration.config.writer import write_config

        write_config(fpath, self)

    @staticmethod
    def from_config(fpath: StrCompatPathLike) -> Workflow:
        from a4x.orchestration.config.reader import read_config

        return read_config(fpath)


def print_workflow_info(wflow: Workflow):
    print("Workflow:", wflow.name)
    print("Description:", wflow.description)
    print()

    wflow_tasks = wflow.get_tasks_in_topological_order()
    wflow_deps = {
        t.task_name: list(wflow.graph.successors(t.task_name)) for t in wflow_tasks
    }

    print("Tasks:")
    print("======")
    for task in wflow_tasks:
        print("  - Name:", task.task_name)
        print(
            "    Site:",
            task.site if task.site is not None else None,
        )
        print("    Inputs:")
        for inp in task.inputs:
            print("    * Path/Name:", inp)
            print("      Directory:", inp.directory)
            if inp.directory is not None:
                print("      Storage Type:", inp.directory.storage_type)
                print("      Persistency:", inp.directory.persistency)
                if inp.directory.site is not None:
                    print("      Site:", inp.directory.site.name)
                    print("      Scheduler:", inp.directory.site.scheduler)
        print("    Outputs:")
        for inp in task.outputs:
            print("    * Path/Name:", inp.path_attr)
            print("      Directory:", str(inp.directory))
            if inp.directory is not None:
                print("      Storage Type:", inp.directory.storage_type)
                print("      Persistency:", inp.directory.persistency)
                if inp.directory.site is not None:
                    print("      Site:", inp.directory.site.name)
                    print("      Scheduler:", inp.directory.site.scheduler)
        print("    Commands:")
        for cmd in task.commands:
            print("    * Command:", cmd.command_or_exe)
            print("      Args:", cmd.args)
    print()

    print("Task Dependencies:")
    print("==================")
    for parent, children in wflow_deps.items():
        print(f"  - {parent} -> {children}")
