from episteme.core.proof_graph import ProofGraph


def build_proof_graph(proof, results) -> ProofGraph:
    graph = ProofGraph()

    # 1. Crear nodos
    for step in proof.steps:
        graph.add_node(
            id=step.id,
            type=step.type,
            expr=step.expr,
            rule=step.rule,
            theorem=step.theorem,
            metadata={
                "premises": step.premises
            }
        )

    # 2. Crear aristas (dependencias)
    for step in proof.steps:
        if step.premises:
            for p in step.premises:
                graph.add_edge(
                    source=p,
                    target=step.id,
                    type="uses",
                    metadata={"rule": step.rule}
                )

    return graph
