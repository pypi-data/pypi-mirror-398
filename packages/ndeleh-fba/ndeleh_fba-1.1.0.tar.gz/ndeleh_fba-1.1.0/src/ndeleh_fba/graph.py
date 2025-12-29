from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Hashable, Any


NodeId = Hashable


@dataclass
class Node:
    """
    A node in the associative graph.

    Attributes
    ----------
    id:
        Unique identifier for the node (string, int, etc.).
    data:
        Optional metadata associated with the node (labels, payloads, etc.).
    """
    id: NodeId
    data: Dict[str, Any] = field(default_factory=dict)


class Graph:
    """
    Simple weighted graph for the Ndeleh Fish Bone Algorithm (N-FBA).

    - Nodes are identified by a hashable id.
    - Edges have a float weight (typically in [0, 1], but not enforced here).
    """

    def __init__(self) -> None:
        # Map node_id -> Node
        self.nodes: Dict[NodeId, Node] = {}
        # Adjacency: node_id -> {neighbor_id -> weight}
        self.edges: Dict[NodeId, Dict[NodeId, float]] = {}

    # ------------- Node management -------------

    def add_node(self, node_id: NodeId, **data: Any) -> None:
        """
        Add a node if it doesn't already exist.

        Parameters
        ----------
        node_id:
            Hashable identifier for the node.
        data:
            Arbitrary keyword metadata.
        """
        if node_id not in self.nodes:
            self.nodes[node_id] = Node(node_id, dict(data))
            self.edges[node_id] = {}
        else:
            # Update metadata if node exists
            self.nodes[node_id].data.update(data)

    def has_node(self, node_id: NodeId) -> bool:
        """Return True if the graph contains a node with this id."""
        return node_id in self.nodes

    # ------------- Edge management -------------

    def add_edge(
        self,
        src: NodeId,
        dst: NodeId,
        weight: float = 1.0,
        undirected: bool = True,
    ) -> None:
        """
        Add an edge (src -> dst) with a given weight.

        If undirected=True (default), also add (dst -> src).

        Nodes are created automatically if they do not yet exist.
        """
        if weight < 0:
            raise ValueError("Edge weight must be non-negative.")

        self.add_node(src)
        self.add_node(dst)

        self.edges[src][dst] = float(weight)
        if undirected:
            self.edges[dst][src] = float(weight)

    def neighbors(self, node_id: NodeId) -> Dict[NodeId, float]:
        """
        Return a dict of neighbors and weights for a node.

        Raises KeyError if the node does not exist.
        """
        if node_id not in self.edges:
            raise KeyError(f"Node {node_id!r} not found in graph.")
        return self.edges[node_id]

    # ------------- Convenience -------------

    def __len__(self) -> int:
        """Number of nodes in the graph."""
        return len(self.nodes)

    def __contains__(self, node_id: object) -> bool:
        return node_id in self.nodes

    def __repr__(self) -> str:
        return f"Graph(num_nodes={len(self.nodes)}, num_edges={self._edge_count()})"

    def _edge_count(self) -> int:
        return sum(len(neigh) for neigh in self.edges.values())
# =============================================================================
# FishboneGraph — thin wrapper for compatibility with industrial logic
# =============================================================================

class FishboneGraph(Graph):
    """
    A thin subclass of Graph used by industrial logic.

    This class exists purely so that code importing `FishboneGraph` works,
    while still using the core Graph functionality.
    """
    def __init__(self):
        super().__init__()
