from langgraph.graph import StateGraph, END
from .state import PlanState
from .nodes import planner, executor

def build_graph():
    graph = StateGraph(PlanState)

    graph.add_node("planner", planner)
    graph.add_node("executor", executor)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "executor")
    graph.add_edge("executor", END)

    return graph.compile()