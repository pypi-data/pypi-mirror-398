from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any

from taskmind.core import RuleEngine
from taskmind.dsl import parse_rule


app = FastAPI(title="TaskMind API", version="0.1.0")

engine = RuleEngine()


# --------- Request / Response Models ---------

class RuleInput(BaseModel):
    rule: str


class EvaluateRequest(BaseModel):
    context: Dict[str, Any]
    explain: bool = True


class EvaluateResponse(BaseModel):
    matched_rules: List[str]
    actions: List[str]
    conflict: bool
    explanation: List[str] | None


# --------- API Endpoints ---------

@app.post("/rules")
def add_rule(rule_input: RuleInput):
    """
    Add a rule using DSL.
    """
    rule = parse_rule(rule_input.rule)
    engine.add_rule(rule)
    return {"status": "rule added", "rule": rule_input.rule}


@app.post("/evaluate", response_model=EvaluateResponse)
def evaluate(req: EvaluateRequest):
    """
    Evaluate context against rules.
    """
    result = engine.run(req.context, explain=req.explain)

    explanation_text = None
    if req.explain and result["explanation"]:
        # convert explanation dicts → human-readable
        explanation_text = [
            f"Rule '{step['rule']}' "
            f"{'matched' if step['result'] else 'did not match'} "
            f"(priority {step['priority']})"
            for step in result["explanation"]
        ]

    return {
        "matched_rules": result["matched_rules"],
        "actions": result["actions"],
        "conflict": result["conflict"],
        "explanation": explanation_text
    }
