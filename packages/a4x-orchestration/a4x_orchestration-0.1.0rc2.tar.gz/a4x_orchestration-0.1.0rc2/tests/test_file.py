import pathlib

import pytest
from a4x.orchestration.file import File
from a4x.orchestration.site import PersistencyType, Site, StorageType


def test_file_construct():
    site = Site("tuolumne", "flux")
    directory = site.add_directory(
        "nfs0", "/nfs0/dummy_user", StorageType.SHARED, PersistencyType.PERSISTENT
    )
    dir0 = site.add_directory(
        "nfs1", "/nfs1/dummy_user", StorageType.SHARED, PersistencyType.PERSISTENT
    )

    file0 = File("test0.dat")
    assert file0.path_attr == pathlib.Path("test0.dat")
    assert file0.resolved_path is None
    assert not file0.is_resolved
    assert file0.path is None
    assert file0.directory is None
    assert file0.is_virtual
    assert file0.storage_type is None
    assert file0.persistency is None
    assert file0.site is None

    file0 = File("test0.dat", directory)
    assert file0.path_attr == pathlib.Path("test0.dat")
    assert file0.resolved_path is None
    assert not file0.is_resolved
    assert file0.path is None
    assert file0.directory == directory
    assert not file0.is_virtual
    assert file0.storage_type is None
    assert file0.persistency is None
    assert file0.site == site
    assert file0 in directory.files

    file0.set_directory(dir0)
    assert file0 not in directory.files
    assert file0 in dir0.files

    with pytest.raises(
        TypeError, match="^The file name must be either a string or a path-like object$"
    ):
        _ = File("test0.dat".encode())

    with pytest.raises(
        TypeError,
        match="^The 'directory' argument must be of type 'a4x.orchestration.Directory'$",
    ):
        _ = File("test0.dat", 10)


def test_file_resolve():
    site = Site("tuolumne", "flux")
    directory = site.add_directory(
        "nfs0", "/nfs0/dummy_user", StorageType.SHARED, PersistencyType.PERSISTENT
    )

    file0 = File("test0.dat")
    assert not file0.is_resolved
    file0.resolve()
    assert file0.is_resolved
    assert file0.path == pathlib.Path("test0.dat")
    assert file0.directory is None
    assert file0.is_virtual
    assert file0.storage_type is None
    assert file0.persistency is None
    assert file0.site is None

    file0 = File("test0.dat", directory)
    assert not file0.is_resolved
    file0.resolve()
    assert file0.is_resolved
    assert file0.path == pathlib.Path("/nfs0/dummy_user/test0.dat")
    assert file0.directory == directory
    assert not file0.is_virtual
    assert file0.storage_type == StorageType.SHARED
    assert file0.persistency == PersistencyType.PERSISTENT
    assert file0.site == site
