from typing import TypedDict


class ReflectionRound(TypedDict, total=False):
    attempt: int
    draft: str
    feedback: str
    needs_revision: bool
    status: str


class ReflectionState(TypedDict, total=False):
    task: str
    draft: str
    feedback: str
    final_answer: str
    attempts: int
    needs_revision: bool
    status: str
    history: list[ReflectionRound]