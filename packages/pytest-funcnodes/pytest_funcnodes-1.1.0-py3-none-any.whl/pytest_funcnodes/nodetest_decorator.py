from typing import Callable, List, Union, Type
import funcnodes_core as fn
import functools
import pytest
import asyncio


def nodetest(node: Union[None, List[Type[fn.Node]], Type[fn.Node]] = None):
    """Decorator for async node tests.
    This decorator automatically applies:
    - The 'nodetest' marker, so that tests can be filtered via --nodetests-only.
    - The 'pytest.mark.asyncio' marker so that the test is run in an async event loop.
    """

    if node is None:
        node = []
    elif not isinstance(node, list):
        node = [node]

    try:
        invalid = [
            n for n in node if not isinstance(n, type) or not issubclass(n, fn.Node)
        ]
    except TypeError:
        invalid = node

    if invalid:
        raise TypeError("node must be a subclass of funcnodes_core.Node")

    def decorator(func):
        # check if func is a coroutine function
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("func must be a coroutine function")

        @pytest.mark.nodetest(nodes=node)
        @pytest.mark.asyncio(loop_scope="function")
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def funcnodes_test(func: Callable = None, **decorator_kwargs):
    """Decorator for async node tests.
    This decorator automatically applies:
    - The 'nodetest' marker, so that tests can be filtered via --nodetests-only.
    - The 'pytest.mark.asyncio' marker so that the test is run in an async event loop.
    """

    if func is None:

        def _inner_decorator(func: Callable):
            return funcnodes_test(func, **decorator_kwargs)

        return _inner_decorator

    # check if func is a coroutine function
    if not asyncio.iscoroutinefunction(func):

        @pytest.mark.funcnodes_test(**decorator_kwargs)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    @pytest.mark.funcnodes_test(**decorator_kwargs)
    @pytest.mark.asyncio(loop_scope="function")
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)

    return wrapper
