import networkx as nx

from partridge.utilities import setwrap, remove_node_attributes


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
