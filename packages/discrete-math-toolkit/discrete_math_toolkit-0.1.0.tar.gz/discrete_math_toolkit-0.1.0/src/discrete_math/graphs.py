"""
Graphs Module
=============

Provides graph data structures and algorithms for graph theory operations.
"""

from typing import Dict, Set, List, Tuple, Optional
from collections import deque, defaultdict
import heapq


class Graph:
    """
    Graph data structure supporting both directed and undirected graphs.
    """
    
    def __init__(self, directed: bool = False):
        """
        Initialize a graph.
        
        Args:
            directed: If True, creates a directed graph; otherwise undirected
        """
        self.directed = directed
        self.adjacency_list: Dict[any, Set] = defaultdict(set)
        self.weights: Dict[Tuple, float] = {}
    
    def add_vertex(self, vertex):
        """Add a vertex to the graph."""
        if vertex not in self.adjacency_list:
            self.adjacency_list[vertex] = set()
    
    def add_edge(self, u, v, weight: float = 1.0):
        """
        Add an edge to the graph.
        
        Args:
            u: Source vertex
            v: Destination vertex
            weight: Edge weight (default: 1.0)
        """
        self.add_vertex(u)
        self.add_vertex(v)
        self.adjacency_list[u].add(v)
        self.weights[(u, v)] = weight
        
        if not self.directed:
            self.adjacency_list[v].add(u)
            self.weights[(v, u)] = weight
    
    def remove_vertex(self, vertex):
        """Remove a vertex and all its edges from the graph."""
        if vertex in self.adjacency_list:
            # Remove all edges to this vertex
            for v in self.adjacency_list:
                self.adjacency_list[v].discard(vertex)
                if (v, vertex) in self.weights:
                    del self.weights[(v, vertex)]
            
            # Remove edges from this vertex
            for neighbor in self.adjacency_list[vertex]:
                if (vertex, neighbor) in self.weights:
                    del self.weights[(vertex, neighbor)]
            
            # Remove vertex itself
            del self.adjacency_list[vertex]
    
    def remove_edge(self, u, v):
        """Remove an edge from the graph."""
        if u in self.adjacency_list:
            self.adjacency_list[u].discard(v)
            if (u, v) in self.weights:
                del self.weights[(u, v)]
        
        if not self.directed and v in self.adjacency_list:
            self.adjacency_list[v].discard(u)
            if (v, u) in self.weights:
                del self.weights[(v, u)]
    
    def get_vertices(self) -> Set:
        """Return set of all vertices."""
        return set(self.adjacency_list.keys())
    
    def get_edges(self) -> Set[Tuple]:
        """Return set of all edges."""
        edges = set()
        for u in self.adjacency_list:
            for v in self.adjacency_list[u]:
                if self.directed or (v, u) not in edges:
                    edges.add((u, v))
        return edges
    
    def get_neighbors(self, vertex) -> Set:
        """Return set of neighbors for a vertex."""
        return self.adjacency_list.get(vertex, set())
    
    def degree(self, vertex) -> int:
        """Return degree of a vertex."""
        if self.directed:
            return self.in_degree(vertex) + self.out_degree(vertex)
        return len(self.adjacency_list.get(vertex, set()))
    
    def in_degree(self, vertex) -> int:
        """Return in-degree of a vertex (for directed graphs)."""
        count = 0
        for u in self.adjacency_list:
            if vertex in self.adjacency_list[u]:
                count += 1
        return count
    
    def out_degree(self, vertex) -> int:
        """Return out-degree of a vertex (for directed graphs)."""
        return len(self.adjacency_list.get(vertex, set()))
    
    def bfs(self, start) -> List:
        """
        Breadth-first search traversal.
        
        Args:
            start: Starting vertex
        
        Returns:
            List of vertices in BFS order
        """
        if start not in self.adjacency_list:
            return []
        
        visited = set()
        queue = deque([start])
        result = []
        
        while queue:
            vertex = queue.popleft()
            if vertex not in visited:
                visited.add(vertex)
                result.append(vertex)
                
                for neighbor in self.adjacency_list[vertex]:
                    if neighbor not in visited:
                        queue.append(neighbor)
        
        return result
    
    def dfs(self, start) -> List:
        """
        Depth-first search traversal.
        
        Args:
            start: Starting vertex
        
        Returns:
            List of vertices in DFS order
        """
        if start not in self.adjacency_list:
            return []
        
        visited = set()
        result = []
        
        def dfs_recursive(vertex):
            visited.add(vertex)
            result.append(vertex)
            
            for neighbor in self.adjacency_list[vertex]:
                if neighbor not in visited:
                    dfs_recursive(neighbor)
        
        dfs_recursive(start)
        return result
    
    def is_connected(self) -> bool:
        """Check if the graph is connected."""
        if not self.adjacency_list:
            return True
        
        start = next(iter(self.adjacency_list))
        visited = set(self.bfs(start))
        return len(visited) == len(self.adjacency_list)
    
    def shortest_path(self, start, end) -> Tuple[List, float]:
        """
        Find shortest path using Dijkstra's algorithm.
        
        Args:
            start: Starting vertex
            end: Ending vertex
        
        Returns:
            Tuple of (path as list, total distance)
        """
        if start not in self.adjacency_list or end not in self.adjacency_list:
            return ([], float('inf'))
        
        distances = {v: float('inf') for v in self.adjacency_list}
        distances[start] = 0
        previous = {}
        pq = [(0, start)]
        
        while pq:
            current_dist, current = heapq.heappop(pq)
            
            if current == end:
                break
            
            if current_dist > distances[current]:
                continue
            
            for neighbor in self.adjacency_list[current]:
                weight = self.weights.get((current, neighbor), 1.0)
                distance = current_dist + weight
                
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current
                    heapq.heappush(pq, (distance, neighbor))
        
        # Reconstruct path
        path = []
        current = end
        while current in previous:
            path.append(current)
            current = previous[current]
        
        if path or start == end:
            path.append(start)
            path.reverse()
            return (path, distances[end])
        
        return ([], float('inf'))
    
    def has_cycle(self) -> bool:
        """Check if the graph has a cycle."""
        visited = set()
        rec_stack = set()
        
        def has_cycle_util(v, parent=None):
            visited.add(v)
            rec_stack.add(v)
            
            for neighbor in self.adjacency_list[v]:
                if neighbor not in visited:
                    if has_cycle_util(neighbor, v):
                        return True
                elif neighbor in rec_stack:
                    if self.directed or neighbor != parent:
                        return True
            
            rec_stack.remove(v)
            return False
        
        for vertex in self.adjacency_list:
            if vertex not in visited:
                if has_cycle_util(vertex):
                    return True
        
        return False
    
    def is_bipartite(self) -> bool:
        """Check if the graph is bipartite."""
        if not self.adjacency_list:
            return True
        
        color = {}
        
        def bfs_color(start):
            queue = deque([start])
            color[start] = 0
            
            while queue:
                vertex = queue.popleft()
                
                for neighbor in self.adjacency_list[vertex]:
                    if neighbor not in color:
                        color[neighbor] = 1 - color[vertex]
                        queue.append(neighbor)
                    elif color[neighbor] == color[vertex]:
                        return False
            return True
        
        for vertex in self.adjacency_list:
            if vertex not in color:
                if not bfs_color(vertex):
                    return False
        
        return True
    
    def topological_sort(self) -> Optional[List]:
        """
        Perform topological sort (for DAGs only).
        
        Returns:
            List of vertices in topological order, or None if graph has cycle
        """
        if not self.directed:
            return None
        
        if self.has_cycle():
            return None
        
        in_degree = {v: 0 for v in self.adjacency_list}
        for v in self.adjacency_list:
            for neighbor in self.adjacency_list[v]:
                in_degree[neighbor] += 1
        
        queue = deque([v for v in in_degree if in_degree[v] == 0])
        result = []
        
        while queue:
            vertex = queue.popleft()
            result.append(vertex)
            
            for neighbor in self.adjacency_list[vertex]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result if len(result) == len(self.adjacency_list) else None
    
    def __str__(self):
        """String representation of the graph."""
        lines = []
        for vertex in sorted(self.adjacency_list.keys(), key=str):
            neighbors = sorted(self.adjacency_list[vertex], key=str)
            lines.append(f"{vertex}: {neighbors}")
        return "\n".join(lines)


def create_complete_graph(n: int) -> Graph:
    """Create a complete graph with n vertices."""
    g = Graph()
    for i in range(n):
        for j in range(i + 1, n):
            g.add_edge(i, j)
    return g


def create_cycle_graph(n: int) -> Graph:
    """Create a cycle graph with n vertices."""
    g = Graph()
    for i in range(n):
        g.add_edge(i, (i + 1) % n)
    return g


def create_path_graph(n: int) -> Graph:
    """Create a path graph with n vertices."""
    g = Graph()
    for i in range(n - 1):
        g.add_edge(i, i + 1)
    return g


__all__ = [
    'Graph',
    'create_complete_graph',
    'create_cycle_graph',
    'create_path_graph',
]
