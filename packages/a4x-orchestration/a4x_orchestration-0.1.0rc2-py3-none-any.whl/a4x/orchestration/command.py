from __future__ import annotations

from typing import List, Optional, Union

from a4x.orchestration.file import File
from a4x.orchestration.resources import SchedulableWork
from a4x.orchestration.site import Scheduler


class Command(SchedulableWork):
    """
    A class representing one or more commands within a single Task,
    optionally with associated scheduling settings.

    When no scheduling settings are present and no args are provided via the constructor,
    it is assumed that the 'command_or_exe' field represents one or more shell commands
    that can be copied verbatim into an eventual configuration file or batch script.

    When no scheduling settings are present and some args are provide via the constructor,
    it is assumed that the combination of the 'command_or_exe' and 'args' fields represents
    a single shell command the is built via 'str.join'.

    When scheduling settings are present, it is assumed that the command represents a parallel
    program to be launched with tools like 'mpiexec', 'srun', or 'flux run'.
    """

    def __init__(self, command_or_exe: Union[str, File], *exe_args):
        """
        Create a Command.

        :param command_or_exe: either a block of shell commands or the name/path for a single executable to be run
        :type command_or_exe: str
        :param *exe_args: arguments to pass to the provided executable when :code:`command_or_exe` represents a single executable
        :type *exe_args: Any (but should be convertable to str)
        """
        super().__init__()
        if not isinstance(command_or_exe, (str, File)):
            raise TypeError(
                "The 'command_or_exe argument must be of type 'str' or 'a4x.orchestration.File'"
            )
        self.command_or_exe = command_or_exe
        if isinstance(command_or_exe, str):
            self.command_or_exe = command_or_exe.strip()
        self.args = list(exe_args).copy()
        self.description_attr = None

    @property
    def description(self) -> Optional[str]:
        """
        A description of the command or command block.
        """
        return self.description_attr

    @description.setter
    def description(self, desc: str):
        self.description_attr = desc

    def __hash__(self):
        return hash(
            (
                self.command_or_exe,
                tuple(self.args),
                self.jobspec_settings,
                frozenset(self.annotations),
            )
        )

    def __eq__(self, other):
        if not isinstance(other, Command):
            return False
        return (
            self.command_or_exe == other.command_or_exe
            and self.args == other.args
            and self.jobspec_settings == other.jobspec_settings
            and self.annotations == other.annotations
        )

    @property
    def is_block_command(self):
        """
        True if the command represents a block of shell commands. False otherwise.
        """
        return (
            isinstance(self.command_or_exe, str)
            and len(self.args) == 0
            and len(list(self.command_or_exe.split())) > 1
        )

    def generate_parallel_launch(self, local_rjms: Scheduler) -> List[str]:
        """
        Generate the parallel launcher command and arguments for the current command and provided RJMS.

        For example, if the RJMS is Flux, this method will return "flux run" and the arguments corresponding
        with this command's resources.

        :param local_rjms: the local resource and job management system (RJMS)
        :type local_rjms: a4x.orchestration.Scheduler
        :return: the parallel launcher command for the current command and provided RJMS
        :rtype: List[str]
        """
        if self.jobspec_settings.resources is None:
            return []
        resources = self.jobspec_settings.resources
        per_task_resources = resources.resources_per_slot
        nodes_not_in_slot = resources.num_nodes is not None and resources.num_nodes > 0
        parallel_launcher = []
        if local_rjms == Scheduler.LSF:
            parallel_launcher.append("jsrun")
            if resources.num_procs > 0:
                parallel_launcher.extend(["--nrs", f"{resources.num_procs}"])
            if per_task_resources is not None:
                if (
                    per_task_resources.cores is not None
                    and per_task_resources.cores > 0
                ):
                    parallel_launcher.extend(
                        ["--cpu_per_rs", f"{per_task_resources.cores}"]
                    )
                if per_task_resources.gpus is not None and per_task_resources.gpus > 0:
                    parallel_launcher.extend(
                        ["--gpu_per_rs", f"{per_task_resources.gpus}"]
                    )
            for env_var, env_val in self.jobspec_settings.environment.items():
                parallel_launcher.extend(["--env", f"{env_var}={env_val}"])
        elif local_rjms == Scheduler.SLURM:
            parallel_launcher.append("srun")
            if nodes_not_in_slot:
                parallel_launcher.append(f"--nodes={resources.num_nodes}")
            if resources.num_procs > 0:
                parallel_launcher.append(f"--ntasks={resources.num_procs}")
            if per_task_resources is not None:
                if not nodes_not_in_slot:
                    parallel_launcher.append(f"--nodes={per_task_resources.nodes}")
                if (
                    per_task_resources.cores is not None
                    and per_task_resources.cores > 0
                ):
                    parallel_launcher.append(
                        f"--cpus-per-task={per_task_resources.cores}"
                    )
                if per_task_resources.gpus is not None and per_task_resources.gpus > 0:
                    parallel_launcher.append(
                        f"--gpus-per-task={per_task_resources.gpus}"
                    )
            if resources.exclusive:
                parallel_launcher.append("--exclusive")
            if self.jobspec_settings.duration is not None:
                parallel_launcher.append(f"--time={self.jobspec_settings.duration}")
            for env_var, env_val in self.jobspec_settings.environment.items():
                parallel_launcher.insert(0, f"{env_var}={env_val}")
        elif local_rjms == Scheduler.FLUX:
            parallel_launcher.extend(["flux", "run"])
            if nodes_not_in_slot:
                parallel_launcher.append(f"--nodes={resources.num_nodes}")
            if resources.num_procs > 0:
                parallel_launcher.append(f"--ntasks={resources.num_procs}")
            if per_task_resources is not None:
                if not nodes_not_in_slot:
                    parallel_launcher.append(f"--nodes={per_task_resources.nodes}")
                if (
                    per_task_resources.cores is not None
                    and per_task_resources.cores > 0
                ):
                    parallel_launcher.append(
                        f"--cores-per-task={per_task_resources.cores}"
                    )
                if per_task_resources.gpus is not None and per_task_resources.gpus > 0:
                    parallel_launcher.append(
                        f"--gpus-per-task={per_task_resources.gpus}"
                    )
            if resources.exclusive:
                parallel_launcher.append("--exclusive")
            if self.jobspec_settings.duration is not None:
                parallel_launcher.append(
                    f"--time-limit={self.jobspec_settings.duration}"
                )
            for env_var, env_val in self.jobspec_settings.environment.items():
                parallel_launcher.append(f"--env={env_var}={env_val}")
        else:
            parallel_launcher.append("mpiexec")
            # The following settings are only supported by certain MPI
            # implementations, so we do not generate these flags.
            #   * resources.nodes/per_task_resources.node
            #   * per_task_resources.cores
            #   * per_task_resources.gpus
            #   * resources.exclusive
            #   * jobspec_settings.duration
            # If you need these things and you are using a RJMS that
            # does not have a dedicated launcher (e.g., srun and flux run),
            # consider generating the launcher command yourself
            if resources.num_procs > 0:
                parallel_launcher.extend(["-n", f"{resources.num_procs}"])
            for env_var, env_val in self.jobspec_settings.environment.items():
                parallel_launcher.insert(0, f"{env_var}={env_val}")
        return parallel_launcher

    def __repr__(self):
        return "Command(cmd={cmd},args={args})".format(
            cmd=self.command_or_exe.replace("\n", "\\n"), args=self.args
        )
