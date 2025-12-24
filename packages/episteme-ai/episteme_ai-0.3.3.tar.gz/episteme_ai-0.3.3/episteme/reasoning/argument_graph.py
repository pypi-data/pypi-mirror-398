from dataclasses import dataclass, field
from typing import List, Dict, Literal, Optional

NodeType = Literal[
    "claim",
    "hypothesis",
    "thesis",
    "evidence",
    "contradiction"
]

EdgeType = Literal[
    "supports",
    "contradicts",
    "depends_on",
    "explains"
]


@dataclass
class ArgumentNode:
    id: int
    text: str
    type: NodeType
    score: float = 1.0
    metadata: Dict = field(default_factory=dict)


@dataclass
class ArgumentEdge:
    source: int
    target: int
    type: EdgeType
    metadata: Dict = field(default_factory=dict)


@dataclass
class ArgumentGraph:
    nodes: List[ArgumentNode] = field(default_factory=list)
    edges: List[ArgumentEdge] = field(default_factory=list)

    def add_node(
        self,
        text: str,
        type: NodeType,
        score: float = 1.0,
        metadata: Optional[Dict] = None
    ) -> ArgumentNode:
        node = ArgumentNode(
            id=len(self.nodes) + 1,
            text=text,
            type=type,
            score=score,
            metadata=metadata or {}
        )
        self.nodes.append(node)
        return node

    def add_edge(
        self,
        source: int,
        target: int,
        type: EdgeType,
        metadata: Optional[Dict] = None
    ) -> ArgumentEdge:
        edge = ArgumentEdge(
            source=source,
            target=target,
            type=type,
            metadata=metadata or {}
        )
        self.edges.append(edge)
        return edge

    def to_dict(self) -> Dict:
        return {
            "type": "argument_graph",
            "nodes": [node.__dict__ for node in self.nodes],
            "edges": [edge.__dict__ for edge in self.edges],
            "summary": self._summary(),
            "metadata": {
                "n_nodes": len(self.nodes),
                "n_edges": len(self.edges),
                "edge_types": list({e.type for e in self.edges})
            }
        }

    def _summary(self) -> Dict:
        return {
            "n_nodes": len(self.nodes),
            "n_edges": len(self.edges),
            "n_contradictions": sum(
                1 for e in self.edges if e.type == "contradicts"
            ),
            "rigor_score": self._rigor_score()
        }

    def _rigor_score(self) -> float:
        if not self.nodes:
            return 0.0

        avg_node_score = sum(n.score for n in self.nodes) / len(self.nodes)
        penalty = 0.1 * sum(1 for e in self.edges if e.type == "contradicts")

        return max(0.0, min(1.0, avg_node_score - penalty))
