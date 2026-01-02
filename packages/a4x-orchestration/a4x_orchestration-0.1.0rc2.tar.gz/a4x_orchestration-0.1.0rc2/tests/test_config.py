from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from a4x.orchestration.config.validation import validate_config_contents
from a4x.orchestration.workflow import Workflow
from jsonschema import ValidationError
from ruamel.yaml import YAML


def test_config_read(
    pegasus_diamond_workflow,
    diamond_workflow_config_fpath,
    diamond_workflow_expected_config,
):
    diamond_wflow_tasks, diamond_wflow_edges, _ = pegasus_diamond_workflow
    diamond_wflow = Workflow(
        "diamond_workflow",
        "An A4X-Orchestration-based implementation of the Pegasus Diamond workflow",
    )

    for src, dests in diamond_wflow_edges.items():
        for dst in dests:
            diamond_wflow.add_edge(src, dst)

    yaml = YAML()
    with open(diamond_workflow_config_fpath, "r") as f:
        loaded_config = yaml.load(f)

    validate_config_contents(loaded_config)

    assert dict(loaded_config) == diamond_workflow_expected_config

    wflow = Workflow.from_config(diamond_workflow_config_fpath)

    wflow_tasks = wflow.get_tasks_in_topological_order()
    diamond_wflow_tasks = diamond_wflow.get_tasks_in_topological_order()

    wflow_deps = {
        t.task_name: list(wflow.graph.successors(t.task_name)) for t in wflow_tasks
    }
    diamond_wflow_deps = {
        t.task_name: list(diamond_wflow.graph.successors(t.task_name))
        for t in diamond_wflow_tasks
    }

    assert wflow_tasks == diamond_wflow_tasks

    assert wflow_deps == diamond_wflow_deps


def test_config_read_diamond_dir_arg(diamond_workflow_dir_arg_fpath):
    _ = Workflow.from_config(diamond_workflow_dir_arg_fpath)


def test_config_read_bad_file_site(diamond_workflow_bad_file_site_fpath):
    with pytest.raises(KeyError):
        _ = Workflow.from_config(diamond_workflow_bad_file_site_fpath)


def test_config_read_bad_file_dir(diamond_workflow_bad_file_dir_fpath):
    with pytest.raises(KeyError):
        _ = Workflow.from_config(diamond_workflow_bad_file_dir_fpath)


def test_config_read_bad_file_site_dir_mix(
    diamond_workflow_bad_file_site_dir_mix_fpath,
):
    with pytest.raises(KeyError):
        _ = Workflow.from_config(diamond_workflow_bad_file_site_dir_mix_fpath)


def test_config_read_diamond_bad_arg_file_type(
    diamond_workflow_bad_arg_file_type_fpath,
):
    with pytest.raises(ValidationError):
        _ = Workflow.from_config(diamond_workflow_bad_arg_file_type_fpath)


def test_config_read_diamond_bad_arg_file_name(
    diamond_workflow_bad_arg_file_name_fpath,
):
    with pytest.raises(KeyError):
        _ = Workflow.from_config(diamond_workflow_bad_arg_file_name_fpath)


def test_config_read_diamond_bad_arg_dir_type(
    diamond_workflow_bad_arg_dir_type_fpath,
):
    with pytest.raises(ValidationError):
        _ = Workflow.from_config(diamond_workflow_bad_arg_dir_type_fpath)


def test_config_read_diamond_bad_arg_dir_site(
    diamond_workflow_bad_arg_dir_site_fpath,
):
    with pytest.raises(KeyError):
        _ = Workflow.from_config(diamond_workflow_bad_arg_dir_site_fpath)


def test_config_read_diamond_bad_arg_dir_dir(
    diamond_workflow_bad_arg_dir_dir_fpath,
):
    with pytest.raises(KeyError):
        _ = Workflow.from_config(diamond_workflow_bad_arg_dir_dir_fpath)


def test_config_read_diamond_bad_task_inputs(
    diamond_workflow_bad_task_inputs_fpath,
):
    with pytest.raises(KeyError):
        _ = Workflow.from_config(diamond_workflow_bad_task_inputs_fpath)


