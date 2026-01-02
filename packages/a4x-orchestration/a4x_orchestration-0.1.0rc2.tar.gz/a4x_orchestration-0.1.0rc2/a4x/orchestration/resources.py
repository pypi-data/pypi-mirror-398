# Copyright 2025 Global Computing Lab.
# See top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception

from __future__ import annotations

import pathlib
from collections.abc import Mapping
from math import ceil
from typing import Any, Dict, Optional, Union
from warnings import warn

from a4x.orchestration.annotations import AnnotationType
from a4x.orchestration.file import File
from a4x.orchestration.site import Directory
from a4x.orchestration.utils import StrCompatPathLike, StrCompatPathLikeForIsInstance


class JobspecSettings:
    """
    A representation of common settings for a workflow task that may be passed to the underlying batch scheduler.

    On HPC systems, batch schedulers allow users to set various properties/settings for their jobs (e.g., a workflow task).
    A4X-Orchestration encodes some of the more common settings in this class. The specific settings encoded are:
    * :code:`duration`: the maximum allowed duration of the task. Some schedulers call this the "time limit"
    * :code:`queue`: the queue to which the task should be submitted. Some schedulers (namely Slurm) call this a "partition"
    * :code:`cwd`: the working directory of the task
    * :code:`environment`: the environment variables to set for the task
    * :code:`stdin`: the file to redirect :code:`stdin` to
    * :code:`stdin`: the file to redirect :code:`stdout` to
    * :code:`stderr`: the file to redirect :code:`stderr` to
    * :code:`resources`: the requested resources for the task
    """

    def __init__(self):
        self.duration: Optional[Union[int, str]] = None
        self.queue: Optional[str] = None
        self.cwd: Optional[Union[pathlib.Path, Directory]] = None
        self.environment: Dict[str, Any] = {}
        self.stdin: Optional[Union[pathlib.Path, File]] = None
        self.stdout: Optional[Union[pathlib.Path, File]] = None
        self.stderr: Optional[Union[pathlib.Path, File]] = None
        self.resources: Resources = None  # type: ignore

    def __hash__(self):
        return hash(
            (
                self.duration,
                self.queue,
                self.cwd,
                frozenset(self.environment),
                self.stdin,
                self.stdout,
                self.stderr,
                self.resources,
            )
        )

    def __eq__(self, other: object):
        if not isinstance(other, JobspecSettings):
            return False
        are_same = (
            self.cwd == other.cwd
            and self.environment == other.environment
            and self.resources == other.resources
        )
        for opt_member_self, opt_member_other in zip(
            [self.duration, self.queue, self.stdin, self.stdout, self.stderr],
            [other.duration, other.queue, other.stdin, other.stdout, other.stderr],
        ):
            if opt_member_self is None and opt_member_other is None:
                are_same = are_same and True
            elif opt_member_self is not None and opt_member_other is not None:
                are_same = are_same and (opt_member_self == opt_member_other)
            else:
                are_same = are_same and False
        return are_same


