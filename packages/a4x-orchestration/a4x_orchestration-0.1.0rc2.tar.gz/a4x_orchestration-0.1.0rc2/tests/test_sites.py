import pytest
from a4x.orchestration.site import (
    Directory,
    PersistencyType,
    Scheduler,
    Site,
    StorageType,
)


def test_site_construct():
    site = Site("local")
    assert site.name == "local"
    assert site.scheduler_type == Scheduler.UNKNOWN
    assert str(site.scheduler_type) == "unknown"
    assert site.directories_attr == {}

    site = Site("access-pegasus", scheduler_type=Scheduler.CONDOR)
    assert site.name == "access-pegasus"
    assert site.scheduler_type == Scheduler.CONDOR
    assert str(site.scheduler_type) == "condor"
    assert site.directories_attr == {}

    site = Site("access-pegasus", scheduler_type="condor")
    assert site.name == "access-pegasus"
    assert site.scheduler_type == Scheduler.CONDOR
    assert str(site.scheduler_type) == "condor"
    assert site.directories_attr == {}

    site = Site("sierra", scheduler_type=Scheduler.LSF)
    assert site.name == "sierra"
    assert site.scheduler_type == Scheduler.LSF
    assert str(site.scheduler_type) == "lsf"
    assert site.directories_attr == {}

    site = Site("sierra", scheduler_type="lsf")
    assert site.name == "sierra"
    assert site.scheduler_type == Scheduler.LSF
    assert str(site.scheduler_type) == "lsf"
    assert site.directories_attr == {}

    site = Site("aurora", scheduler_type=Scheduler.PBS)
    assert site.name == "aurora"
    assert site.scheduler_type == Scheduler.PBS
    assert str(site.scheduler_type) == "pbs"
    assert site.directories_attr == {}

    site = Site("aurora", scheduler_type="pbs")
    assert site.name == "aurora"
    assert site.scheduler_type == Scheduler.PBS
    assert str(site.scheduler_type) == "pbs"
    assert site.directories_attr == {}

    site = Site("oracle", scheduler_type=Scheduler.SGE)
    assert site.name == "oracle"
    assert site.scheduler_type == Scheduler.SGE
    assert str(site.scheduler_type) == "sge"
    assert site.directories_attr == {}

    site = Site("oracle", scheduler_type="sge")
    assert site.name == "oracle"
    assert site.scheduler_type == Scheduler.SGE
    assert str(site.scheduler_type) == "sge"
    assert site.directories_attr == {}

    site = Site("frontier", scheduler_type=Scheduler.SLURM)
    assert site.name == "frontier"
    assert site.scheduler_type == Scheduler.SLURM
    assert str(site.scheduler_type) == "slurm"
    assert site.directories_attr == {}

    site = Site("frontier", scheduler_type="slurm")
    assert site.name == "frontier"
    assert site.scheduler_type == Scheduler.SLURM
    assert str(site.scheduler_type) == "slurm"

    site = Site("elcap", scheduler_type=Scheduler.FLUX)
    assert site.name == "elcap"
    assert site.scheduler_type == Scheduler.FLUX
    assert str(site.scheduler_type) == "flux"
    assert site.directories_attr == {}

    site = Site("elcap", scheduler_type="flux")
    assert site.name == "elcap"
    assert site.scheduler_type == Scheduler.FLUX
    assert str(site.scheduler_type) == "flux"
    assert site.directories_attr == {}

    with pytest.raises(
        TypeError, match="^The 'site_or_host_name' argument must be of type 'str'$"
    ):
        site = Site(site_or_host_name=10)

    with pytest.raises(
        ValueError, match="^The 'site_or_host_name' argument cannot be an empty string$"
    ):
        site = Site(site_or_host_name="")

    with pytest.raises(
        TypeError,
        match="^The 'scheduler_type' argument must be of type 'str' or 'a4x.orchestration.Scheduler'$",
    ):
        site = Site("local", scheduler_type=10)

    with pytest.raises(ValueError):
        site = Site("local", scheduler_type="bad_sched")


def test_site_scheduler_property():
    site = Site("local")
    assert site.scheduler == Scheduler.UNKNOWN

    site.scheduler = Scheduler.FLUX
    assert site.scheduler == Scheduler.FLUX

    site.scheduler = "slurm"
    assert site.scheduler == Scheduler.SLURM

    with pytest.raises(ValueError):
        site.scheduler = "bad_sched"

    with pytest.raises(
        TypeError,
        match="^The 'scheduler_type' argument must be of type 'str' or 'a4x.orchestration.Scheduler'$",
    ):
        site.scheduler = 10