def test_config_read_diamond_bad_task_outputs(
    diamond_workflow_bad_task_outputs_fpath,
):
    with pytest.raises(KeyError):
        _ = Workflow.from_config(diamond_workflow_bad_task_outputs_fpath)


def test_config_read_lulesh_workflow(lulesh_workflow_config_fpath):
    _ = Workflow.from_config(lulesh_workflow_config_fpath)


def test_config_read_lulesh_bad_cwd_site(lulesh_workflow_config_bad_cwd_site_fpath):
    with pytest.raises(KeyError):
        _ = Workflow.from_config(lulesh_workflow_config_bad_cwd_site_fpath)


def test_config_read_lulesh_bad_cwd_dir(lulesh_workflow_config_bad_cwd_dir_fpath):
    with pytest.raises(KeyError):
        _ = Workflow.from_config(lulesh_workflow_config_bad_cwd_dir_fpath)


def test_config_read_lulesh_bad_cwd_dir_no_site(
    lulesh_workflow_config_bad_cwd_dir_no_site_fpath,
):
    with pytest.raises(ValidationError):
        _ = Workflow.from_config(lulesh_workflow_config_bad_cwd_dir_no_site_fpath)


def test_config_read_lulesh_bad_resource_keys(
    lulesh_workflow_config_bad_resource_keys_fpath,
):
    with pytest.raises(KeyError):
        _ = Workflow.from_config(lulesh_workflow_config_bad_resource_keys_fpath)


def test_config_read_lulesh_bad_task_site(
    lulesh_workflow_config_bad_task_site_fpath,
):
    with pytest.raises(KeyError):
        _ = Workflow.from_config(lulesh_workflow_config_bad_task_site_fpath)


def test_config_write(maestro_lulesh_workflow, pegasus_diamond_workflow):
    _, edges, _ = maestro_lulesh_workflow
    lulesh_wflow = Workflow(
        "maestro_lulesh_workflow_write_test",
        "This is the Maestro Lulesh workflow representation for the config write test",
    )

    for src, dests in edges.items():
        for dst in dests:
            lulesh_wflow.add_edge(src, dst)

    _, edges, _ = pegasus_diamond_workflow

    diamond_wflow = Workflow(
        "diamond_workflow_write_test",
        "This is the Diamond workflow representation for the config write test",
    )

    for src, dests in edges.items():
        for dst in dests:
            diamond_wflow.add_edge(src, dst)

    with TemporaryDirectory() as tmpdir:
        lulesh_config_path = Path(tmpdir) / "lulesh_config.yaml"

        lulesh_wflow.to_config(lulesh_config_path)

        loaded_wflow = Workflow.from_config(lulesh_config_path)

        wflow_tasks = lulesh_wflow.get_tasks_in_topological_order()
        loaded_wflow_tasks = loaded_wflow.get_tasks_in_topological_order()

        wflow_deps = {
            t.task_name: list(lulesh_wflow.graph.successors(t.task_name))
            for t in wflow_tasks
        }
        loaded_wflow_deps = {
            t.task_name: list(loaded_wflow.graph.successors(t.task_name))
            for t in loaded_wflow_tasks
        }

        assert wflow_tasks == loaded_wflow_tasks

        assert wflow_deps == loaded_wflow_deps

        diamond_config_path = Path(tmpdir) / "diamond_config.yaml"

        diamond_wflow.to_config(diamond_config_path)

        loaded_wflow = Workflow.from_config(diamond_config_path)

        wflow_tasks = diamond_wflow.get_tasks_in_topological_order()
        loaded_wflow_tasks = loaded_wflow.get_tasks_in_topological_order()

        wflow_deps = {
            t.task_name: list(diamond_wflow.graph.successors(t.task_name))
            for t in wflow_tasks
        }
        loaded_wflow_deps = {
            t.task_name: list(loaded_wflow.graph.successors(t.task_name))
            for t in loaded_wflow_tasks
        }

        assert wflow_tasks == loaded_wflow_tasks

        assert wflow_deps == loaded_wflow_deps
