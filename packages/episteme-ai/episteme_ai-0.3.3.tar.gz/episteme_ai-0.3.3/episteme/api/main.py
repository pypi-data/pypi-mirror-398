from fastapi import FastAPI
from pydantic import BaseModel

from fastapi import Request
from fastapi.responses import JSONResponse

from episteme.parsers.proof_parser import ProofParser
from episteme.core.checker import ProofChecker
from episteme.parsers.reasoning_parser import ReasoningParser
from episteme.reasoning.analyzer import ReasoningAnalyzer
from episteme.core.build_proof_graph import build_proof_graph
from episteme.theory.loader import list_theories, load_theory

# -------------------------------
# API Version
# -------------------------------

API_VERSION = "0.3"

# -------------------------------
# Models for API input/output
# -------------------------------

class ProofText(BaseModel):
    text: str


class ReasoningText(BaseModel):
    text: str


class EvaluateProofRequest(BaseModel):
    text: str
    theory: str | None = None
    strict_mode: bool = False

class CheckStepRequest(BaseModel):
    proof: str
    step_id: int
    theory: str | None = None


# -------------------------------
# Legacy utils (v0.3)
# -------------------------------

def build_inference_graph(proof, results):
    """
    Legacy inference graph (kept for backward compatibility).
    """
    graph = []
    step_map = {s.id: s for s in proof.steps}

    for r in results:
        step = step_map[r.step_id]
        if step.premises:
            graph.append({
                "from": step.premises,
                "to": step.id,
                "rule": step.rule
            })

    return graph


# -------------------------------
# FastAPI app
# -------------------------------

app = FastAPI(
    title="Episteme API",
    description="API para verificación de proofs y razonamientos naturales",
    version="0.3.3"
)

# -------------------------------
# Endpoints
# -------------------------------

@app.post("/parse_proof")
def parse_proof(data: ProofText):
    parser = ProofParser()
    proof = parser.parse(data.text)
    return {"steps": [step.__dict__ for step in proof.steps]}


@app.post("/check_proof")
def check_proof(data: ProofText):
    parser = ProofParser()
    checker = ProofChecker(theory_name="basic_analysis")

    proof = parser.parse(data.text)
    results = checker.check(proof)

    return {
        "results": [
            {"step": r.step_id, "status": r.status, "message": r.message}
            for r in results
        ]
    }


@app.post("/parse_reasoning")
def parse_reasoning(data: ReasoningText):
    parser = ReasoningParser()
    parsed = parser.parse(data.text)
    return {"parsed": parsed}


@app.post("/evaluate_proof")
def evaluate_proof(data: EvaluateProofRequest):
    # -------------------------------
    # Parse
    # -------------------------------
    parser = ProofParser()
    proof = parser.parse(data.text)

    # -------------------------------
    # Check
    # -------------------------------
    checker = ProofChecker(theory_name=data.theory) \
        if data.theory else ProofChecker()
    results = checker.check(proof)

    # -------------------------------
    # Graphs
    # -------------------------------
    inference_graph = build_inference_graph(proof, results)  # legacy
    proof_graph = build_proof_graph(proof, results)          # v0.3

    # -------------------------------
    # Annotated steps
    # -------------------------------
    annotated_steps = []
    for step, res in zip(proof.steps, results):
        annotated_steps.append({
            "id": step.id,
            "type": step.type,
            "expr": step.expr,
            "theorem": step.theorem,
            "rule": step.rule,
            "premises": step.premises,
            "status": res.status,
            "message": res.message
        })

    # -------------------------------
    # Summary
    # -------------------------------
    valid_steps = sum(1 for r in results if r.status == "ok")
    invalid_steps = sum(1 for r in results if r.status == "invalid")
    unknown_steps = sum(1 for r in results if r.status == "unknown")

    if data.strict_mode:
        global_validity = invalid_steps == 0 and unknown_steps == 0
    else:
        global_validity = invalid_steps == 0

    summary = {
        "valid_steps": valid_steps,
        "invalid_steps": invalid_steps,
        "unknown_steps": unknown_steps,
        "strict_mode": data.strict_mode,
        "global_validity": global_validity
    }

    return {
        "steps": annotated_steps,
        "inference_graph": inference_graph,          # legacy (v0.2)
        "proof_graph": proof_graph.to_dict(),        # NEW (v0.3)
        "summary": summary
    }


@app.post("/reasoning/analyze")
def analyze_reasoning(data: ReasoningText):
    analyzer = ReasoningAnalyzer()
    result = analyzer.analyze(data.text)

    graph = result["argument_graph"]

    return {
        "argument_graph": graph.to_dict(),
        "flags": result["flags"],
        "summary": graph.to_dict()["summary"]
    }

@app.post("/proof/check_step")
def check_step(data: CheckStepRequest):
    parser = ProofParser()
    proof = parser.parse(data.proof)

    checker = ProofChecker(theory_name=data.theory) \
        if data.theory else ProofChecker()

    results = checker.check(proof)

    for r in results:
        if r.step_id == data.step_id:
            return {
                "step_id": r.step_id,
                "status": r.status,
                "message": r.message
            }

    return {
        "step_id": data.step_id,
        "status": "invalid",
        "message": "Step not found"
    }

@app.get("/theory/list")
def list_available_theories():
    return {
        "theories": list_theories()
    }

@app.get("/theory/get")
def get_theory(name: str):
    theory = load_theory(name)
    return {
        "name": name,
        "theorems": theory
    }

@app.exception_handler(ValueError)
def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={
            "api_version": API_VERSION,
            "error": {
                "code": "INVALID_INPUT",
                "message": str(exc),
                "details": {}
            }
        }
    )

@app.get("/")
def root():
    return {"message": "Episteme API is running"}