class SchedulableWork(AnnotationType):
    """
    A class representing any unit of work (e.g., :code:`Command` and :code:`Task`)
    that can support scheduling settings. It provides various properties and methods
    to set and get scheduling settings.
    """

    def __init__(self):
        super().__init__()
        self.jobspec_settings = JobspecSettings()

    @property
    def duration(self):
        """
        The duration of the schedulable work.

        Can be either a number or a string, as supported by the WMS plugin.
        """
        return self.jobspec_settings.duration

    @duration.setter
    def duration(self, duration: Optional[Union[int, str]]):
        if duration is not None and not isinstance(duration, (int, str)):
            raise TypeError("The 'duration' property must be an int or string")
        if duration is not None and isinstance(duration, int) and duration <= 0:
            raise ValueError(
                "When the 'duration' property is an integer, its value must be positive"
            )
        self.jobspec_settings.duration = duration

    @property
    def queue(self):
        """The queue/partition that the schedulable work should run under"""
        return self.jobspec_settings.queue

    @queue.setter
    def queue(self, q: Optional[str]):
        if q is not None and not isinstance(q, str):
            raise TypeError("The 'queue' property must be set to a string")
        self.jobspec_settings.queue = q

    @property
    def cwd(self):
        """The working directory of the schedulable work"""
        return self.jobspec_settings.cwd

    @cwd.setter
    def cwd(self, cwd: Optional[Union[StrCompatPathLike, Directory]]):
        if cwd is not None and not isinstance(
            cwd, (StrCompatPathLikeForIsInstance, Directory)
        ):
            raise TypeError(
                "The 'cwd' property must be set to a path-like object, a string, or an A4X-Orchestration Directory"
            )
        if cwd is not None and isinstance(cwd, StrCompatPathLikeForIsInstance):
            self.jobspec_settings.cwd = pathlib.Path(cwd).expanduser().resolve()
        else:
            self.jobspec_settings.cwd = cwd

    @property
    def environment(self):
        """
        A dictionary storing environment variables and their values.

        This property behaves similarly to :code:`os.environ`.
        """
        return self.jobspec_settings.environment

    @environment.setter
    def environment(self, environ: Optional[Mapping]):
        if environ is not None and not isinstance(environ, Mapping):
            raise TypeError("The 'environment' property must be a mapping")
        self.jobspec_settings.environment = dict(environ) if environ is not None else {}

    @property
    def stdin(self):
        """A file path to use for redirection of STDIN"""
        return self.jobspec_settings.stdin

    @stdin.setter
    def stdin(self, stdin: Optional[Union[StrCompatPathLike, File]]):
        if stdin is not None and not isinstance(
            stdin, (StrCompatPathLikeForIsInstance, File)
        ):
            raise TypeError(
                "The 'stdin' property must be a path-like object, a string, or an A4X-Orchestration File"
            )
        self.jobspec_settings.stdin = stdin
        if isinstance(stdin, StrCompatPathLikeForIsInstance):
            self.jobspec_settings.stdin = pathlib.Path(stdin)

    @property
    def stdout(self):
        """A file path to use for redirection of STDOUT"""
        return self.jobspec_settings.stdout

    @stdout.setter
    def stdout(self, stdout: Optional[Union[StrCompatPathLike, File]]):
        if stdout is not None and not isinstance(
            stdout, (StrCompatPathLikeForIsInstance, File)
        ):
            raise TypeError(
                "The 'stdout' property must be a path-like object, a string, or an A4X-Orchestration File"
            )
        self.jobspec_settings.stdout = stdout
        if isinstance(stdout, StrCompatPathLikeForIsInstance):
            self.jobspec_settings.stdout = pathlib.Path(stdout)

    @property
    def stderr(self):
        """A file path to use for redirection of STDERR"""
        return self.jobspec_settings.stderr

    @stderr.setter
    def stderr(self, stderr: Optional[Union[StrCompatPathLike, File]]):
        if stderr is not None and not isinstance(
            stderr, (StrCompatPathLikeForIsInstance, File)
        ):
            raise TypeError(
                "The 'stderr' property must be a path-like object or a string"
            )
        self.jobspec_settings.stderr = stderr
        if isinstance(stderr, StrCompatPathLikeForIsInstance):
            self.jobspec_settings.stderr = pathlib.Path(stderr)

    def set_resources(
        self,
        num_procs: int = 1,
        cores_per_proc: Optional[int] = None,
        gpus_per_proc: Optional[int] = None,
        num_nodes: Optional[int] = None,
        allocate_nodes_exclusively: bool = False,
        exclusive_node_per_proc: bool = False,
    ):
        """
        Set the resources for the schedulable work.

        :param num_procs: number of processes/slots (i.e., MPI task/rank) to use
        :type num_procs: int
        :param cores_per_proc: number of CPU cores per process/slot
        :type cores_per_proc: int
        :param gpus_per_proc: number of GPUs per process/slot
        :type gpus_per_proc: int
        :param num_nodes: number of nodes
        :type num_nodes: int
        :param allocate_nodes_exclusively: if True, ask the scheduler to allocate nodes exclusively (i.e., not shared with other users)
        :type allocate_nodes_exclusively: bool
        :param exclusive_node_per_proc: if True, give each process an entire node's worth of resources
        :type exclusive_node_per_proc: bool
        :raises ValueError: if any input has an invalid value
        :raises TypeError: if :code:`allocate_nodes_exclusively: or :code:`exclusive_node_per_proc` is not a bool
        """
        if not isinstance(num_procs, int) or num_procs <= 0:
            raise ValueError("num_procs must be a non-negative integer")
        if cores_per_proc is not None and (
            not isinstance(cores_per_proc, int) or cores_per_proc <= 0
        ):
            raise ValueError("cores_per_proc must be a non-negative integer or None")
        if gpus_per_proc is not None and (
            not isinstance(gpus_per_proc, int) or gpus_per_proc <= 0
        ):
            raise ValueError("gpus_per_proc must be a non-negative integer or None")
        if num_nodes is not None and (not isinstance(num_nodes, int) or num_nodes <= 0):
            raise ValueError("num_nodes must be a non-negative integer or None")
        if not isinstance(allocate_nodes_exclusively, bool):
            raise TypeError("allocate_nodes_exclusively must be a boolean")
        if not isinstance(exclusive_node_per_proc, bool):
            raise TypeError("exclusive_node_per_proc must be a boolean")
        if exclusive_node_per_proc:
            proc_resources = Slot(num_nodes=1)
            total_num_nodes = num_procs
        else:
            if cores_per_proc is None:
                cores_per_proc = 1
            proc_resources = Slot(num_cores=cores_per_proc, num_gpus=gpus_per_proc)
            total_num_nodes = num_nodes
        self.jobspec_settings.resources = Resources(
            num_procs=num_procs,
            per_proc_resources=proc_resources,
            num_nodes=total_num_nodes,
            exclusive=allocate_nodes_exclusively,
        )
        return self

    def get_resources(self):
        """Get the resource request for the schedulable work"""
        if self.jobspec_settings.resources is None:
            return None
        return self.jobspec_settings.resources.copy()

    def get_jobspec_settings(self):
        """Get all scheduling settings for the schedulable work"""
        return self.jobspec_settings


