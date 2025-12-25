from functools import cached_property

import networkx as nx
from networkx.classes.graph import _CachedPropertyResetterAdj


class VergeGraph:
    """
    This is the main graph for generating a VergeGraph
    """

    _adj = _CachedPropertyResetterAdj()
    adjlist_outer_dict_factory = dict

    def __init__(self):
        self.graph = nx.Graph()
        self._adj = self.adjlist_outer_dict_factory()

    def add_node(self, value: int) -> None:
        """This method is used to add a node"""
        self.graph.add_node(value)

    def add_edge(self, src: int, dest: int) -> None:
        """This method is used to add an edge"""
        self.graph.add_edge(src, dest)

    def clear(self) -> None:
        """This is used to clear the graph after creation"""
        self.graph.clear()

    def get_nodes(self) -> nx.classes.graph.NodeView:
        """Get the nodes in the graph"""
        return self.graph.nodes

    def get_edges(self) -> nx.classes.graph.EdgeView:
        """Get the edges in the graph"""
        return self.graph.edges

    def __len__(self) -> int:
        """Gets the length of the nodes"""
        return self.graph.__len__()

    def __iter__(self):
        return self.graph.__iter__()

    def is_directed(self):
        return self.graph.is_directed()

    def is_multigraph(self):
        return self.graph.is_multigraph()

    @cached_property
    def edges(self):
        return self.graph.edges()

    @cached_property
    def nodes(self):
        return self.graph.nodes()
