from typing import List, Type, Optional
import funcnodes_core as fn


def all_nodes_tested(
    tested_nodes: List[Type[fn.Node]],
    shelf: fn.Shelf,
    ignore: Optional[List[Type[fn.Node]]] = None,
):
    nodes = fn.flatten_shelf(shelf)[0]
    if ignore is None:
        ignore = []

    ignore_nodes = []
    for n in ignore:
        if isinstance(n, type) and issubclass(n, fn.Node):
            ignore_nodes.append(n)
        elif isinstance(n, fn.Shelf):
            ignore_nodes.extend(fn.flatten_shelf(n)[0])
        else:
            raise TypeError(
                f"ignore must be a subclass of funcnodes_core.Node or a Shelf not {type(n)}"
            )

    untested_nodes = [n for n in nodes if n not in tested_nodes]
    untested_nodes = [n for n in untested_nodes if n not in ignore_nodes]
    assert not untested_nodes, "Untested nodes:\n" + "\n".join(
        str(n) for n in untested_nodes
    )
