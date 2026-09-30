from langgraph.graph import END, START, StateGraph

from .nodes import critic_agent, generator_agent
from .state import ReflectionRound, ReflectionState


def should_retry(state: ReflectionState) -> str:
    if state.get("needs_revision") and state.get("attempts", 0) < 3:
        return "generator"
    return END


def build_graph():
    graph = StateGraph(ReflectionState)
    graph.add_node("generator", generator_agent)
    graph.add_node("critic", critic_agent)
    graph.add_edge(START, "generator")
    graph.add_edge("generator", "critic")
    graph.add_conditional_edges("critic", should_retry)
    return graph.compile()


def run_query(task: str, *, api_key: str | None = None) -> ReflectionState:
    if not task.strip():
        raise ValueError("Enter a task before submitting.")

    state: ReflectionState = {
        "task": task.strip(),
        "attempts": 0,
        "needs_revision": True,
        "status": "pending",
        "history": [],
    }
    config = {"configurable": {"openai_api_key": api_key}}
    graph = build_graph()

    for update in graph.stream(state, config=config, stream_mode="updates"):
        for node_name, node_result in update.items():
            state.update(node_result)
            if node_name == "generator":
                state["history"].append(
                    {
                        "attempt": node_result["attempts"],
                        "draft": node_result["draft"],
                        "feedback": "",
                        "status": "drafted",
                    }
                )
            elif node_name == "critic" and state["history"]:
                round_info: ReflectionRound = state["history"][-1]
                round_info.update(
                    {
                        "feedback": node_result.get("feedback", ""),
                        "needs_revision": node_result.get("needs_revision", False),
                        "status": node_result.get("status", "needs_improvement"),
                    }
                )

    return state