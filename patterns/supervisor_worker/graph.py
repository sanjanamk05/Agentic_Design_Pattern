from langgraph.graph import END, START, StateGraph

from .nodes import general_agent, leaves_balance, math_agent, supervisor
from .state import SupervisorWorkerState


def route(state: SupervisorWorkerState) -> str:
    return state["worker"]


def build_graph():
    graph = StateGraph(SupervisorWorkerState)
    graph.add_node("supervisor", supervisor)
    graph.add_node("math_agent", math_agent)
    graph.add_node("leaves_balance", leaves_balance)
    graph.add_node("general_agent", general_agent)

    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges(
        "supervisor",
        route,
        {
            "math": "math_agent",
            "leave": "leaves_balance",
            "general": "general_agent",
        },
    )
    graph.add_edge("math_agent", END)
    graph.add_edge("leaves_balance", END)
    graph.add_edge("general_agent", END)
    return graph.compile()


def run_query(query: str, *, api_key: str | None = None) -> SupervisorWorkerState:
    if not query.strip():
        raise ValueError("Enter a question before submitting.")
    return build_graph().invoke(
        {"query": query.strip()},
        config={"configurable": {"openai_api_key": api_key}},
    )