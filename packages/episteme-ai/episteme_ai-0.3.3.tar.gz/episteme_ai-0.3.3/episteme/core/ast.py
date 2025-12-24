from dataclasses import dataclass
from typing import List, Optional, Literal


StepType = Literal[
    "assume",
    "claim",
    "derive",
    "invoke_theorem",
    "apply_rule"
]


@dataclass
class Step:
    """
    Representa un paso de una demostración o razonamiento.
    """
    id: int
    type: StepType
    expr: Optional[str] = None
    theorem: Optional[str] = None
    rule: Optional[str] = None
    premises: Optional[List[int]] = None

    def __repr__(self):
        return (
            f"Step(id={self.id}, type={self.type}, "
            f"expr={self.expr}, theorem={self.theorem}, "
            f"rule={self.rule}, premises={self.premises})"
        )


@dataclass
class Proof:
    """
    Representa una demostración completa como una lista ordenada de pasos.
    """
    steps: List[Step]

    def get_step(self, step_id: int) -> Step:
        for step in self.steps:
            if step.id == step_id:
                return step
        raise ValueError(f"Step {step_id} not found.")