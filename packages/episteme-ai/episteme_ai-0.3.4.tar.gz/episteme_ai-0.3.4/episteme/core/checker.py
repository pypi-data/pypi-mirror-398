from typing import Dict, List, Set
from episteme.core.ast import Step, Proof
from episteme.theory.loader import load_theory
from episteme.core.expression_normalizer import ExpressionNormalizer


class CheckResult:
    def __init__(self, step_id: int, status: str, message: str = ""):
        self.step_id = step_id
        self.status = status
        self.message = message

    def __repr__(self):
        return f"Step {self.step_id}: {self.status} ({self.message})"


class ProofChecker:
    """
    Checker heurístico mínimo para Episteme (v0.3).
    """

    def __init__(self, theory: Dict[str, str] = None, theory_name: str = None):
        if theory_name:
            self.theory = load_theory(theory_name)
        else:
            self.theory = theory if theory else {}

    # ====================================================
    # CHECK DE UNA DEMOSTRACIÓN COMPLETA
    # ====================================================
    def check(self, proof: Proof) -> List[CheckResult]:
        results: List[CheckResult] = []
        valid_steps: Set[int] = set()

        for step in proof.steps:
            result = self._check_step(step, proof, valid_steps)
            results.append(result)

            if result.status == "ok":
                valid_steps.add(step.id)

        return results

    # ====================================================
    # CHECK DE UN PASO INDIVIDUAL
    # ====================================================
    def _check_step(self, step: Step, proof: Proof, valid_steps: Set[int]) -> CheckResult:

        # ASSUME / CLAIM
        if step.type in ("assume", "claim"):
            if not step.expr:
                return CheckResult(step.id, "invalid", "Empty expression")
            return CheckResult(step.id, "ok", "Base step")

        # INVOKE THEOREM
        if step.type == "invoke_theorem":
            if step.theorem not in self.theory:
                return CheckResult(step.id, "invalid", f"Theorem '{step.theorem}' not found")
            return CheckResult(step.id, "ok", f"Theorem '{step.theorem}' found")

        # DERIVE / APPLY_RULE
        if step.type in ("derive", "apply_rule"):

            if not step.premises:
                return CheckResult(step.id, "invalid", "No premises provided")

            for p in step.premises:
                if p not in valid_steps:
                    return CheckResult(step.id, "invalid", f"Premise {p} is invalid")

            rule = (step.rule or "").lower()

            if rule == "modus_ponens":
                return self._check_modus_ponens(step, proof)
            if rule == "modus_tollens":
                return self._check_modus_tollens(step, proof)
            if rule == "contrapositive":
                return self._check_contrapositive(step, proof)
            if rule == "universal_instantiation":
                return self._check_universal_instantiation(step, proof)
            if rule == "double_negation":
                return self._check_double_negation(step, proof)

            if rule == "hypothetical_syllogism":
                return self._check_hypothetical_syllogism(step, proof)

            if rule == "conjunction_elimination":
                return self._check_conjunction_elimination(step, proof)

            return CheckResult(step.id, "unknown", "Unrecognized rule")

        return CheckResult(step.id, "unknown", f"Unknown step type '{step.type}'")

    # ====================================================
    # MODUS PONENS
    # ====================================================
    def _check_modus_ponens(self, step: Step, proof: Proof) -> CheckResult:
        if len(step.premises) != 2:
            return CheckResult(step.id, "invalid", "Modus Ponens requires two premises")

        p1 = proof.get_step(step.premises[0])
        p2 = proof.get_step(step.premises[1])

        e1 = ExpressionNormalizer.normalize(p1.expr)
        e2 = ExpressionNormalizer.normalize(p2.expr)

        if "->" not in e2:
            return CheckResult(step.id, "invalid", "Second premise must be implication")

        left, right = map(str.strip, e2.split("->"))

        if e1 != left:
            return CheckResult(step.id, "invalid", "Premise does not match implication")

        if ExpressionNormalizer.normalize(step.expr) != right:
            return CheckResult(step.id, "invalid", "Conclusion does not match implication")

        return CheckResult(step.id, "ok", "Modus Ponens applied correctly")

    # ====================================================
    # MODUS TOLLENS
    # ====================================================
    def _check_modus_tollens(self, step: Step, proof: Proof) -> CheckResult:
        if len(step.premises) != 2:
            return CheckResult(step.id, "invalid", "Modus Tollens requires two premises")

        p1 = proof.get_step(step.premises[0])
        p2 = proof.get_step(step.premises[1])

        for impl, neg in [(p1, p2), (p2, p1)]:
            impl_expr = ExpressionNormalizer.normalize(impl.expr)
            neg_expr = ExpressionNormalizer.normalize(neg.expr)

            if "->" not in impl_expr or not neg_expr.startswith("not "):
                continue

            A, B = map(str.strip, impl_expr.split("->"))
            if neg_expr[len("not "):] == B:
                expected = f"not {A}"
                if ExpressionNormalizer.normalize(step.expr) == expected:
                    return CheckResult(step.id, "ok", "Modus Tollens applied correctly")
                return CheckResult(step.id, "invalid", f"Expected '{expected}'")

        return CheckResult(step.id, "invalid", "Premises do not match Modus Tollens")

    # ====================================================
    # CONTRAPOSITION
    # ====================================================
    def _check_contrapositive(self, step: Step, proof: Proof) -> CheckResult:
        if len(step.premises) != 1:
            return CheckResult(step.id, "invalid", "Contrapositive requires one premise")

        p = proof.get_step(step.premises[0])
        expr = ExpressionNormalizer.normalize(p.expr)

        if "->" not in expr:
            return CheckResult(step.id, "invalid", "Premise must be implication")

        A, B = map(str.strip, expr.split("->"))
        expected = f"not {B} -> not {A}"

        if ExpressionNormalizer.normalize(step.expr) == expected:
            return CheckResult(step.id, "ok", "Contrapositive applied correctly")

        return CheckResult(step.id, "invalid", f"Expected '{expected}'")

    # ====================================================
    # UNIVERSAL INSTANTIATION
    # ====================================================
    def _check_universal_instantiation(self, step: Step, proof: Proof) -> CheckResult:
        if len(step.premises) != 1:
            return CheckResult(step.id, "invalid", "Universal instantiation requires one premise")

        p = proof.get_step(step.premises[0])
        expr = ExpressionNormalizer.normalize(p.expr)

        if not expr.startswith("forall "):
            return CheckResult(step.id, "invalid", "Premise must start with 'forall'")

        _, formula = expr.split(" ", 1)

        if "(x)" not in formula:
            return CheckResult(step.id, "invalid", "Expected variable x in universal formula")

        template = formula.replace("(x)", "")

        concl = ExpressionNormalizer.normalize(step.expr)

        if not concl.startswith(template):
            return CheckResult(step.id, "invalid", "Conclusion does not match universal formula")

        return CheckResult(step.id, "ok", "Universal instantiation applied correctly")
    
    # ====================================================
    # DOUBLE NEGATION
    # ====================================================
    def _check_double_negation(self, step: Step, proof: Proof) -> CheckResult:
        if len(step.premises) != 1:
            return CheckResult(step.id, "invalid", "Double negation requires one premise")

        p = proof.get_step(step.premises[0])
        expr = ExpressionNormalizer.normalize(p.expr)

        if not expr.startswith("not not "):
            return CheckResult(step.id, "invalid", "Premise must be of form 'not not A'")

        expected = expr[len("not not "):]

        if ExpressionNormalizer.normalize(step.expr) == expected:
            return CheckResult(step.id, "ok", "Double negation eliminated correctly")

        return CheckResult(step.id, "invalid", f"Expected '{expected}'")

    # ====================================================
    # HYPOTHETICAL SYLLOGISM
    # ====================================================
    def _check_hypothetical_syllogism(self, step: Step, proof: Proof) -> CheckResult:
        if len(step.premises) != 2:
            return CheckResult(step.id, "invalid", "Hypothetical syllogism requires two premises")

        p1 = proof.get_step(step.premises[0])
        p2 = proof.get_step(step.premises[1])

        e1 = ExpressionNormalizer.normalize(p1.expr)
        e2 = ExpressionNormalizer.normalize(p2.expr)

        if "->" not in e1 or "->" not in e2:
            return CheckResult(step.id, "invalid", "Both premises must be implications")

        A, B1 = map(str.strip, e1.split("->"))
        B2, C = map(str.strip, e2.split("->"))

        if B1 != B2:
            return CheckResult(step.id, "invalid", "Middle terms do not match")

        expected = f"{A} -> {C}"

        if ExpressionNormalizer.normalize(step.expr) == expected:
            return CheckResult(step.id, "ok", "Hypothetical syllogism applied correctly")

        return CheckResult(step.id, "invalid", f"Expected '{expected}'")

    # ====================================================
    # CONJUNCTION ELIMINATION
    # ====================================================
    def _check_conjunction_elimination(self, step: Step, proof: Proof) -> CheckResult:
        if len(step.premises) != 1:
            return CheckResult(step.id, "invalid", "Conjunction elimination requires one premise")

        p = proof.get_step(step.premises[0])
        expr = ExpressionNormalizer.normalize(p.expr)

        if " and " not in expr:
            return CheckResult(step.id, "invalid", "Premise must be a conjunction 'A and B'")

        A, B = map(str.strip, expr.split("and", 1))

        concl = ExpressionNormalizer.normalize(step.expr)

        if concl == A or concl == B:
            return CheckResult(step.id, "ok", "Conjunction eliminated correctly")

        return CheckResult(step.id, "invalid", "Conclusion must be one conjunct")
