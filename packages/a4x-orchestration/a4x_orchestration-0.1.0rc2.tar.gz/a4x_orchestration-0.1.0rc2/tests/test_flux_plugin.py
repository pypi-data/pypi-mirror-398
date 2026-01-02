import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pytest
from a4x.orchestration.builtin_plugins.flux import FluxPlugin
from a4x.orchestration.site import Scheduler
from a4x.orchestration.workflow import Workflow
from ruamel.yaml import YAML


def test_flux_plugin_bad_site(maestro_lulesh_workflow):
    tasks, edges, _ = maestro_lulesh_workflow

    wflow = Workflow("flux_lulesh_workflow")

    wflow.add_tasks(*tasks)

    expected_edges = []
    for src, dests in edges.items():
        for dst in dests:
            wflow.add_edge(src, dst)
            expected_edges.append((src.task_name, dst.task_name))

    with pytest.raises(ValueError):
        _ = FluxPlugin(wflow)


def test_flux_plugin_shell_launcher(
    helper,
    maestro_lulesh_workflow,
    flux_plugin_launch_sh,
    flux_plugin_make_lulesh,
    flux_plugin_run_lulesh_100_10,
):
    tasks, edges, _ = maestro_lulesh_workflow

    wflow = Workflow("flux_lulesh_workflow")

    wflow.add_tasks(*tasks)

    expected_edges = []
    for src, dests in edges.items():
        for dst in dests:
            wflow.add_edge(src, dst)
            expected_edges.append((src.task_name, dst.task_name))

    assert len(wflow.sites) == 1
    for site in wflow.sites:
        site.scheduler = Scheduler.FLUX

    plugin = FluxPlugin(wflow)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        plugin.configure(tmpdir, use_shell_launcher=True, exist_ok=True)

        make_lulesh_file = tmpdir_path / "make_lulesh_script.sh"
        lulesh_100_10_file = tmpdir_path / "run_lulesh_100_10_script.sh"
        launch_file = tmpdir_path / "launch.sh"

        make_lulesh_test_file = helper.load_flux_plugin_test_file(
            flux_plugin_make_lulesh, tmpdir
        )
        lulesh_100_10_test_file = helper.load_flux_plugin_test_file(
            flux_plugin_run_lulesh_100_10, tmpdir
        )
        launch_test_file = helper.load_flux_plugin_test_file(
            flux_plugin_launch_sh, tmpdir
        )

        with open(make_lulesh_file, "r") as f:
            make_lulesh_lines = helper.readlines_for_script_file(f)
            assert make_lulesh_lines == make_lulesh_test_file

        with open(lulesh_100_10_file, "r") as f:
            lulesh_100_10_lines = helper.readlines_for_script_file(f)
            assert lulesh_100_10_lines == lulesh_100_10_test_file

        with open(launch_file, "r") as f:
            launch_lines = helper.readlines_for_script_file(f)
            assert launch_lines == launch_test_file


def test_flux_plugin_python_launcher(
    helper,
    maestro_lulesh_workflow,
    flux_plugin_launch_py,
    flux_plugin_make_lulesh,
    flux_plugin_run_lulesh_100_10,
):
    tasks, edges, _ = maestro_lulesh_workflow

    wflow = Workflow("flux_lulesh_workflow")

    wflow.add_tasks(*tasks)

    expected_edges = []
    for src, dests in edges.items():
        for dst in dests:
            wflow.add_edge(src, dst)
            expected_edges.append((src.task_name, dst.task_name))

    assert len(wflow.sites) == 1
    for site in wflow.sites:
        site.scheduler = Scheduler.FLUX

    plugin = FluxPlugin(wflow)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        plugin.configure(tmpdir, use_shell_launcher=False, exist_ok=True)

        make_lulesh_file = tmpdir_path / "make_lulesh_script.sh"
        lulesh_100_10_file = tmpdir_path / "run_lulesh_100_10_script.sh"
        launch_file = tmpdir_path / "launch.py"

        make_lulesh_test_file = helper.load_flux_plugin_test_file(
            flux_plugin_make_lulesh, tmpdir
        )
        lulesh_100_10_test_file = helper.load_flux_plugin_test_file(
            flux_plugin_run_lulesh_100_10, tmpdir
        )
        launch_test_file = helper.load_flux_plugin_test_file(
            flux_plugin_launch_py, tmpdir
        )

        with open(make_lulesh_file, "r") as f:
            make_lulesh_lines = helper.readlines_for_script_file(f)
            assert make_lulesh_lines == make_lulesh_test_file

        with open(lulesh_100_10_file, "r") as f:
            lulesh_100_10_lines = helper.readlines_for_script_file(f)
            assert lulesh_100_10_lines == lulesh_100_10_test_file

        with open(launch_file, "r") as f:
            launch_lines = helper.readlines_for_script_file(f)
            assert launch_lines == launch_test_file


def test_flux_plugin_bad_site_scheduler(maestro_lulesh_workflow):
    tasks, edges, _ = maestro_lulesh_workflow

    wflow = Workflow("flux_lulesh_workflow")

    wflow.add_tasks(*tasks)

    expected_edges = []
    for src, dests in edges.items():
        for dst in dests:
            wflow.add_edge(src, dst)
            expected_edges.append((src.task_name, dst.task_name))

    with pytest.raises(ValueError):
        _ = FluxPlugin(wflow)


