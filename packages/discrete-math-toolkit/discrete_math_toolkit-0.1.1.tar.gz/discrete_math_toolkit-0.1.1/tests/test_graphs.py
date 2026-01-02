"""Tests for the graphs module."""

import pytest
from discrete_math.graphs import Graph, create_complete_graph, create_cycle_graph


def test_graph_creation():
    """Test basic graph creation."""
    g = Graph()
    g.add_vertex(1)
    g.add_vertex(2)
    g.add_edge(1, 2)
    
    assert 1 in g.get_vertices()
    assert 2 in g.get_vertices()
    assert (1, 2) in g.get_edges() or (2, 1) in g.get_edges()


def test_directed_graph():
    """Test directed graph."""
    g = Graph(directed=True)
    g.add_edge(1, 2)
    
    assert (1, 2) in g.get_edges()
    assert (2, 1) not in g.get_edges()


def test_bfs():
    """Test breadth-first search."""
    g = Graph()
    g.add_edge(1, 2)
    g.add_edge(2, 3)
    g.add_edge(1, 3)
    
    result = g.bfs(1)
    assert len(result) == 3
    assert result[0] == 1


def test_dfs():
    """Test depth-first search."""
    g = Graph()
    g.add_edge(1, 2)
    g.add_edge(2, 3)
    g.add_edge(1, 3)
    
    result = g.dfs(1)
    assert len(result) == 3
    assert result[0] == 1


def test_shortest_path():
    """Test shortest path finding."""
    g = Graph()
    g.add_edge(1, 2, 1)
    g.add_edge(2, 3, 1)
    g.add_edge(1, 3, 5)
    
    path, distance = g.shortest_path(1, 3)
    assert distance == 2  # Via vertex 2


def test_is_connected():
    """Test connectivity checking."""
    g = Graph()
    g.add_edge(1, 2)
    g.add_edge(2, 3)
    
    assert g.is_connected()


def test_has_cycle():
    """Test cycle detection."""
    g = Graph()
    g.add_edge(1, 2)
    g.add_edge(2, 3)
    g.add_edge(3, 1)
    
    assert g.has_cycle()


def test_is_bipartite():
    """Test bipartite checking."""
    g = Graph()
    g.add_edge(1, 2)
    g.add_edge(2, 3)
    
    assert g.is_bipartite()


def test_complete_graph():
    """Test complete graph creation."""
    g = create_complete_graph(4)
    assert len(g.get_edges()) == 6  # K4 has 6 edges


def test_cycle_graph():
    """Test cycle graph creation."""
    g = create_cycle_graph(5)
    assert len(g.get_edges()) == 5
