from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from config.llm import get_llm
from tools.calculator import calculator
from .state import AgentState


class RouteDecision(BaseModel):
    route: Literal["math", "general"] = Field(
        description="Use math only for questions answerable by evaluating arithmetic."
    )
    expression: str = Field(
        default="",
        description="A Python-style arithmetic expression when route is math; otherwise empty.",
    )


def _llm_for_config(config: RunnableConfig | None):
    configurable = (config or {}).get("configurable", {})
    return get_llm(configurable.get("openai_api_key"))


def reasoning_agent(
    state: AgentState, config: RunnableConfig | None = None
) -> dict[str, str]:
    planner = _llm_for_config(config).with_structured_output(RouteDecision)
    decision = planner.invoke(
        [
            SystemMessage(
                content=(
                    "Classify the user's request. Choose math only when the request is a "
                    "calculation that can be answered by a numeric arithmetic expression. "
                    "For definitions, explanations, advice, and all other requests choose "
                    "general. Do not solve or explain the question."
                )
            ),
            HumanMessage(content=state["question"]),
        ]
    )

    expression = decision.expression.strip()
    if decision.route == "math" and expression:
        return {"route": "math", "expression": expression}
    return {"route": "general", "expression": ""}


def math_agent(state: AgentState) -> dict[str, str]:
    try:
        result = calculator(state["expression"])
    except (ArithmeticError, ValueError) as error:
        return {"error": str(error)}

    return {
        "result": result,
        "answer": f"The answer is {result}.",
    }


def fallback_agent(
    state: AgentState, config: RunnableConfig | None = None
) -> dict[str, str]:
    response = _llm_for_config(config).invoke(
        [
            SystemMessage(
                content=(
                    "Answer the user's question clearly and accurately. If it is outside "
                    "your knowledge, say so. Do not claim to have used a calculator."
                )
            ),
            HumanMessage(content=state["question"]),
        ]
    )
    return {"route": "general", "answer": response.content.strip()}