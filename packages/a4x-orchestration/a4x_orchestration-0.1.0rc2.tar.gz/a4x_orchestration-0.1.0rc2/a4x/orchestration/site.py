from __future__ import annotations

import pathlib
from collections.abc import MutableMapping
from typing import Set, Union

try:
    from enum import StrEnum
except ImportError:
    from strenum import StrEnum

from a4x.orchestration.annotations import AnnotationType
from a4x.orchestration.utils import StrCompatPathLike


class StorageType(StrEnum):
    """
    An enum representing a type of storage.
    """

    UNKNOWN = "unknown"
    LOCAL = "local"
    SHARED = "shared"


class PersistencyType(StrEnum):
    """
    An enum representing the persistency of storage.
    """

    UNKNOWN = "unknown"
    SCRATCH = "scratch"
    PERSISTENT = "persistent"


class Scheduler(StrEnum):
    """
    An enum representing the resource and job management system (RJMS) of a site.
    """

    UNKNOWN = "unknown"
    CONDOR = "condor"
    LSF = "lsf"
    PBS = "pbs"
    SGE = "sge"
    SLURM = "slurm"
    FLUX = "flux"


class Site(MutableMapping, AnnotationType):
    def __init__(
        self,
        site_or_host_name: str,
        scheduler_type: Union[Scheduler, str] = Scheduler.UNKNOWN,
    ):
        """
        Create a Site.

        :param site_or_host_name: the identifier/name of the site. Oftentimes the hostname of a system.
        :type site_or_host_name: str
        :param scheduler_type: the type of scheduler for the site.
        :type scheduler_type: Union[Scheduler, str]
        """
        AnnotationType.__init__(self)
        if not isinstance(site_or_host_name, str):
            raise TypeError("The 'site_or_host_name' argument must be of type 'str'")
        if site_or_host_name == "":
            raise ValueError(
                "The 'site_or_host_name' argument cannot be an empty string"
            )
        self.name = site_or_host_name
        if isinstance(scheduler_type, Scheduler):
            self.scheduler_type = scheduler_type
        elif isinstance(scheduler_type, str):
            self.scheduler_type = Scheduler(scheduler_type)
        else:
            raise TypeError(
                "The 'scheduler_type' argument must be of type 'str' or 'a4x.orchestration.Scheduler'"
            )
        self.directories_attr = {}

    @property
    def scheduler(self) -> Scheduler:
        return self.scheduler_type

    @scheduler.setter
    def scheduler(self, scheduler_type: Union[Scheduler, str]):
        if isinstance(scheduler_type, Scheduler):
            self.scheduler_type = scheduler_type
        elif isinstance(scheduler_type, str):
            self.scheduler_type = Scheduler(scheduler_type)
        else:
            raise TypeError(
                "The 'scheduler_type' argument must be of type 'str' or 'a4x.orchestration.Scheduler'"
            )

    def add_directory(
        self,
        identifier: str,
        path: StrCompatPathLike,
        storage_type: StorageType = StorageType.UNKNOWN,
        persistency: PersistencyType = PersistencyType.UNKNOWN,
    ):
        if identifier in self.directories_attr:
            raise KeyError(
                f"Cannot add a directory under identifier '{identifier}' because that identifier already exists. If you want to change an existing directory entry, use the Site class's dict-like interface"
            )
        # The Directory constructor self-registers the Directory in this Site
        new_dir = Directory(
            identifier=identifier,
            path=path,
            site=self,
            storage_type=storage_type,
            persistency=persistency,
        )
        return new_dir

    def __getitem__(self, key: str) -> Directory:
        return self.directories_attr[key]

    def __setitem__(self, key: str, val: Directory):
        if not isinstance(val, Directory):
            raise TypeError("Values of 'Site' must be of type 'Directory'")
        self.directories_attr[key] = val
        if val.identifier != key and val.identifier in self.directories_attr:
            del self.directories_attr[val.identifier]
        val.identifier = key

    def __delitem__(self, key: str):
        del self.directories_attr[key]

    def __len__(self) -> int:
        return len(self.directories_attr)

    def __iter__(self):
        return iter(self.directories_attr)

    def resolve_site_files(self):
        for directory in self.directories_attr.values():
            directory._resolve_files()

    @property
    def directories(self) -> Set[Directory]:
        return set(self.directories_attr.values())

    def __eq__(self, other) -> bool:
        return self.name == other.name and self.scheduler_type == other.scheduler_type

    def __hash__(self):
        return hash((self.name, self.scheduler_type))

    def __repr__(self):
        return f"Site(name={self.name},sched={self.scheduler_type})"


__DEFAULT_SITE_FOR_TASKS: Site = None


def set_default_site(site: Site):
    global __DEFAULT_SITE_FOR_TASKS
    __DEFAULT_SITE_FOR_TASKS = site


def get_default_site() -> Site:
    global __DEFAULT_SITE_FOR_TASKS
    return __DEFAULT_SITE_FOR_TASKS


class Directory:
    def __init__(
        self,
        identifier: str,
        path: StrCompatPathLike,
        site: Site,
        storage_type: Union[StorageType, str] = StorageType.UNKNOWN,
        persistency: Union[PersistencyType, str] = PersistencyType.UNKNOWN,
    ):
        if not isinstance(storage_type, (StorageType, str)):
            raise TypeError(
                "The 'storage_type' parameter must be of type 'StorageType' or a corresponding string value"
            )
        if not isinstance(persistency, (PersistencyType, str)):
            raise TypeError(
                "The 'persistency' parameter must be of type 'PersistencyType' or a corresponding string value"
            )
        self.identifier = identifier
        self.path = pathlib.Path(path)
        if not self.path.is_absolute():
            raise ValueError(
                "The 'path' argument must represent an absolute path (e.g., a string starting with '/' for Linux)"
            )
        self.storage_type_attr = StorageType(storage_type)
        self.persistency_attr = PersistencyType(persistency)
        self.site = site
        self.files = set()
        if self.identifier not in self.site:
            self.site[self.identifier] = self

    @property
    def storage_type(self) -> StorageType:
        return self.storage_type_attr

    @property
    def persistency(self) -> PersistencyType:
        return self.persistency_attr

    def get_site(self):
        return self.site

    def __truediv__(self, other: StrCompatPathLike):
        identifier = f"{self.identifier}/{str(other)}"
        if identifier in self.site:
            return self.site[identifier]
        return Directory(
            identifier=identifier,
            path=self.path / other,
            site=self.site,
            storage_type=self.storage_type_attr,
            persistency=self.persistency_attr,
        )

    def _add_file(self, f):
        if f not in self.files:
            self.files.add(f)

    def _remove_file(self, f):
        if f in self.files:
            self.files.remove(f)

    def _resolve_files(self):
        for f in self.files:
            f.resolve()

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, Directory)
            and self.path == other.path
            and self.site == other.site
            and self.storage_type_attr == other.storage_type_attr
            and self.persistency_attr == other.persistency_attr
        )

    def __hash__(self):
        return hash(
            (self.path, self.site, self.storage_type_attr, self.persistency_attr)
        )

    def __str__(self):
        return str(self.path)

    def __repr__(self):
        return f"Directory(path={self.path},site={self.site},storage_type={self.storage_type_attr},persistency={self.persistency_attr})"
