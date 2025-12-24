from episteme.parsers.reasoning_parser import ReasoningParser
from episteme.reasoning.analyze_tools import (
    detect_contradictions,
    detect_relations,
    compute_flags
)
from episteme.reasoning.argument_graph import ArgumentGraph


class ReasoningAnalyzer:
    def __init__(self):
        self.parser = ReasoningParser()

    def analyze(self, text: str) -> dict:
        parsed = self.parser.parse(text)

        contradictions = detect_contradictions(parsed)
        relations = detect_relations(parsed)

        graph = ArgumentGraph()
        node_map = {}

        # 1. Crear nodos
        for idx, p in enumerate(parsed, start=1):
            node = graph.add_node(
                text=p["sentence"],
                type=p["type"],
                score=0.8,
                metadata=p
            )
            node_map[idx] = node.id

        # 2. Añadir contradicciones como aristas
        for c in contradictions:
            s1_idx = self._find_sentence_index(parsed, c["s1"])
            s2_idx = self._find_sentence_index(parsed, c["s2"])

            if s1_idx and s2_idx:
                graph.add_edge(
                    source=node_map[s1_idx],
                    target=node_map[s2_idx],
                    type="contradicts",
                    metadata={"reason": c["reason"]}
                )

        # 3. Añadir relaciones (evidence, etc.)
        for r in relations:
            from_idx = self._find_sentence_index(parsed, r["from"])
            to_idx = self._find_sentence_index(parsed, r["to"])

            if from_idx and to_idx:
                graph.add_edge(
                    source=node_map[from_idx],
                    target=node_map[to_idx],
                    type="supports"
                )

        flags = compute_flags(parsed, contradictions, relations)

        return {
            "argument_graph": graph,
            "flags": flags
        }

    def _find_sentence_index(self, parsed, sentence: str):
        for i, p in enumerate(parsed, start=1):
            if p["sentence"] == sentence:
                return i
        return None
