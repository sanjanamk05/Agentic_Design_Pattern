from langchain_core.runnables import RunnableConfig

from config.llm import get_llm
from tools.calculator import calculator
from tools.leaves_db import get_leave_balance
from .state import SupervisorWorkerState


def _llm_for_config(config: RunnableConfig | None):
    configurable = (config or {}).get("configurable", {})
    return get_llm(configurable.get("openai_api_key"))


def supervisor(
    state: SupervisorWorkerState, config: RunnableConfig | None = None
) -> dict[str, str]:
    prompt = f"""
    Decide which worker should handle this request.

    Return ONLY one word:
    - math
    - leave
    - general

    Use:
    - math for calculations, percentages, averages, and totals
    - leave for leave balance, vacation, sick leave, and PTO
    - general for definitions, explanations, and all other questions

    Request: {state["query"]}
    """
    worker = _llm_for_config(config).invoke(prompt).content.strip().lower()
    if worker not in {"math", "leave", "general"}:
        worker = "general"
    return {"worker": worker}


def math_agent(
    state: SupervisorWorkerState, config: RunnableConfig | None = None
) -> dict[str, str]:
    prompt = f"""
    Convert this request into a valid arithmetic expression.
    Return only the expression.

    Request: {state["query"]}
    """
    expression = _llm_for_config(config).invoke(prompt).content.strip()
    try:
        result = calculator(expression)
    except (ArithmeticError, ValueError) as error:
        result = f"Error: {error}"
    return {"expression": expression, "result": result}


def leaves_balance(
    state: SupervisorWorkerState, config: RunnableConfig | None = None
) -> dict[str, str]:
    prompt = f"""
    Extract the employee name from this request.
    Return only the employee name.

    Request: {state["query"]}
    """
    employee_name = _llm_for_config(config).invoke(prompt).content.strip()
    balance = get_leave_balance(employee_name)
    return {
        "employee_name": employee_name,
        "leave_balance": balance,
        "result": balance,
    }


def general_agent(
    state: SupervisorWorkerState, config: RunnableConfig | None = None
) -> dict[str, str]:
    prompt = f"""
    Answer the user's question clearly and accurately.
    If you do not know the answer, say so. Do not convert the request into a math expression.

    Question: {state["query"]}
    """
    answer = _llm_for_config(config).invoke(prompt).content.strip()
    return {"answer": answer, "result": answer}