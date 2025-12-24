def detect_contradictions(parsed_sentences):
    contradictions = []
    sentences = [p["sentence"] for p in parsed_sentences]

    for i in range(len(sentences)-1):
        s1, s2 = sentences[i], sentences[i+1]

        # Heurística 1: conectores adversativos
        if any(c in s2.lower() for c in ["pero", "sin embargo", "no obstante", "aunque"]):
            contradictions.append({
                "s1": s1,
                "s2": s2,
                "reason": "Adversative connector suggests contradiction"
            })

        # Heurística 2: negación explícita
        if ("no " in s2.lower()) and (s2.replace("no ", "").strip().lower() in s1.lower()):
            contradictions.append({
                "s1": s1,
                "s2": s2,
                "reason": "Direct negation pattern"
            })

    return contradictions

def detect_relations(parsed_sentences):
    relations = []
    for i in range(1, len(parsed_sentences)):
        s_prev = parsed_sentences[i-1]
        s_curr = parsed_sentences[i]

        if "porque" in s_curr["sentence"].lower() or "ya que" in s_curr["sentence"].lower():
            relations.append({
                "type": "evidence",
                "from": s_curr["sentence"],
                "to": s_prev["sentence"]
            })
    return relations

def compute_flags(parsed, contradictions, relations):
    n_hyp = sum(1 for p in parsed if p["type"] == "hypothesis")
    n_claims = sum(1 for p in parsed if p["type"] == "claim")
    n_relations = len(relations)
    n_contradictions = len(contradictions)

    claims_without_support = max(0, n_claims - n_relations)

    rigor_score = max(0.0, 1.0 - 0.4*n_contradictions - 0.3*claims_without_support)

    weaknesses = []
    strengths = []

    if n_hyp > 0:
        strengths.append("Contains explicit hypotheses")
    if n_relations > 0:
        strengths.append("Provides some evidence")
    if n_contradictions > 0:
        weaknesses.append("Contains contradictions")
    if claims_without_support > 0:
        weaknesses.append("Claims lack evidence")

    return {
        "rigor_score": round(rigor_score, 3),
        "weaknesses": weaknesses,
        "strengths": strengths
    }
