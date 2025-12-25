# pytest-funcnodes

`pytest_funcnodes` is the maintained pytest plugin for FuncNodes modules. It replaces the legacy `TestAllNodesBase` harness by supplying decorators, fixtures, and coverage helpers that keep the runtime isolated and guarantee every node is exercised.

## Key Features

- `@pytest_funcnodes.nodetest`
  Marks async node tests, injects `pytest.mark.asyncio`, and records which node classes were covered. **Every** test that executes a node must use this decorator so the plugin can reset registries and track coverage.

- `@pytest_funcnodes.funcnodes_test`
  Wraps sync or async tests that interact with `funcnodes_core` / `funcnodes` state (loading shelves, running flows, tweaking config). It toggles the same isolated `test_context` used for node tests, disabling file loggers and pointing configs at a per-test temp directory.

- Autouse fixtures & CLI flag
  The plugin ships `nodetest_setup_teardown` / `funcnodes_test_setup_teardown` fixtures plus `--nodetests-only`, letting you run just node suites while keeping isolation guarantees.

- Coverage helper
  `pytest_funcnodes.all_nodes_tested(all_nodes, shelf, ignore=...)` flattens shelves and asserts that every exported node class was covered by a `@nodetest`.

## Installation

```bash
uv add pytest-funcnodes
# or
pip install pytest_funcnodes
```

## Usage

### 1. Mark node tests

```python
import pytest_funcnodes
import funcnodes as fn

@fn.NodeDecorator("demo.concat")
def concat(a: str, b: str) -> str:
    return a + b

@pytest_funcnodes.nodetest(concat)
async def test_concat():
    node = concat()
    node["a"] = "foo"
    node["b"] = "bar"
    await node
    assert node["out"].value == "foobar"
```

### 2. Mark runtime/integration tests

```python
import pytest_funcnodes
from funcnodes_core import config as fnconfig

@pytest_funcnodes.funcnodes_test
def test_config_uses_temp_dir():
    cfg_dir = fnconfig.get_config_dir()
    assert cfg_dir.name.startswith("funcnodes_test_")
```

### 3. Enforce shelf coverage

```python
from pytest_funcnodes import all_nodes_tested
import funcnodes_basic as fnmodule

def test_all_nodes_tested(all_nodes):
    all_nodes_tested(all_nodes, fnmodule.NODE_SHELF, ignore=[])
```

This assertion fails with a list of missing node classes if any exported node lacks a `@nodetest`.

### 4. CLI workflow

- `pytest --nodetests-only` filters the run down to node suites.
- The session fixture prints `Session fixture setup/teardown`, confirming the plugin activated.
- No manual calls to `funcnodes_core.testing.setup()` / `teardown()` are required—the fixtures enter and exit `test_context` automatically.

## Runtime Isolation Details

`test_context` (see `pytest_funcnodes/testingsystem.py`) rewrites the FuncNodes config directory into a temp folder per PID, clears leftovers between tests, disables file handlers, upgrades selected warnings (e.g., `FuncNodesDeprecationWarning`) to errors, and removes the temp directory on exit. This means:

- Tests never leak global registry state (`funcnodes_core.node.REGISTERED_NODES` is cleared after each run).
- File logs stay inside the temp dir and are removed after teardown.
- Fail-fast behavior surfaces deprecated APIs that still fire warnings.

Always prefer the provided decorators over manual setup so these safeguards remain effective.
