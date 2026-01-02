from pathlib import Path
from typing import Optional

from a4x.orchestration.site import Directory, PersistencyType, Site, StorageType
from a4x.orchestration.utils import StrCompatPathLike, StrCompatPathLikeForIsInstance


class File:
    def __init__(self, p: StrCompatPathLike, directory: Directory = None):
        if not isinstance(p, StrCompatPathLikeForIsInstance):
            raise TypeError(
                "The file name must be either a string or a path-like object"
            )
        self.path_attr = Path(p)
        self.resolved_path = None
        self.directory = None
        self.storage_type_attr = None
        self.persistency_attr = None
        self.is_resolved = False
        if directory is not None:
            self.set_directory(directory)

    def set_directory(self, directory: Directory):
        if not isinstance(directory, Directory):
            raise TypeError(
                "The 'directory' argument must be of type 'a4x.orchestration.Directory'"
            )
        old_directory = self.directory
        self.directory = directory
        # Note: this conditional for Directory._add_file and Directory._remove_file
        #       must come after setting self.directory. Otherwise, the set hashing that
        #       happens in _add_file and _remove_file will not work properly
        if old_directory is None:
            directory._add_file(self)
        else:
            old_directory._remove_file(self)
            directory._add_file(self)
        if self.is_resolved:
            self.is_resolved = False
            self.storage_type_attr = None
            self.persistency_attr = None
            self.resolved_path = None

    def resolve(self):
        if self.directory is not None:
            self.resolved_path = self.directory.path / self.path_attr
            self.storage_type_attr = self.directory.storage_type
            self.persistency_attr = self.directory.persistency
        else:
            self.resolved_path = self.path_attr
            self.storage_type_attr = None
            self.persistency_attr = None
        self.is_resolved = True

    @property
    def storage_type(self) -> Optional[StorageType]:
        return self.storage_type_attr

    @property
    def persistency(self) -> Optional[PersistencyType]:
        return self.persistency_attr

    @property
    def site(self) -> Optional[Site]:
        if self.directory is None:
            return None
        return self.directory.site

    @property
    def path(self) -> Optional[Path]:
        if not self.is_resolved or self.resolved_path is None:
            return None
        return self.resolved_path

    @property
    def is_virtual(self) -> bool:
        return self.directory is None

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, File)
            and self.path_attr == other.path_attr
            and self.directory == other.directory
        )

    def __hash__(self):
        return hash((self.path_attr, self.directory))

    def __repr__(self):
        repr_str = f"File(path={str(self.path_attr)}"
        if self.directory is not None:
            repr_str += f",dir={repr(self.directory)}"
        repr_str += ")"
        return repr_str
