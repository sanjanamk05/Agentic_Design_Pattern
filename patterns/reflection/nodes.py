import json

from langchain_core.runnables import RunnableConfig

from config.llm import get_llm
from .state import ReflectionState


def _llm_for_config(config: RunnableConfig | None):
    configurable = (config or {}).get("configurable", {})
    return get_llm(configurable.get("openai_api_key"))


def generator_agent(
    state: ReflectionState, config: RunnableConfig | None = None
) -> dict[str, object]:
    prompt = f"""
    You are the generator in a reflection workflow. Write a concise answer that
    directly fulfills the task. On revisions, use the critic's feedback and
    improve the previous draft. Return only the answer, without commentary.

    Task: {state['task']}
    Previous draft: {state.get('draft', '') or 'None'}
    Critic feedback: {state.get('feedback', '') or 'None'}
    """
    draft = _llm_for_config(config).invoke(prompt).content.strip()
    return {
        "draft": draft,
        "final_answer": draft,
        "attempts": state.get("attempts", 0) + 1,
        "status": "drafted",
    }


def critic_agent(
    state: ReflectionState, config: RunnableConfig | None = None
) -> dict[str, object]:
    prompt = f"""
    You are the critic in a reflection workflow. Check whether the draft fully
    satisfies the task, is clear, and avoids unsupported claims. Request revision
    if anything important is missing or incorrect. Otherwise approve it.

    Return only valid JSON in this shape:
    {{"needs_revision": true, "feedback": "short, actionable feedback"}}

    Task: {state['task']}
    Draft: {state['draft']}
    """
    response = _llm_for_config(config).invoke(prompt).content.strip()
    payload = json.loads(response)
    needs_revision = bool(payload.get("needs_revision", False))
    feedback = str(payload.get("feedback", "Looks good.")).strip()

    result: dict[str, object] = {
        "needs_revision": needs_revision,
        "feedback": feedback,
        "status": "needs_improvement" if needs_revision else "approved",
    }
    if not needs_revision:
        result["final_answer"] = state["draft"]
    return result