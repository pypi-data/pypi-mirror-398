import warnings
from pathlib import Path
import tempfile
import shutil

import pytest

from funcnodes_core import config as fnconfig
from funcnodes_core.utils.deprecations import FuncNodesDeprecationWarning
import funcnodes_core as fn
from pytest_funcnodes import testingsystem

from pytest_funcnodes import (
    all_nodes_tested,
    get_in_test,
    set_in_test,
    setup,
    teardown,
    test_context,
)


def test_set_in_test_enables_warning_errors_and_resets():
    test_file: Path | None = None
    try:
        with warnings.catch_warnings():
            with pytest.raises(FuncNodesDeprecationWarning):
                set_in_test(
                    no_prefix=True,
                    clear=True,
                    fail_on_warnings=(FuncNodesDeprecationWarning,),
                )
                warnings.warn("boom", FuncNodesDeprecationWarning)

        config_dir = fnconfig.get_config_dir()
        assert get_in_test()
        test_file = config_dir / "leftover.txt"
        test_file.write_text("data")
    finally:
        teardown()

    assert test_file is not None
    assert test_file.exists()

    try:
        set_in_test(no_prefix=True, clear=True, fail_on_warnings=())
        assert get_in_test()
        assert not test_file.exists()
    finally:
        teardown()


def test_set_in_test_early_return_when_already_flagged(tmp_path):
    original_base = fnconfig._BASE_CONFIG_DIR
    original_in_test = testingsystem._IN_NODE_TEST
    try:
        # simulate already-in-test state pointing to a temp dir
        fnconfig._BASE_CONFIG_DIR = Path(tempfile.gettempdir()) / "funcnodes_test"
        testingsystem._IN_NODE_TEST = True
        fnconfig.reload(fnconfig._BASE_CONFIG_DIR)

        before_dir = fnconfig.get_config_dir()
        set_in_test(no_prefix=True, clear=True)
        after_dir = fnconfig.get_config_dir()
        assert before_dir == after_dir
    finally:
        testingsystem._IN_NODE_TEST = original_in_test
        fnconfig._BASE_CONFIG_DIR = original_base
        fnconfig.reload(original_base)


def test_set_in_test_handles_unlistable_warning_input():
    try:
        set_in_test(
            no_prefix=True, clear=True, fail_on_warnings=FuncNodesDeprecationWarning
        )
        with pytest.raises(FuncNodesDeprecationWarning):
            warnings.warn("boom", FuncNodesDeprecationWarning)
    finally:
        teardown()


def test_set_in_test_clear_handles_existing_dir_with_open_file(tmp_path):
    original_base = fnconfig._BASE_CONFIG_DIR
    held_file = None
    try:
        base_dir = Path(tempfile.gettempdir()) / "funcnodes_test"
        base_dir.mkdir(parents=True, exist_ok=True)
        held_file = open(base_dir / "held.txt", "w")  # noqa: SIM115
        held_file.write("locked")
        held_file.flush()

        set_in_test(no_prefix=True, clear=True)
        assert fnconfig.get_config_dir().exists()
    finally:
        teardown()
        if held_file:
            held_file.close()
        shutil.rmtree(
            Path(tempfile.gettempdir()) / "funcnodes_test", ignore_errors=True
        )
        fnconfig._BASE_CONFIG_DIR = original_base
        fnconfig.reload(original_base)


def test_set_in_test_writes_custom_config():
    try:
        set_in_test(
            no_prefix=True,
            clear=True,
            config={"env_dir": "custom-env"},
            fail_on_warnings=(),
        )
        cfg = fnconfig.get_config()
        assert cfg["env_dir"].endswith("custom-env")
    finally:
        teardown()


def test_setup_raises_when_config_cannot_be_set():
    original_base = fnconfig._BASE_CONFIG_DIR
    original_in_test = testingsystem._IN_NODE_TEST
    try:
        bad_dir = Path(__file__).parent / "nontemp_config_dir"
        testingsystem._IN_NODE_TEST = True
        fnconfig._BASE_CONFIG_DIR = bad_dir
        fnconfig.reload(fnconfig._BASE_CONFIG_DIR)
        with pytest.raises(RuntimeError, match="Failed to set in test mode"):
            setup(raise_if_already_in_test=False, no_prefix=True)
    finally:
        testingsystem._IN_NODE_TEST = original_in_test
        fnconfig._BASE_CONFIG_DIR = original_base
        fnconfig.reload(original_base)
        shutil.rmtree(bad_dir, ignore_errors=True)


def test_test_context_raises_when_config_not_in_tempdir():
    original_base = fnconfig._BASE_CONFIG_DIR
    try:
        bad_dir = Path(__file__).parent / "nontemp_config_dir"
        fnconfig._BASE_CONFIG_DIR = bad_dir
        fnconfig.reload(bad_dir)
        testingsystem._IN_NODE_TEST = True

        context = test_context(no_prefix=True, clear=False)
        context._config_dir = bad_dir
        with pytest.raises(RuntimeError, match="Failed to set in test mode"):
            with context:
                pass
    finally:
        testingsystem._IN_NODE_TEST = False
        fnconfig._BASE_CONFIG_DIR = original_base
        fnconfig.reload(original_base)
        shutil.rmtree(bad_dir, ignore_errors=True)


def test_setup_detects_existing_test_mode():
    try:
        set_in_test(no_prefix=True)
        with pytest.raises(RuntimeError):
            setup(raise_if_already_in_test=True, no_prefix=True)
    finally:
        teardown()


def test_test_context_cleans_and_marks_state():
    config_dir: Path | None = None
    with test_context(no_prefix=True, clear=True) as ctx:
        assert get_in_test()
        config_dir = fnconfig.get_config_dir()
        assert config_dir.parent == Path(tempfile.gettempdir())
        assert ctx._config_dir == config_dir  # noqa: SLF001
        assert config_dir.exists()
    assert not get_in_test()
    assert config_dir is not None
    assert not config_dir.exists()


def test_all_nodes_tested_invalid_ignore_raises():
    shelf = fn.Shelf(name="Empty", nodes=[])
    with pytest.raises(TypeError):
        all_nodes_tested([], shelf, ignore=["not-a-node"])