def test_flux_plugin_execute(maestro_lulesh_workflow):
    tasks, edges, _ = maestro_lulesh_workflow

    wflow = Workflow("flux_lulesh_workflow")

    wflow.add_tasks(*tasks)

    expected_edges = []
    for src, dests in edges.items():
        for dst in dests:
            wflow.add_edge(src, dst)
            expected_edges.append((src.task_name, dst.task_name))

    assert len(wflow.sites) == 1
    for site in wflow.sites:
        site.scheduler = Scheduler.FLUX

    plugin = FluxPlugin(wflow)

    with tempfile.TemporaryDirectory() as tmpdir:
        plugin.configure(tmpdir, use_shell_launcher=True, exist_ok=True)

        assert "flux_plugin" in wflow.annotations
        assert "out_dir" in wflow.annotations["flux_plugin"]
        assert tmpdir == wflow.annotations["flux_plugin"]["out_dir"]
        assert "launcher_uses_shell" in wflow.annotations["flux_plugin"]
        assert wflow.annotations["flux_plugin"]["launcher_uses_shell"]

        io_buf = StringIO()

        with redirect_stdout(io_buf):
            plugin.execute(dry_run=True)

        expected_stdout = f"""
Launching workflow:
Dry run enabled. Would have run the following command:
{tmpdir}/launch.sh
""".strip()
        assert io_buf.getvalue().strip() == expected_stdout

        plugin.configure(tmpdir, use_shell_launcher=False, exist_ok=True)

        assert "flux_plugin" in wflow.annotations
        assert "out_dir" in wflow.annotations["flux_plugin"]
        assert tmpdir == wflow.annotations["flux_plugin"]["out_dir"]
        assert "launcher_uses_shell" in wflow.annotations["flux_plugin"]
        assert not wflow.annotations["flux_plugin"]["launcher_uses_shell"]

        io_buf = StringIO()

        with redirect_stdout(io_buf):
            plugin.execute(dry_run=True)

        expected_stdout = f"""
Launching workflow:
Dry run enabled. Would have run the following command:
{tmpdir}/launch.py
""".strip()
        assert io_buf.getvalue().strip() == expected_stdout

        plugin.configure(tmpdir, use_shell_launcher=True, exist_ok=True)

        io_buf = StringIO()

        with redirect_stdout(io_buf):
            plugin.execute(alternate_shell="/custom/dir/bash", dry_run=True)

        expected_stdout = f"""
Launching workflow:
Dry run enabled. Would have run the following command:
/custom/dir/bash {tmpdir}/launch.sh
""".strip()
        assert io_buf.getvalue().strip() == expected_stdout

        plugin.configure(tmpdir, use_shell_launcher=False, exist_ok=True)

        io_buf = StringIO()

        with redirect_stdout(io_buf):
            plugin.execute(
                alternate_python_interpreter="/custom/dir/python3", dry_run=True
            )

        expected_stdout = f"""
Launching workflow:
Dry run enabled. Would have run the following command:
/custom/dir/python3 {tmpdir}/launch.py
""".strip()
        assert io_buf.getvalue().strip() == expected_stdout

        curr_out_dir = plugin.out_dir
        plugin.out_dir = None
        with pytest.raises(RuntimeError):
            plugin.execute(dry_run=True)

        plugin.out_dir = curr_out_dir
        plugin.use_shell_launcher = None
        with pytest.raises(RuntimeError):
            plugin.execute(dry_run=True)


def test_flux_plugin_generate_w_config(
    pegasus_diamond_workflow, diamond_workflow_expected_config
):
    tasks, edges, _ = pegasus_diamond_workflow

    wflow = Workflow(
        "diamond_workflow",
        "An A4X-Orchestration-based implementation of the Pegasus Diamond workflow",
    )

    wflow.add_tasks(*tasks)

    expected_edges = []
    for src, dests in edges.items():
        for dst in dests:
            wflow.add_edge(src, dst)
            expected_edges.append((src.task_name, dst.task_name))

    plugin = FluxPlugin(wflow)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        config_file = tmpdir_path / "config.yaml"

        plugin.configure(tmpdir, a4x_config_out_file=config_file, exist_ok=True)

        yaml = YAML()

        with open(config_file, "r") as f:
            config = yaml.load(f)

        expected_config = diamond_workflow_expected_config.copy()
        expected_config["workflow"]["annotations"]["flux_plugin"]["out_dir"] = tmpdir

        assert dict(config) == expected_config

        with pytest.raises(TypeError):
            plugin.configure(tmpdir, a4x_config_out_file=10, exist_ok=True)


def test_flux_plugin_get_settings_from_wflow(pegasus_diamond_workflow):
    tasks, edges, _ = pegasus_diamond_workflow

    wflow = Workflow(
        "diamond_workflow",
        "An A4X-Orchestration-based implementation of the Pegasus Diamond workflow",
    )

    wflow.add_tasks(*tasks)

    expected_edges = []
    for src, dests in edges.items():
        for dst in dests:
            wflow.add_edge(src, dst)
            expected_edges.append((src.task_name, dst.task_name))

    plugin = FluxPlugin(wflow)

    assert plugin.get_plugin_settings_from_wflow() is None

    with tempfile.TemporaryDirectory() as tmpdir:
        plugin.configure(tmpdir, exist_ok=True)

        plugin_settings = plugin.get_plugin_settings_from_wflow()

        assert plugin_settings is not None
        assert "out_dir" in plugin_settings
        assert plugin_settings["out_dir"] == tmpdir
        assert "launcher_uses_shell" in plugin_settings
        assert plugin_settings["launcher_uses_shell"]
