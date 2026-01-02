# Copyright 2025 Global Computing Lab.
# See top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception

import pathlib

import pytest
from a4x.orchestration.resources import (
    JobspecSettings,
    Resources,
    SchedulableWork,
    Slot,
)


def test_slot_construct():
    ts = Slot(num_nodes=1, num_cores=None, num_gpus=None)

    assert ts.nodes == 1
    assert ts.cores is None
    assert ts.gpus is None

    with pytest.raises(TypeError):
        _ = Slot(num_nodes="1", num_cores=None, num_gpus=None)  # type: ignore

    with pytest.raises(ValueError):
        _ = Slot(num_nodes=0, num_cores=None, num_gpus=None)

    with pytest.raises(RuntimeError):
        _ = Slot(num_nodes=1, num_cores=None, num_gpus=4)

    with pytest.raises(RuntimeError):
        _ = Slot(num_nodes=1, num_cores=30, num_gpus=None)

    ts = Slot(num_nodes=None, num_cores=30, num_gpus=None)

    assert ts.nodes is None
    assert ts.cores == 30
    assert ts.gpus is None

    ts = Slot(num_nodes=None, num_cores=30, num_gpus=1)

    assert ts.nodes is None
    assert ts.cores == 30
    assert ts.gpus == 1

    with pytest.raises(TypeError):
        _ = Slot(num_nodes=None, num_cores="30", num_gpus=None)  # type: ignore

    with pytest.raises(TypeError):
        _ = Slot(num_nodes=None, num_cores=30, num_gpus="1")  # type: ignore

    with pytest.raises(RuntimeError):
        _ = Slot(num_nodes=None, num_cores=None, num_gpus=1)

    with pytest.raises(RuntimeError):
        _ = Slot(num_nodes=None, num_cores=0, num_gpus=1)

    with pytest.raises(ValueError):
        _ = Slot(num_nodes=None, num_cores=30, num_gpus=0)


def test_slot_eq():
    slot1 = Slot(num_nodes=1)
    slot2 = Slot(num_nodes=1)

    assert slot1 == slot2

    slot2 = Slot(num_cores=10)

    assert slot1 != slot2

    slot1 = Slot(num_cores=5)

    assert slot1 != slot2

    slot1 = Slot(num_cores=10)

    assert slot1 == slot2

    slot2 = Slot(num_cores=10, num_gpus=1)

    assert slot1 != slot2

    slot1 = Slot(num_cores=10, num_gpus=4)

    assert slot1 != slot2

    slot1 = Slot(num_cores=10, num_gpus=1)

    assert slot1 == slot2

    assert slot1 != "not a slot"


def test_slot_copy():
    ts = Slot(num_nodes=None, num_cores=30, num_gpus=1)
    ts_cpy = ts.copy()

    assert ts == ts_cpy


def test_slot_to_dict():
    slot = Slot(num_nodes=1)

    expected = {"nodes": {"count": 1}}

    assert slot.to_dict() == expected

    slot = Slot(num_cores=20)

    expected = {"cores": {"count": 20}}

    assert slot.to_dict() == expected

    slot = Slot(num_cores=20, num_gpus=4)

    expected = {"cores": {"count": 20}, "gpus": {"count": 4}}

    assert slot.to_dict() == expected


