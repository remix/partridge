from cchardet import UniversalDetector
import numpy as np
from pandas.core.common import flatten


def setwrap(value):
    """
    Returns a flattened and stringified set from the given object or iterable.

    For use in public functions which accept argmuents or kwargs that can be
    one object or a list of objects.
    """
    return set(map(np.unicode, set(flatten([value]))))


def remove_node_attributes(G, attributes):
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


def detect_encoding(f, limit=2500):
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
