from dataclasses import dataclass, field
from typing import List, Dict, Optional, Literal

NodeType = Literal[
    "assume",
    "claim",
    "derive",
    "invoke_theorem"
]

EdgeType = Literal[
    "uses",        # dependencia lógica
    "derives"      # resultado de inferencia
]


@dataclass
class ProofNode:
    id: int
    type: NodeType
    expr: str
    rule: Optional[str] = None
    theorem: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class ProofEdge:
    source: int
    target: int
    type: EdgeType
    metadata: Dict = field(default_factory=dict)


@dataclass
class ProofGraph:
    nodes: List[ProofNode] = field(default_factory=list)
    edges: List[ProofEdge] = field(default_factory=list)

    def add_node(
        self,
        id: int,
        type: NodeType,
        expr: str,
        rule: Optional[str] = None,
        theorem: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> ProofNode:
        node = ProofNode(
            id=id,
            type=type,
            expr=expr,
            rule=rule,
            theorem=theorem,
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
    ) -> ProofEdge:
        edge = ProofEdge(
            source=source,
            target=target,
            type=type,
            metadata=metadata or {}
        )
        self.edges.append(edge)
        return edge

    def to_dict(self) -> Dict:
        return {
            "type": "proof_graph",
            "nodes": [n.__dict__ for n in self.nodes],
            "edges": [e.__dict__ for e in self.edges],
            "summary": self._summary(),
            "metadata": {
                "n_nodes": len(self.nodes),
                "n_edges": len(self.edges)
            }
        }

    def _summary(self) -> Dict:
        return {
            "n_steps": len(self.nodes),
            "n_dependencies": len(self.edges),
            "n_inference_steps": sum(
                1 for n in self.nodes if n.type == "derive"
            )
        }