def test_resources_construct():
    res = Resources(
        num_procs=4,
        per_proc_resources=Slot(num_nodes=1),
        num_nodes=None,
        exclusive=False,
    )
    assert res.num_procs == 4
    assert res.num_nodes == 4
    assert res.num_slots_per_node == 1
    assert res.resources_per_slot == Slot(num_nodes=1)
    expected = {"slots": {"count": 4, "with": Slot(num_nodes=1)}}
    assert res.resource_dict == expected
    assert not res.exclusive

    res = Resources(
        num_procs=4,
        per_proc_resources=Slot(num_cores=10, num_gpus=1),
        num_nodes=1,
        exclusive=True,
    )
    assert res.num_procs == 4
    assert res.num_nodes == 1
    assert res.num_slots_per_node == 4
    assert res.resources_per_slot == Slot(num_cores=10, num_gpus=1)
    expected = {
        "nodes": {
            "count": 1,
            "with": {"slots": {"count": 4, "with": Slot(num_cores=10, num_gpus=1)}},
        }
    }
    assert res.resource_dict == expected
    assert res.exclusive

    res = Resources(
        num_procs=4,
        per_proc_resources=Slot(num_cores=10, num_gpus=1),
    )
    assert res.num_procs == 4
    assert res.num_nodes is None
    assert res.num_slots_per_node is None
    assert res.resources_per_slot == Slot(num_cores=10, num_gpus=1)
    expected = {
        "slots": {"count": 4, "with": Slot(num_cores=10, num_gpus=1)},
    }
    assert res.resource_dict == expected
    assert not res.exclusive

    with pytest.raises(TypeError):
        _ = Resources(
            num_procs="4",  # type: ignore
            per_proc_resources=Slot(num_cores=10, num_gpus=1),
        )

    with pytest.raises(TypeError):
        _ = Resources(
            num_procs=4,
            per_proc_resources=Slot(num_cores=10, num_gpus=1),
            num_nodes="1",  # type: ignore
        )

    with pytest.raises(TypeError):
        _ = Resources(
            num_procs=4,
            per_proc_resources=Slot(num_cores=10, num_gpus=1),
            exclusive="True",  # type: ignore
        )

    with pytest.raises(TypeError):
        _ = Resources(
            num_procs=4,
            per_proc_resources=("num_nodes", None, "num_cores", 10, "num_gpus", 1),  # type: ignore
        )

    with pytest.raises(ValueError):
        _ = Resources(
            num_procs=4,
            per_proc_resources=Slot(num_cores=10, num_gpus=1),
            num_nodes=10,
        )

    with pytest.warns(RuntimeWarning):
        _ = Resources(
            num_procs=4,
            per_proc_resources=Slot(num_cores=10, num_gpus=1),
            num_nodes=3,
        )


def test_resources_eq():
    res1 = Resources(
        num_procs=4, per_proc_resources=Slot(num_cores=10, num_gpus=1), num_nodes=1
    )
    res2 = Resources(
        num_procs=4, per_proc_resources=Slot(num_cores=10, num_gpus=1), num_nodes=1
    )
    assert res1 == res2

    res1 = Resources(num_procs=4, per_proc_resources=Slot(num_nodes=1))
    res2 = Resources(num_procs=4, per_proc_resources=Slot(num_nodes=1))
    assert res1 == res2

    res1 = Resources(
        num_procs=4,
        per_proc_resources=Slot(num_cores=10, num_gpus=1),
        num_nodes=1,
        exclusive=True,
    )
    res2 = Resources(
        num_procs=4, per_proc_resources=Slot(num_cores=10, num_gpus=1), num_nodes=1
    )
    assert res1 != res2

    res1 = Resources(
        num_procs=4, per_proc_resources=Slot(num_cores=10, num_gpus=1), num_nodes=1
    )
    res2 = Resources(
        num_procs=2, per_proc_resources=Slot(num_cores=10, num_gpus=1), num_nodes=1
    )
    assert res1 != res2

    res1 = Resources(
        num_procs=4, per_proc_resources=Slot(num_cores=10, num_gpus=1), num_nodes=1
    )
    res2 = Resources(
        num_procs=4, per_proc_resources=Slot(num_cores=10, num_gpus=1), num_nodes=4
    )
    assert res1 != res2

    res1 = Resources(num_procs=4, per_proc_resources=Slot(num_cores=10, num_gpus=1))
    res2 = Resources(num_procs=4, per_proc_resources=Slot(num_cores=10, num_gpus=1))
    assert res1 == res2

    res1 = Resources(num_procs=4, per_proc_resources=Slot(num_cores=10, num_gpus=1))
    res2 = Resources(
        num_procs=4, per_proc_resources=Slot(num_cores=10, num_gpus=1), num_nodes=1
    )
    assert res1 != res2

    assert res1 != "not a resource set"


