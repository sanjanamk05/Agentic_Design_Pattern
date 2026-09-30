from typing import TypedDict, List

class PlanState(TypedDict):
    task: str
    plan: List[str]
    output: str