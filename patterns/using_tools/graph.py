from langgraph.graph import END, START, StateGraph

from .nodes import fallback_agent, math_agent, reasoning_agent
from .state import AgentState


def _after_reasoning(state: AgentState) -> str:
    return "math_agent" if state.get("route") == "math" else "fallback_agent"


def _after_math(state: AgentState) -> str:
    return "fallback_agent" if state.get("error") else END


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("reasoning_agent", reasoning_agent)
    graph.add_node("math_agent", math_agent)
    graph.add_node("fallback_agent", fallback_agent)

    graph.add_edge(START, "reasoning_agent")
    graph.add_conditional_edges("reasoning_agent", _after_reasoning)
    graph.add_conditional_edges("math_agent", _after_math)
    graph.add_edge("fallback_agent", END)

    return graph.compile()


def answer_question(question: str, *, api_key: str | None = None) -> AgentState:
    if not question.strip():
        raise ValueError("Enter a question before submitting.")
    return build_graph().invoke(
        {"question": question.strip()},
        config={"configurable": {"openai_api_key": api_key}},
    )