class Resources:
    """
    The representation of the resource set for a workflow task.

    This class (and its companion: :py:class:`Slot`) are heavily inspired by the representation of resources for jobs
    in the Flux resource manager. For more information about how Flux represents resources, see Flux's
    `RFC 14 <https://flux-framework.readthedocs.io/projects/flux-rfc/en/latest/spec_14.html#canonical-job-specification>`_.

    A set of resources consists of one or more "slots", which may be evenly divided across a number of nodes, if specified.
    A "slot" represents the resources for each process in the workflow task. In other words, the workflow management system or
    (more likely) the platform's batch scheduler will allocate out the resources for the all the slots and then assign
    one process to each slot.

    Workflow developers should not use this class directly. Instead, they should use the
    :py:meth:`a4x.orchestration.task.Task.set_resources` method.
    """

    def __init__(
        self,
        num_procs: int,
        per_proc_resources: Slot,
        num_nodes: Optional[int] = None,
        exclusive: bool = False,
    ):
        """
        Construct a set of resources.

        :param num_procs: number of processes in the workflow task
        :type num_procs: int
        :param per_proc_resources: resources needed for each process in the workflow task
        :type per_proc_resources: :py:class:`Slot`
        :param num_nodes: total number of nodes that should be allocated to the workflow task. Ignored if nodes are specified in `per_proc_resource`
        :type num_nodes: Optional[int]
        :param exclusive: if ``True``, the workflow task should have exclusive control of the nodes allocated
        :type exclusive: bool
        :raises TypeError: if any input has an invalid type
        :raises ValueError: if `num_nodes` is larger than `num_procs` because that would waste resources
        """
        if not isinstance(num_procs, int):
            raise TypeError("Total number of processes must be an int")
        if num_nodes is not None and not isinstance(num_nodes, int):
            raise TypeError(
                "Number of nodes must be an int (or None when each process gets its own exclusive node)"
            )
        if not isinstance(exclusive, bool):
            raise TypeError("The 'exclusive' parameter must be a boolean")
        if not isinstance(per_proc_resources, Slot):
            raise TypeError("The per-process resources must be of type Slot")
        procs_have_exclusive_nodes = per_proc_resources.nodes is not None
        self.resource_dict = {}
        self.total_num_procs = num_procs
        self.exclusive = exclusive
        if not procs_have_exclusive_nodes and num_nodes is not None:
            if num_nodes > num_procs:
                raise ValueError(
                    "The number of nodes cannot be greater than the number of procs without wasting resources"
                )
            if num_procs % num_nodes != 0:
                warn(
                    f"It is not possible to evenly distribute {num_procs} procs (e.g., MPI ranks) across {num_nodes}",
                    RuntimeWarning,
                )
            self.total_num_nodes = num_nodes
            total_num_slots_per_node = int(ceil(num_procs / float(num_nodes)))
            self.resource_dict = {
                "nodes": {
                    "count": self.total_num_nodes,
                    "with": {
                        "slots": {
                            "count": total_num_slots_per_node,
                            "with": per_proc_resources.copy(),
                        }
                    },
                }
            }
        elif not procs_have_exclusive_nodes:
            self.total_num_nodes = None
            self.resource_dict = {
                "slots": {"count": num_procs, "with": per_proc_resources.copy()}
            }
        else:
            self.total_num_nodes = num_procs
            self.resource_dict = {
                "slots": {"count": num_procs, "with": per_proc_resources.copy()}
            }

    def __eq__(self, other: object) -> bool:
        """
        Checks if one resource set is equal to the other

        :param other: the other resource set
        :type other: :py:class:`Resources`
        :return: ``True`` if equal, ``False`` otherwise
        :rtype: bool
        """
        if not isinstance(other, Resources):
            return False
        if self.total_num_nodes is None:
            are_equal = other.total_num_nodes is None
        else:
            are_equal = (
                other.total_num_nodes is not None
                and self.total_num_nodes == other.total_num_nodes
            )
        return (
            are_equal
            and self.total_num_procs == other.total_num_procs
            and self.resource_dict == other.resource_dict
            and self.exclusive == other.exclusive
        )

    def copy(self):
        """
        Create a new resource set with the same values as :code:`self`

        :return: a copy of the resource set
        :rtype: :py:class:`Resources`
        """
        new_resources = Resources(
            num_procs=self.num_procs,
            per_proc_resources=self.resources_per_slot,
            num_nodes=self.num_nodes,
            exclusive=self.exclusive,
        )
        return new_resources

    @property
    def num_procs(self) -> int:
        """
        Get the number of processes in the resource set

        :return: the number of processes in the resource set
        :rtype: int
        """
        return self.total_num_procs

    @property
    def num_nodes(self) -> Optional[int]:
        """
        Get the number of nodes in the resource set

        :return: the number of nodes in the resource set, or ``None`` if the number of nodes is not specified
        :rtype: Optional[int]
        """
        # If this returns None, then we don't have an explicit number of nodes requested
        return self.total_num_nodes

    @property
    def num_slots_per_node(self) -> Optional[int]:
        """
        Get the number of slots per node in the resource set

        :return: the number of slots per node in the resource set, or ``None`` if the number of nodes is not specified
        :rtype: Optional[int]
        """
        if "slots" in self.resource_dict:
            return 1 if self.total_num_nodes is not None else None
        return self.resource_dict["nodes"]["with"]["slots"]["count"]  # type: ignore

    @property
    def resources_per_slot(self) -> Slot:
        """
        Get the resources for each slot in the resource set

        :return: the resources for each slot in the resource set
        :rtype: :py:class:`Slot`
        """
        if "slots" in self.resource_dict:
            return self.resource_dict["slots"]["with"]
        return self.resource_dict["nodes"]["with"]["slots"]["with"]

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the resouce set to a JSON-like dictionary representation that is roughly equivalent to a Flux resource request

        :return: the dictionary representation of the resource set
        :rtype: ``Dict[str, Any]``
        """
        resource_dict: Dict[str, Any] = {"exclusive": self.exclusive}
        resource_dict["resources"] = self.resource_dict.copy()
        if "slots" in self.resource_dict:
            resource_dict["resources"]["slots"]["with"] = self.resource_dict["slots"][
                "with"
            ].to_dict()
        else:
            resource_dict["resources"]["nodes"]["with"]["slots"]["with"] = (
                self.resource_dict["nodes"]["with"]["slots"]["with"].to_dict()
            )
        return resource_dict


class Slot:
    """
    The representation of the resource set of a single process in a workflow task.

    As described with the :py:class:`Resources` class, the concept of a "slot" is heavily inspired
    by the representation of resources for jobs in the Flux resource manager. For more information
    about how Flux represents resources, see Flux's
    `RFC 14 <https://flux-framework.readthedocs.io/projects/flux-rfc/en/latest/spec_14.html#canonical-job-specification>`_.
    """

    def __init__(
        self,
        num_nodes: Optional[int] = None,
        num_cores: Optional[int] = None,
        num_gpus: Optional[int] = None,
    ):
        """
        Create a slot with the specified resources.

        :param num_nodes: the number of nodes that each process should have access to. If not ``None``, this value should always be 1
        :type num_nodes: Optional[int]
        :param num_cores: the number of cores that each process should have access to
        :type num_cores: Optional[int]
        :param num_gpus: the number of GPUs that each process should have access to
        :type num_gpus: Optional[int]

        .. note::
           If :code:`num_nodes` is not ``None``, then :code:`num_cores` and :code:`num_gpus` should be ``None``
           because each process will get all the cores and GPUs on the node. Conversely, if :code:`num_cores`
           is not ``None``, then :code:`num_nodes` should be ``None`` because each process is getting less than
           one node's worth of resources. If :code:`num_cores` is not ``None``, then :code:`num_gpus` can either be
           ``None`` (to request no GPUs per process) or an integer (to request that number of GPUs per process).

        .. warning::
           A4X-Orchestration currently does **not** validate the resources you request. If you request more resources
           than are actually available, A4X-Orchestration will happily inject those values into your workflow configuration,
           which will cause your workflow to crash. Users should take care to not request more resources than can be feasibly
           used on the system.
        """
        if num_nodes is not None and not isinstance(num_nodes, int):
            raise TypeError(
                "The number of nodes for a process must be either an int or None"
            )
        if num_cores is not None and not isinstance(num_cores, int):
            raise TypeError(
                "The number of cores for a process must be either an int or None"
            )
        if num_gpus is not None and not isinstance(num_gpus, int):
            raise TypeError(
                "The number of GPUs for a process must be either an int or None"
            )
        if num_nodes is not None and (num_cores is not None or num_gpus is not None):
            raise RuntimeError(
                "INTERNAL ERROR: if each process is getting its own exclusive node, num_cores and num_gpus should not be provided to Slot"
            )
        if num_nodes is not None and num_nodes != 1:
            raise ValueError("Tasks cannot run on more or less than 1 node at a time")
        if num_nodes is None and (num_cores is None or num_cores <= 0):
            raise RuntimeError("INTERNAL ERROR: a process must have some CPU cores")
        if num_gpus is not None and num_gpus <= 0:
            raise ValueError("Number of GPUs must be a positive integer")
        self.num_nodes: Optional[int] = num_nodes
        self.num_cores: Optional[int] = num_cores
        self.num_gpus: Optional[int] = num_gpus

    def __eq__(self, other: object) -> bool:
        """
        Checks if one slot is equal to the other

        :param other: the other slot
        :type other: :py:class:`Slot`
        :return: ``True`` if equal, ``False`` otherwise
        :rtype: bool
        """
        if not isinstance(other, Slot):
            return False
        if self.num_nodes is None:
            are_equal = (
                other.num_nodes is None
                and self.num_cores is not None
                and other.num_cores is not None
                and self.num_cores == other.num_cores
            )
            if self.num_gpus is None:
                are_equal = are_equal and other.num_gpus is None
            else:
                are_equal = (
                    are_equal
                    and other.num_gpus is not None
                    and self.num_gpus == other.num_gpus
                )
        else:
            are_equal = (
                other.num_nodes is not None
                and self.num_nodes == other.num_nodes
                and self.num_cores is None
                and other.num_cores is None
                and self.num_gpus is None
                and other.num_gpus is None
            )
        return are_equal

    def copy(self):
        """
        Create a new slot with the same values as :code:`self`

        :return: a copy of the slot
        :rtype: :py:class:`Slot`
        """
        return Slot(num_nodes=self.nodes, num_cores=self.cores, num_gpus=self.gpus)

    @property
    def nodes(self) -> Optional[int]:
        """
        Get the number of nodes in the slot

        :return: the number of nodes in the slot, or ``None`` if the number of nodes is not specified
        :rtype: Optional[int]
        """
        return self.num_nodes

    @property
    def cores(self) -> Optional[int]:
        """
        Get the number of cores in the slot

        :return: the number of cores in the slot, or ``None`` if the number of cores is not specified
        :rtype: Optional[int]
        """
        return self.num_cores

    @property
    def gpus(self) -> Optional[int]:
        """
        Get the number of GPUs in the slot

        :return: the number of GPUs in the slot, or ``None`` if the number of GPUs is not specified
        :rtype: Optional[int]
        """
        return self.num_gpus

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the slot to a JSON-like dictionary representation that is roughly equivalent to a Flux resource request

        :return: the dictionary representation of the slot
        :rtype: ``Dict[str, Any]``
        """
        resource_dict = {}
        if self.num_nodes is not None:
            resource_dict = {"nodes": {"count": self.num_nodes}}
        else:
            resource_dict = {"cores": {"count": self.num_cores}}
            if self.num_gpus is not None:
                resource_dict.update({"gpus": {"count": self.num_gpus}})
        return resource_dict
