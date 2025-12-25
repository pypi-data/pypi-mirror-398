import logging
import os
from typing import List, Optional
import warnings
from funcnodes_core import config as fnconfig
from funcnodes_core._logging import (
    FUNCNODES_LOGGER,
    _update_logger,
    set_logging_dir,
    _update_logger_handlers,
)  # noqa C0415 # pylint: disable=import-outside-toplevel

from pathlib import Path
import tempfile
import shutil
import uuid

from funcnodes_core.utils.deprecations import FuncNodesDeprecationWarning

_IN_NODE_TEST = False


def get_in_test() -> bool:
    return (
        _IN_NODE_TEST
        and Path(tempfile.gettempdir()) in fnconfig.get_config_dir().parents
    )


def set_in_test(
    *,
    clear: bool = True,
    no_prefix: bool = False,
    prefix: Optional[str] = None,
    config: Optional[fnconfig.ConfigType] = None,
    fail_on_warnings: Optional[List[Warning]] = None,
    disable_file_handler: bool = True,
):
    """
    Sets the configuration to be in test mode.

    Returns:
      None

    Examples:
      >>> set_in_test()
    """
    global _IN_NODE_TEST
    try:
        if _IN_NODE_TEST:  # no change
            return
        _IN_NODE_TEST = True

        if fail_on_warnings is None:
            fail_on_warnings = [FuncNodesDeprecationWarning]
        if fail_on_warnings:
            if not isinstance(fail_on_warnings, list):
                try:
                    fail_on_warnings = list(fail_on_warnings)
                except Exception:
                    fail_on_warnings = [fail_on_warnings]

            for w in fail_on_warnings:
                # prepend so that existing ignore/default filters do not override
                warnings.filterwarnings("error", category=w, append=False)

        fn = "funcnodes_test"

        if not no_prefix:
            if prefix is None:
                prefix = f"_{os.getpid()}_{uuid.uuid4().hex}"
            else:
                prefix = f"_{prefix}"
            fn += prefix

        fnconfig._BASE_CONFIG_DIR = Path(tempfile.gettempdir()) / fn
        if clear:
            if fnconfig._BASE_CONFIG_DIR.exists():
                try:
                    shutil.rmtree(fnconfig._BASE_CONFIG_DIR)
                except Exception:
                    pass

        if config:
            fnconfig.write_config(fnconfig._BASE_CONFIG_DIR / "config.json", config)

        fnconfig.reload(fnconfig._BASE_CONFIG_DIR)

        if disable_file_handler:
            fnconfig.update_config({"logging": {"handler": {"file": False}}})
        fnconfig.update_config({"logging": {"level": "DEBUG"}})
        # import here to avoid circular import
        set_logging_dir(os.path.join(fnconfig._BASE_CONFIG_DIR, "logs"))
        _update_logger(FUNCNODES_LOGGER)

    finally:
        fnconfig._CONFIG_CHANGED = (
            True  # we change this to true, that the config is reloaded
        )


def setup(
    raise_if_already_in_test: bool = True,
    config: Optional[fnconfig.ConfigType] = None,
    fail_on_warnings: Optional[List[Warning]] = None,
    clear: bool = True,
    no_prefix: bool = False,
    prefix: Optional[str] = None,
    disable_file_handler: bool = True,
):
    if raise_if_already_in_test and get_in_test():
        raise RuntimeError("Already in test mode")
    if not get_in_test():
        set_in_test(
            config=config,
            fail_on_warnings=fail_on_warnings,
            clear=clear,
            no_prefix=no_prefix,
            prefix=prefix,
            disable_file_handler=disable_file_handler,
        )
    if not get_in_test():
        raise RuntimeError("Failed to set in test mode")
    logging.basicConfig(level=logging.DEBUG)
    _update_logger_handlers(FUNCNODES_LOGGER)


def teardown():
    """This can be called after each test, which will do a little cleanup."""
    global _IN_NODE_TEST
    # remove all from the "funcnodes" logger

    # get all logger that start with "funcnodes."

    loggers = [
        name
        for name in logging.root.manager.loggerDict
        if name.startswith("funcnodes.")
    ] + ["funcnodes"]

    loggers = [logging.getLogger(name) for name in loggers]

    for logger in loggers:
        # handlers have to be accessed as a list,
        # because they are removed during iteration
        for handler in list(logger.handlers):
            handler.close()

    # remove all registered nodes
    from funcnodes_core.node import REGISTERED_NODES

    REGISTERED_NODES.clear()

    _IN_NODE_TEST = False


class test_context:
    def __init__(
        self,
        config: Optional[fnconfig.ConfigType] = None,
        fail_on_warnings: Optional[List[Warning]] = None,
        clear: bool = True,
        no_prefix: bool = False,
        disable_file_handler: bool = True,
        prefix: Optional[str] = None,
    ):
        self._config_dir = None
        self._config = config
        self._fail_on_warnings = fail_on_warnings
        self._clear = clear
        self._no_prefix = no_prefix
        self._disable_file_handler = disable_file_handler
        self._prefix = prefix

    def __enter__(self):
        setup(
            config=self._config,
            fail_on_warnings=self._fail_on_warnings,
            clear=self._clear,
            no_prefix=self._no_prefix,
            prefix=self._prefix,
            disable_file_handler=self._disable_file_handler,
        )
        self._config_dir = fnconfig.get_config_dir()
        if Path(tempfile.gettempdir()) not in self._config_dir.parents:
            raise RuntimeError(f"Config dir is not in tempdir: {self._config_dir}")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        teardown()
        if self._config_dir is not None:
            # remove dir even if not empty
            shutil.rmtree(self._config_dir)
