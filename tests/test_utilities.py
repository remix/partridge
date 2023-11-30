import io
import networkx as nx
import pytest

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


def test_detect_encoding():
    # straight up ascii is a subset of unicode
    assert detect_encoding(io.BytesIO(b"abcde")) == "utf-8"

    # actual unicode
    assert detect_encoding(io.BytesIO(b"Eyjafjallaj\xc3\xb6kull")) == "utf-8"

    # non-unicode, ISO characterset
    #
    # (Note: we don't assert a specific characterset, because we don't want
    # tests to break as changes are made in charset-normalizer. See:
    # https://github.com/remix/partridge/pull/84)
    enc = detect_encoding(io.BytesIO(b"\xC4pple"))
    assert enc and enc != "utf-8"