def test_resources_copy():
    res = Resources(
        num_procs=4,
        per_proc_resources=Slot(num_cores=10, num_gpus=1),
        num_nodes=1,
        exclusive=True,
    )
    res_cpy = res.copy()
    assert res == res_cpy


def test_resources_to_dict():
    res = Resources(
        num_procs=4,
        per_proc_resources=Slot(num_cores=10, num_gpus=1),
        num_nodes=1,
        exclusive=True,
    )
    expected = {
        "exclusive": True,
        "resources": {
            "nodes": {
                "count": 1,
                "with": {
                    "slots": {
                        "count": 4,
                        "with": {"cores": {"count": 10}, "gpus": {"count": 1}},
                    }
                },
            }
        },
    }
    assert res.to_dict() == expected

    res = Resources(
        num_procs=4,
        per_proc_resources=Slot(num_nodes=1),
        num_nodes=None,
        exclusive=False,
    )
    expected = {
        "exclusive": False,
        "resources": {"slots": {"count": 4, "with": {"nodes": {"count": 1}}}},
    }
    assert res.to_dict() == expected

    res = Resources(
        num_procs=4,
        per_proc_resources=Slot(num_cores=10, num_gpus=1),
    )
    expected = {
        "exclusive": False,
        "resources": {
            "slots": {
                "count": 4,
                "with": {"cores": {"count": 10}, "gpus": {"count": 1}},
            }
        },
    }
    assert res.to_dict() == expected


