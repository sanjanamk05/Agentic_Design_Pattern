from typing import Literal, TypedDict


class SupervisorWorkerState(TypedDict, total=False):
    query: str
    worker: Literal["math", "leave", "general"]
    expression: str
    result: str
    employee_name: str
    leave_balance: str
    answer: str