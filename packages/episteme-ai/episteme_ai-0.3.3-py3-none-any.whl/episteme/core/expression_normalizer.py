import re


class ExpressionNormalizer:
    """
    Normaliza expresiones lógicas simples para facilitar
    el matching de reglas de inferencia.
    """

    @staticmethod
    def normalize(expr: str) -> str:
        if not expr:
            return expr

        e = expr.strip()

        # 1. Lowercase
        e = e.lower()

        # 2. Normalizar negación
        e = e.replace("¬", "not ")
        e = re.sub(r"\bno\b", "not", e)
        e = re.sub(r"\bnot\s+", "not ", e)

        # 3. Normalizar implicación
        e = e.replace("→", "->")
        e = e.replace("⇒", "->")
        e = re.sub(r"\s*->\s*", " -> ", e)

        # 4. Normalizar cuantificadores
        e = e.replace("∀", "forall ")
        e = re.sub(r"\bforall\s+", "forall ", e)

        # 5. Quitar espacios múltiples
        e = re.sub(r"\s+", " ", e)

        return e.strip()