def test_jobspec():
    task = SchedulableWork()

    task.duration = "2h"
    assert task.duration == "2h"

    task.duration = 120
    assert task.duration == 120

    task.duration = None
    assert task.duration is None

    with pytest.raises(TypeError):
        task.duration = 2.1  # type: ignore

    with pytest.raises(ValueError):
        task.duration = -1

    task.queue = "pbatch"
    assert task.queue == "pbatch"

    task.queue = None
    assert task.queue is None

    with pytest.raises(TypeError):
        task.queue = 10  # type: ignore

    task.cwd = "~"
    assert task.cwd == pathlib.Path("~").expanduser().resolve()

    task.cwd = pathlib.Path.cwd()
    assert task.cwd == pathlib.Path.cwd()

    task.cwd = None
    assert task.cwd is None

    with pytest.raises(TypeError):
        task.cwd = 10  # type: ignore

    base_env = {
        "PATH": "/home/user/bin:$PATH",
        "LD_LIBRARY_PATH": "/path/to/my/lib:$LD_LIBRARY_PATH",
    }

    task.environment = base_env
    assert task.environment == base_env

    task.environment = None
    assert task.environment == {}

    task.environment = base_env
    task.environment["EXTRA_ENV"] = "this is an extra env var"
    base_env["EXTRA_ENV"] = "this is an extra env var"
    assert task.environment == base_env

    with pytest.raises(TypeError):
        task.environment = "str"  # type: ignore

    redirect_file = "file_for_redirect.txt"

    task.stdin = redirect_file
    assert task.stdin == pathlib.Path(redirect_file)

    task.stdin = None
    assert task.stdin is None

    with pytest.raises(TypeError):
        task.stdin = 10  # type: ignore

    task.stdout = redirect_file
    assert task.stdout == pathlib.Path(redirect_file)

    task.stdout = None
    assert task.stdout is None

    with pytest.raises(TypeError):
        task.stdout = 10  # type: ignore

    task.stderr = redirect_file
    assert task.stderr == pathlib.Path(redirect_file)

    task.stderr = None
    assert task.stderr is None

    with pytest.raises(TypeError):
        task.stderr = 10  # type: ignore

    task.set_resources(
        num_procs=16,
        cores_per_proc=1,
        gpus_per_proc=1,
        num_nodes=2,
        allocate_nodes_exclusively=True,
    )
    expected_resources = Resources(
        num_procs=16,
        per_proc_resources=Slot(num_cores=1, num_gpus=1),
        num_nodes=2,
        exclusive=True,
    )
    assert task.get_resources() == expected_resources

    task.set_resources(num_procs=16, exclusive_node_per_proc=True)
    expected_resources = Resources(num_procs=16, per_proc_resources=Slot(num_nodes=1))
    assert task.get_resources() == expected_resources

    task.set_resources(num_procs=16, exclusive_node_per_proc=True)
    expected_resources = Resources(
        num_procs=16,
        per_proc_resources=Slot(num_nodes=1),
    )
    assert task.get_resources() == expected_resources

    with pytest.raises(ValueError):
        task.set_resources(
            num_procs="16",  # type: ignore
            cores_per_proc=1,
            gpus_per_proc=1,
            num_nodes=2,
            allocate_nodes_exclusively=True,
        )

    with pytest.raises(ValueError):
        task.set_resources(
            num_procs=-16,
            cores_per_proc=1,
            gpus_per_proc=1,
            num_nodes=2,
            allocate_nodes_exclusively=True,
        )

    with pytest.raises(ValueError):
        task.set_resources(
            num_procs=16,
            cores_per_proc="1",  # type: ignore
            gpus_per_proc=1,
            num_nodes=2,
            allocate_nodes_exclusively=True,
        )

    with pytest.raises(ValueError):
        task.set_resources(
            num_procs=16,
            cores_per_proc=-1,
            gpus_per_proc=1,
            num_nodes=2,
            allocate_nodes_exclusively=True,
        )

    with pytest.raises(ValueError):
        task.set_resources(
            num_procs=16,
            cores_per_proc=1,
            gpus_per_proc="1",  # type: ignore
            num_nodes=2,
            allocate_nodes_exclusively=True,
        )

    with pytest.raises(ValueError):
        task.set_resources(
            num_procs=16,
            cores_per_proc=1,
            gpus_per_proc=-1,
            num_nodes=2,
            allocate_nodes_exclusively=True,
        )

    with pytest.raises(ValueError):
        task.set_resources(
            num_procs=16,
            cores_per_proc=1,
            gpus_per_proc=1,
            num_nodes="2",  # type: ignore
            allocate_nodes_exclusively=True,
        )

    with pytest.raises(ValueError):
        task.set_resources(
            num_procs=16,
            cores_per_proc=1,
            gpus_per_proc=1,
            num_nodes=-2,
            allocate_nodes_exclusively=True,
        )

    with pytest.raises(TypeError):
        task.set_resources(
            num_procs=16,
            cores_per_proc=1,
            gpus_per_proc=1,
            num_nodes=2,
            allocate_nodes_exclusively="True",  # type: ignore
        )

    with pytest.raises(TypeError):
        task.set_resources(
            num_procs=16,
            exclusive_node_per_proc="True",  # type: ignore
        )

    task = SchedulableWork()

    task.duration = "2h"
    task.queue = "pbatch"
    task.environment = base_env
    task.stdout = redirect_file
    task.set_resources(
        num_procs=16,
        cores_per_proc=1,
        gpus_per_proc=1,
        num_nodes=2,
        allocate_nodes_exclusively=True,
    )

    expected_jobspec_settings = JobspecSettings()
    expected_jobspec_settings.duration = "2h"
    expected_jobspec_settings.queue = "pbatch"
    expected_jobspec_settings.environment = base_env
    expected_jobspec_settings.stdout = pathlib.Path(redirect_file)
    expected_jobspec_settings.resources = Resources(
        num_procs=16,
        per_proc_resources=Slot(num_cores=1, num_gpus=1),
        num_nodes=2,
        exclusive=True,
    )

    assert task.get_jobspec_settings() != "bad string"
    assert task.get_jobspec_settings() == expected_jobspec_settings

    expected_jobspec_settings.stdout = None
    assert task.get_jobspec_settings() != expected_jobspec_settings
