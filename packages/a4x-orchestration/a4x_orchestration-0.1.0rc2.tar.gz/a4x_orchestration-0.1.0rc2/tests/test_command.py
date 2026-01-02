import pytest
from a4x.orchestration.command import Command
from a4x.orchestration.site import Scheduler


def test_command():
    cmd_block = """
if [ "$a_var" == "yes" ]; then
    echo "YES"
else
    echo "NO"
fi
"""
    exe0 = "/usr/bin/bash"
    exe1 = "ls"
    args1 = ["-lah", "~"]

    cmd_block_obj = Command(cmd_block)
    assert cmd_block_obj.command_or_exe == cmd_block.strip()
    assert cmd_block_obj.is_block_command

    cmd_block_for_hash = Command(cmd_block)

    cmd0 = Command(exe0)
    assert cmd0.command_or_exe == exe0
    assert not cmd0.is_block_command

    cmd1 = Command(exe1, *args1)
    assert cmd1.command_or_exe == exe1
    assert cmd1.args == args1
    assert not cmd1.is_block_command

    assert hash(cmd_block_obj) != hash(cmd0)
    assert hash(cmd_block_obj) == hash(cmd_block_for_hash)
    assert cmd_block_obj != cmd0
    assert cmd_block_obj == cmd_block_for_hash
    assert cmd_block_obj != 5

    with pytest.raises(TypeError):
        cmd0 = Command(10)


def test_command_description():
    hostname_exe = "hostname"

    cmd = Command(hostname_exe)

    assert cmd.description is None

    desc = "This is a description"
    cmd.description = desc

    assert cmd.description == desc


def test_command_parallel_launch():
    hostname_exe = "hostname"

    cmd = Command(hostname_exe)

    cmd.set_resources(
        num_procs=4,
        cores_per_proc=96,
        gpus_per_proc=4,
        num_nodes=4,
        allocate_nodes_exclusively=True,
        exclusive_node_per_proc=False,
    )
    cmd.environment["OMP_NUM_THREADS"] = 96
    cmd.duration = 50

    jsrun_launch = [
        "jsrun",
        "--nrs",
        "4",
        "--cpu_per_rs",
        "96",
        "--gpu_per_rs",
        "4",
        "--env",
        "OMP_NUM_THREADS=96",
    ]
    srun_launch = [
        "OMP_NUM_THREADS=96",
        "srun",
        "--nodes=4",
        "--ntasks=4",
        "--cpus-per-task=96",
        "--gpus-per-task=4",
        "--exclusive",
        "--time=50",
    ]
    flux_run_launch = [
        "flux",
        "run",
        "--nodes=4",
        "--ntasks=4",
        "--cores-per-task=96",
        "--gpus-per-task=4",
        "--exclusive",
        "--time-limit=50",
        "--env=OMP_NUM_THREADS=96",
    ]
    mpiexec_launch = [
        "OMP_NUM_THREADS=96",
        "mpiexec",
        "-n",
        "4",
    ]

    assert cmd.generate_parallel_launch(Scheduler.LSF) == jsrun_launch
    assert cmd.generate_parallel_launch(Scheduler.SLURM) == srun_launch
    assert cmd.generate_parallel_launch(Scheduler.FLUX) == flux_run_launch
    assert cmd.generate_parallel_launch(Scheduler.SGE) == mpiexec_launch
    assert cmd.generate_parallel_launch(Scheduler.PBS) == mpiexec_launch
    assert cmd.generate_parallel_launch(Scheduler.CONDOR) == mpiexec_launch
    assert cmd.generate_parallel_launch(Scheduler.UNKNOWN) == mpiexec_launch
