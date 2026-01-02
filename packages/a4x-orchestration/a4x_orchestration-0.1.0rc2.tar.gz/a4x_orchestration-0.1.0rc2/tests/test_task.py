# Copyright 2025 Global Computing Lab.
# See top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception

import pathlib

import pytest
from a4x.orchestration.command import Command
from a4x.orchestration.file import File
from a4x.orchestration.resources import JobspecSettings, Resources, Slot
from a4x.orchestration.site import Site, get_default_site, set_default_site
from a4x.orchestration.task import Task


def test_task_construct():
    name = "test_task"
    description = "This is a test"
    task = Task(name, description)
    assert task.task_name == name
    assert task.description == description
    assert task.commands == []
    assert task.inputs == []
    assert task.outputs == []
    assert task.add_input_extra_kwargs == {}
    assert task.add_output_extra_kwargs == {}
    assert task.jobspec_settings == JobspecSettings()


def test_task_sequence_funcs():
    name = "test_task"
    description = "This is a test"
    task = Task(name, description)

    with pytest.raises(IndexError):
        print(task[10])

    with pytest.raises(IndexError):
        del task[10]

    with pytest.raises(TypeError):
        task[10] = 5

    with pytest.raises(TypeError):
        task.insert(10, 5)

    cmd0 = Command("/usr/bin/bash")
    cmd1_str = "./test_program"
    cmd1 = Command(cmd1_str)
    cmd2 = Command("/usr/bin/bash", "-c", "'echo \"Hello World\"'")

    task.append(cmd1)
    task.append(cmd2)
    task.insert(0, cmd0)

    task[1] = cmd1_str

    assert task[0] == cmd0
    assert task[1] == cmd1
    assert task[2] == cmd2


def test_inputs():
    task = Task("inputs_test")

    path1 = File("test1.dat")
    path2 = File("test2.dat")

    task.add_inputs(path1, path2)
    assert task.add_input_extra_kwargs == {}
    assert task.get_inputs() == [path1, path2]

    task.add_inputs(path1, path2, pegasus_dummy_config_var="val")
    assert task.add_input_extra_kwargs == {"pegasus_dummy_config_var": "val"}
    assert task.get_inputs() == [path1, path2]

    with pytest.raises(TypeError):
        task.add_inputs(path1, "test2.dat")

    with pytest.raises(TypeError):
        task.add_inputs(10, path2)

    with pytest.raises(TypeError):
        task.add_inputs(10, "test2.dat")


def test_outputs():
    task = Task("outputs_test")

    path1 = File("test1.dat")
    path2 = File("test2.dat")

    task.add_outputs(path1, path2)
    assert task.add_output_extra_kwargs == {}
    assert task.get_outputs() == [path1, path2]

    task.add_outputs(path1, path2, pegasus_dummy_config_var="val")
    assert task.add_output_extra_kwargs == {"pegasus_dummy_config_var": "val"}
    assert task.get_outputs() == [path1, path2]

    with pytest.raises(TypeError):
        task.add_outputs(path1, "test2.dat")

    with pytest.raises(TypeError):
        task.add_outputs(10, path2)

    with pytest.raises(TypeError):
        task.add_outputs(10, "test2.dat")


def test_jobspec():
    name = "test_task"
    description = "This is a test"
    task = Task(name, description)

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

    name = "test_task"
    description = "This is a test"
    task = Task(name, description)

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


def test_task_set_site():
    site = Site("local")
    task = Task("test_task")

    task.set_site(site)

    with pytest.raises(TypeError, match="The site for a Task must be of type 'Site'"):
        task.set_site(10)


def test_task_site_resolution():
    task0 = Task("test_task0")
    task1 = Task("test_task1")
    task2 = Task("test_task2")
    task3 = Task("test_task3")

    site0 = Site("site0")
    dir0 = site0.add_directory("dir0", "/dummy/dir/0")
    file0 = File("file0.dat", dir0)

    site1 = Site("site1")
    dir1 = site1.add_directory("dir1", "/dummy/dir/1")
    file1 = File("file1.dat", dir1)

    task0.add_inputs(file0)

    task0._resolve_site()
    assert task0.site == site0

    task1.add_outputs(file1)

    task1._resolve_site()
    assert task1.site == site1

    task2.add_inputs(file0)
    task2.add_outputs(file1)

    with pytest.raises(RuntimeError):
        task2._resolve_site()

    task3._resolve_site()
    assert task3.site is None

    set_default_site(site0)

    assert get_default_site() == site0

    task3._resolve_site()
    assert task3.site == site0
