# Copyright 2025 Global Computing Lab.
# See top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception

from __future__ import annotations

from collections.abc import MutableSequence
from typing import List, Union

from a4x.orchestration.command import Command
from a4x.orchestration.file import File
from a4x.orchestration.resources import SchedulableWork
from a4x.orchestration.site import Site, get_default_site


class Task(SchedulableWork, MutableSequence):
    """
    A class representing a single Task in the workflow.

    This class behaves like a Python :code:`list` containing :code:`Command`
    objects. When adding commands into a :code:`Task`, users can add either
    strings or :code:`Command` objects. When provided strings, the :code:`Task`
    class will implicitly convert the strings into :code:`Command` objects with
    no scheduling settings.

    This class also supports all the same properties and methods for
    scheduling settings as :code:`Command`. Regarding scheduling, users
    can think of the :code:`Command` class as representing parallel launches
    (with e.g., 'mpiexec', 'srun', 'flux run'), while the :code:`Task` class
    represents batch submissions (with e.g., 'sbatch', 'flux batch').
    """

    def __init__(self, name: str, description=""):
        """
        Create a Task.

        :param name: the name (i.e., unique identifier) of the Task
        :type name: str
        :param description: a description of the Task
        :type name: Optional[str]
        """
        super().__init__()
        self.task_name = name
        self.description = description
        self.commands = []
        self.inputs = []
        self.outputs = []
        self.site = None
        self.add_input_extra_kwargs = {}
        self.add_output_extra_kwargs = {}

    def set_site(self, site: Site):
        """
        Sets the site for this task.

        :param site: the site
        :type site: a4x.orchestration.Site
        """
        if not isinstance(site, Site):
            raise TypeError("The site for a Task must be of type 'Site'")
        self.site = site

    def __getitem__(self, idx):
        """
        Get a command from the Task

        :param idx: the index into the list of :code:`Command` objects
        :type idx: Union[int, slice]
        :return: one or more requested :code:`Command` object(s)
        :rtype: Command
        :raises IndexError: if the index in out-of-bounds
        """
        return self.commands[idx]

    def __setitem__(self, idx, val: Union[str, Command]):
        """
        Set a command in the Task

        :param idx: the index into the list of :code:`Command` objects
        :type idx: Union[int, slice]
        :param val: the command to add
        :type val: Union[str, Command]
        :raises TypeError: if :code:`val` is not a string or :code:`Command`
        :raises IndexError: if the index in out-of-bounds
        """
        if not isinstance(val, (str, Command)):
            raise TypeError(
                "Tasks can only store Commands or strings (which get implicitly converted into Commands)"
            )
        cmd = val
        if isinstance(val, str):
            cmd = Command(val)
        self.commands[idx] = cmd

    def __delitem__(self, idx):
        """
        Remove a command from the Task by index

        :param idx: the index into the list of :code:`Command` objects
        :type idx: Union[int, slice]
        :raises IndexError: if the index in out-of-bounds
        """
        del self.commands[idx]

    def __len__(self) -> int:
        """
        Get the number of commands in the Task

        :return: the number of commands in the Task
        :rtype: int
        """
        return len(self.commands)

    def insert(self, idx, val: Union[str, Command]):
        """
        Insert a command at a specific index in the Task's command list

        :param idx: the index into the list of :code:`Command` objects
        :type idx: Union[int, slice]
        :param val: the command to add
        :type val: Union[str, Command]
        :raises TypeError: if :code:`val` is not a string or :code:`Command`
        """
        if not isinstance(val, (str, Command)):
            raise TypeError(
                "Tasks can only store Commands or strings (which get implicitly converted into Commands)"
            )
        cmd = val
        if isinstance(val, str):
            cmd = Command(val)
        self.commands.insert(idx, cmd)

    def add_inputs(self, *inputs, **extra_kwargs):
        """
        Add one or more inputs to the Task

        :param *inputs: the inputs to add to the Task
        :type *inputs: a4x.orchestration.Path
        :param **extra_kwargs: extra keyword arguments to associate with input addition. WMS plugins can choose to use or not to use these arguments
        :type **extra_kwargs: Any
        """
        self.add_input_extra_kwargs = extra_kwargs
        self.inputs = list(inputs)
        if any([not isinstance(i, File) for i in self.inputs]):
            raise TypeError(
                "All positional arguments to 'add_inputs' should be of type 'a4x.orchestration.File'"
            )
        return self

    def add_outputs(self, *outputs, **extra_kwargs):
        """
        Add one or more outputs to the Task

        :param *outputs: the outputs to add to the Task
        :type *inputs: a4x.orchestration.Path
        :param **extra_kwargs: extra keyword arguments to associate with output addition. WMS plugins can choose to use or not to use these arguments
        :type **extra_kwargs: Any
        """
        self.add_output_extra_kwargs = extra_kwargs
        self.outputs = list(outputs)
        if any([not isinstance(o, File) for o in self.outputs]):
            raise TypeError(
                "All positional arguments to 'add_outputs' should be of type 'a4x.orchestration.File'"
            )
        return self

    def get_inputs(self) -> List[File]:
        """
        Get all inputs to the Task

        :return: all inputs to the Task
        :rtype: List[File]
        """
        return self.inputs

    def get_outputs(self) -> List[File]:
        """
        Get all outputs to the Task

        :return: all outputs to the Task
        :rtype: List[File]
        """
        return self.outputs

    def __hash__(self):
        return hash(self.task_name)

    def __repr__(self):
        return f"Task(name={self.task_name},site={self.site},commands={self.commands})"

    def __eq__(self, other):
        return (
            isinstance(other, Task)
            and self.task_name == other.task_name
            and self.commands == other.commands
            and self.inputs == other.inputs
            and self.outputs == other.outputs
            and (
                (self.site is None and other.site is None)
                or (
                    self.site is not None
                    and other.site is not None
                    and self.site == other.site
                )
            )
        )

    def __lt__(self, other):
        return self.task_name < other.task_name

    def _resolve_site(self):
        default_site = get_default_site()
        if self.site is None:
            file_sites = set()
            for in_file in self.inputs:
                if in_file.site is not None:
                    file_sites.add(in_file.site)
            for out_file in self.outputs:
                if out_file.site is not None:
                    file_sites.add(out_file.site)
            if len(file_sites) > 1:
                raise RuntimeError(
                    f"Task '{self.task_name}' does not have a site set and input/output files are in multiple sites. Either explicitly set the site for this task with 'Task.set_site' or adjust your inputs/outputs"
                )
            elif len(file_sites) == 1:
                self.site = tuple(file_sites)[0]
            else:
                # Else use the default site as the site for this task
                self.site = None
            if self.site is None:
                self.site = default_site
