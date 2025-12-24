import re
from typing import List, Dict


class ReasoningParser:
    """
    Parser muy simple para razonamientos en lenguaje natural.
    Se basa en heurísticas y palabras clave.
    """

    KEYWORDS = {
        "hypothesis": ["supongamos", "hipótesis", "si asumimos", "propongamos"],
        "thesis": ["por lo tanto", "concluimos", "en consecuencia", "por consiguiente"],
        "claim": ["afirmo", "se sostiene que", "es evidente que", "planteo que"],
        "evidence": ["porque", "ya que", "puesto que", "debido a"],
    }

    def parse(self, text: str) -> List[Dict]:
        sentences = self._split_sentences(text)
        parsed = []

        for s in sentences:
            parsed.append({
                "sentence": s,
                "type": self._classify_sentence(s)
            })

        return parsed

    # -------------------------------------------
    # Split text into sentences
    # -------------------------------------------
    def _split_sentences(self, text: str) -> List[str]:
        # Very simple sentence splitting
        chunks = re.split(r'[.!?]+', text)
        return [c.strip() for c in chunks if c.strip()]

    # -------------------------------------------
    # Classify sentence by heuristics
    # -------------------------------------------
    def _classify_sentence(self, sentence: str) -> str:
        s = sentence.lower()

        for label, kw_list in self.KEYWORDS.items():
            if any(kw in s for kw in kw_list):
                return label

        # fallback heuristic
        if "si " in s and " entonces " in s:
            return "argument"

        return "unknown"
