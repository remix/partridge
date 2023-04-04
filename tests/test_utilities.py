import io
import networkx as nx
import pytest

import numpy as np
import pandas as pd
from partridge.utilities import (
    detect_encoding,
    empty_df,
    remove_node_attributes,
    setwrap,
)


def test_setwrap():
    assert setwrap("a") == {"a"}
    assert setwrap(["a"]) == {"a"}
    assert setwrap({"a"}) == {"a"}
    assert setwrap({1}) == {"1"}
    assert setwrap(1) == {"1"}


def test_remove_node_attributes():
    G = nx.Graph()
    G.add_node(1, label="foo", hello="world")
    G.add_node(2, label="bar", welcome=1)

    X = remove_node_attributes(G, "label")
    Y = remove_node_attributes(G, ["label", "welcome"])

    assert G.nodes[1] == {"label": "foo", "hello": "world"}
    assert G.nodes[2] == {"label": "bar", "welcome": 1}

    assert id(X) != id(G)
    assert X.nodes[1] == {"hello": "world"}
    assert X.nodes[2] == {"welcome": 1}

    assert id(Y) != id(G)
    assert Y.nodes[1] == {"hello": "world"}
    assert Y.nodes[2] == {}


def test_empty_df():
    actual = empty_df(["foo", "bar"])

    expected = pd.DataFrame(
        {"foo": [], "bar": []}, columns=["foo", "bar"], dtype=str
    )

    assert actual.equals(expected)


@pytest.mark.parametrize(
    "test_string,encoding",
    [
        (b"abcde", "utf-8"),  # straight up ascii is a subset of unicode
        (b"Eyjafjallaj\xc3\xb6kull", "utf-8"),  # actual unicode
        (b"\xC4pple", "cp037"),  # non-unicode, ISO characterset
    ],
)
def test_detect_encoding(test_string, encoding):
    assert detect_encoding(io.BytesIO(test_string)) == encoding
