import re
from typing import List
from episteme.core.ast import Step, Proof
from episteme.core.expression_normalizer import ExpressionNormalizer


class ProofParser:
    """
    Parser minimalista basado en plantilla para pruebas estructuradas.
    """

    step_regex = re.compile(r"^\s*(\d+)\.\s*(.+)$")

    def parse(self, text: str) -> Proof:
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        steps: List[Step] = []

        for line in lines:
            match = self.step_regex.match(line)
            if not match:
                raise ValueError(f"Invalid step format: '{line}'")

            step_id = int(match.group(1))
            content = match.group(2).strip()

            step = self._parse_step(step_id, content)
            steps.append(step)

        return Proof(steps)

    # -------------------------------------------
    # Parse individual step
    # -------------------------------------------
    def _parse_step(self, step_id: int, content: str) -> Step:
        content_lower = content.lower()

        # assume A
        if content_lower.startswith("assume "):
            raw = content[len("assume "):].strip()
            expr = ExpressionNormalizer.normalize(raw)
            return Step(id=step_id, type="assume", expr=expr)

        # claim C
        if content_lower.startswith("claim "):
            raw = content[len("claim "):].strip()
            expr = ExpressionNormalizer.normalize(raw)
            return Step(id=step_id, type="claim", expr=expr)

        # invoke_theorem EVT
        if content_lower.startswith("invoke_theorem "):
            theorem = content[len("invoke_theorem "):].strip()
            return Step(id=step_id, type="invoke_theorem", theorem=theorem)

        # derive ...
        if content_lower.startswith("derive "):
            return self._parse_derive(step_id, content)

        # apply_rule ...
        if content_lower.startswith("apply_rule "):
            return self._parse_apply_rule(step_id, content)

        raise ValueError(f"Unknown step type: '{content}'")

    # -------------------------------------------
    # derive B from 1,2 using modus_ponens
    # -------------------------------------------
    def _parse_derive(self, step_id: int, content: str) -> Step:
        content_clean = " ".join(content.split())

        content_clean = content_clean[len("derive "):].strip()

        if " using " in content_clean.lower():
            before, rule_part = re.split(r"\s+using\s+", content_clean, flags=re.IGNORECASE)
            rule = rule_part.strip().lower()
        else:
            before = content_clean
            rule = None

        if " from " not in before.lower():
            raise ValueError(f"Missing 'from' in derive step: '{content}'")

        expr_part, premises_part = re.split(r"\s+from\s+", before, flags=re.IGNORECASE)

        raw_expr = expr_part.strip()
        expr = ExpressionNormalizer.normalize(raw_expr)

        premises_raw = premises_part.replace(" ", "")
        premises = [int(x) for x in premises_raw.split(",") if x]

        return Step(
            id=step_id,
            type="derive",
            expr=expr,
            premises=premises,
            rule=rule
        )

    # -------------------------------------------
    # apply_rule modus_ponens on 1,2 to get B
    # -------------------------------------------
    def _parse_apply_rule(self, step_id: int, content: str) -> Step:
        content = re.sub(r"\s+", " ", content).strip()

        pattern = r"apply_rule (.+) on ([\d,\s]+) to get (.+)"
        m = re.match(pattern, content, flags=re.IGNORECASE)
        if not m:
            raise ValueError(f"Invalid apply_rule format: '{content}'")

        rule = m.group(1).strip().lower()
        premises_raw = m.group(2).replace(" ", "")
        premises = [int(x) for x in premises_raw.split(",") if x]

        raw_expr = m.group(3).strip()
        expr = ExpressionNormalizer.normalize(raw_expr)

        return Step(
            id=step_id,
            type="apply_rule",
            expr=expr,
            premises=premises,
            rule=rule
        )
