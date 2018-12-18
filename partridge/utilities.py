from typing import Any, Dict, Iterable, Optional, Set, BinaryIO, Union

from cchardet import UniversalDetector
import networkx as nx
import numpy as np
import pandas as pd
from pandas.core.common import flatten


def setwrap(value: Any) -> Set[str]:
    """
    Returns a flattened and stringified set from the given object or iterable.

    For use in public functions which accept argmuents or kwargs that can be
    one object or a list of objects.
    """
    return set(map(str, set(flatten([value]))))


def remove_node_attributes(G: nx.DiGraph, attributes: Union[str, Iterable[str]]):
    """
    Return a copy of the graph with the given attributes
    deleted from all nodes.
    """
    G = G.copy()
    for _, data in G.nodes(data=True):
        for attribute in setwrap(attributes):
            if attribute in data:
                del data[attribute]
    return G


def detect_encoding(f: BinaryIO, limit: int = 2500) -> str:
    u = UniversalDetector()
    for line in f:
        u.feed(line)

        limit -= 1
        if u.done or limit < 1:
            break

    u.close()
    if u.result["encoding"].lower() == "ascii":
        return "utf-8"
    else:
        return u.result["encoding"]


def empty_df(columns: Optional[Iterable[str]] = None) -> pd.DataFrame:
    columns = [] if columns is None else columns
    empty: Dict = {col: [] for col in columns}
    return pd.DataFrame(empty, columns=columns, dtype=np.unicode)
