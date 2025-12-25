from pytest_funcnodes import nodetest, funcnodes_test
from pathlib import Path
import tempfile
import logging


@nodetest(None)
async def test_config_dir():
    import funcnodes_core

    config_dir: Path = funcnodes_core.config.get_config_dir()
    # make sure config dir is a temporary directory
    assert config_dir.is_dir()
    # test if the config dir is a subdirectory of the temp dir
    assert config_dir.parent == Path(tempfile.gettempdir())


@nodetest(None)
async def test_logger():
    import funcnodes_core

    logger = funcnodes_core._logging.FUNCNODES_LOGGER

    # make sure no logging.FileHandler is present
    assert not any(
        isinstance(handler, logging.FileHandler) for handler in logger.handlers
    )

    assert logger.level == logging.DEBUG


@funcnodes_test
async def test_config_dir_funcnodes_test():
    import funcnodes_core

    config_dir: Path = funcnodes_core.config.get_config_dir()
    # make sure config dir is a temporary directory
    assert config_dir.is_dir()
    # test if the config dir is a subdirectory of the temp dir
    assert config_dir.parent == Path(tempfile.gettempdir())


@funcnodes_test
async def test_logger_funcnodes_test():
    import funcnodes_core

    logger = funcnodes_core._logging.FUNCNODES_LOGGER
    assert not any(
        isinstance(handler, logging.FileHandler) for handler in logger.handlers
    )
    assert logger.level == logging.DEBUG


@funcnodes_test
async def test_confirg_dir_in_temp():
    import funcnodes_core

    config_dir: Path = funcnodes_core.config.get_config_dir()
    # make sure config dir is a temporary directory
    assert config_dir.is_dir()
    # test if the config dir is a subdirectory of the temp dir
    assert config_dir.parent == Path(tempfile.gettempdir())


@funcnodes_test
def test_assert_config_without_coroutine():
    import funcnodes_core

    config_dir: Path = funcnodes_core.config.get_config_dir()
    # make sure config dir is a temporary directory
    assert config_dir.is_dir()
    # test if the config dir is a subdirectory of the temp dir
    assert config_dir.parent == Path(tempfile.gettempdir())


# test same functions A and B to make sure they use different config dirs
@funcnodes_test
def test_assert_config_without_conflict_A():
    import funcnodes_core

    config_dir: Path = funcnodes_core.config.get_config_dir()
    # make sure config dir is a temporary directory
    assert config_dir.is_dir()
    # test if the config dir is a subdirectory of the temp dir
    unexpected_file = config_dir / "UNEXPECTED_FILE.txt"
    assert not unexpected_file.exists()
    # make the file
    unexpected_file.touch()
    assert unexpected_file.exists()


@funcnodes_test
def test_assert_config_without_conflict_B():
    import funcnodes_core

    config_dir: Path = funcnodes_core.config.get_config_dir()
    # make sure config dir is a temporary directory
    assert config_dir.is_dir()
    # test if the config dir is a subdirectory of the temp dir
    unexpected_file = config_dir / "UNEXPECTED_FILE.txt"
    assert not unexpected_file.exists()
    # make the file
    unexpected_file.touch()
    assert unexpected_file.exists()