def test_site_add_directory():
    site = Site("tuolumne", scheduler_type="flux")

    directory0 = site.add_directory("nfs0", "/nfs0/dummy_user")
    assert directory0.storage_type == StorageType.UNKNOWN
    assert directory0.persistency == PersistencyType.UNKNOWN
    assert directory0.get_site() == site

    directory1 = site.add_directory(
        "nfs1", "/nfs1/dummy_user", storage_type=StorageType.SHARED
    )
    assert directory1.storage_type == StorageType.SHARED
    assert directory1.persistency == PersistencyType.UNKNOWN
    assert directory1.get_site() == site

    directory2 = site.add_directory(
        "local", "/tmp/dummy_user", storage_type=StorageType.LOCAL
    )
    assert directory2.storage_type == StorageType.LOCAL
    assert directory1.persistency == PersistencyType.UNKNOWN
    assert directory1.get_site() == site

    directory3 = site.add_directory(
        "nfs2", "/nfs2/dummy_user", persistency=PersistencyType.PERSISTENT
    )
    assert directory3.storage_type == StorageType.UNKNOWN
    assert directory3.persistency == PersistencyType.PERSISTENT
    assert directory3.get_site() == site

    directory4 = site.add_directory(
        "scratch1", "/scratch/dummy_user", persistency=PersistencyType.SCRATCH
    )
    assert directory4.storage_type == StorageType.UNKNOWN
    assert directory4.persistency == PersistencyType.SCRATCH
    assert directory4.get_site() == site

    directory5 = site.add_directory(
        "scratch2",
        "/tmp/scratch/dummy_user",
        storage_type=StorageType.LOCAL,
        persistency=PersistencyType.SCRATCH,
    )
    assert directory5.storage_type == StorageType.LOCAL
    assert directory5.persistency == PersistencyType.SCRATCH
    assert directory5.get_site() == site

    directory6 = site.add_directory(
        "persistent_shared",
        "/lustre/dummy_user",
        storage_type=StorageType.SHARED,
        persistency=PersistencyType.PERSISTENT,
    )
    assert directory6.storage_type == StorageType.SHARED
    assert directory6.persistency == PersistencyType.PERSISTENT
    assert directory6.get_site() == site

    with pytest.raises(KeyError):
        site.add_directory("nfs1", "/non_existant_nfs/dummy_user")

    with pytest.raises(
        TypeError,
        match="^The 'storage_type' parameter must be of type 'StorageType' or a corresponding string value$",
    ):
        site.add_directory("test", "/path/doesnt/matter", storage_type=10)

    with pytest.raises(
        TypeError,
        match="^The 'persistency' parameter must be of type 'PersistencyType' or a corresponding string value$",
    ):
        site.add_directory("test", "/path/doesnt/matter", persistency=10)

    with pytest.raises(ValueError):
        site.add_directory("test", "./relative_path")


def test_site_mapping():
    site = Site("tuolumne", scheduler_type="flux")

    directory0 = Directory(
        "dir0", "/nfs0/dummy_user", site, StorageType.SHARED, PersistencyType.PERSISTENT
    )
    directory1 = Directory(
        "dir1", "/nfs1/dummy_user", site, StorageType.SHARED, PersistencyType.PERSISTENT
    )
    directory2 = Directory(
        "dir2", "/tmp/dummy_user", site, StorageType.LOCAL, PersistencyType.SCRATCH
    )

    assert site["dir0"] is directory0
    assert site["dir1"] is directory1
    assert site["dir2"] is directory2

    site["nfs0"] = directory0
    site["nfs1"] = directory1
    site["tmpfs"] = directory2

    with pytest.raises(TypeError, match="Values of 'Site' must be of type 'Directory'"):
        site["dummy"] = 10

    assert site["nfs0"] == directory0
    assert site["nfs1"] == directory1
    assert site["tmpfs"] == directory2

    assert "dir0" not in site
    assert "dir1" not in site
    assert "dir2" not in site

    with pytest.raises(KeyError):
        _ = site["bad_key"]

    assert len(site) == 3
    assert sorted(tuple(iter(site))) == sorted(("nfs0", "nfs1", "tmpfs"))

    del site["tmpfs"]

    assert len(site) == 2
    assert sorted(tuple(iter(site))) == sorted(("nfs0", "nfs1"))


def test_site_eq():
    site0 = Site("tuolumne", scheduler_type="flux")
    site1 = Site("tuolumne", scheduler_type="flux")
    site2 = Site("tuolumne")
    site3 = Site("local", scheduler_type="flux")
    site4 = Site("local", scheduler_type="flux")

    site3.add_directory("nfs0", "/nfs0/dummy_user")
    site4.add_directory("nfs0", "/nfs0/dummy_user")

    assert site0 == site1
    assert site0 != site2
    assert site0 != site3
    assert site3 == site4
