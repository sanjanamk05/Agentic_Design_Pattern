import os

import streamlit as st
from dotenv import load_dotenv

from patterns.reflection.graph import run_query as run_reflection_query
from patterns.supervisor_worker.graph import run_query as run_supervisor_query
from patterns.using_tools.graph import answer_question


load_dotenv()

st.set_page_config(
    page_title="Tool-using agent",
    page_icon=":material/hub:",
    layout="centered",
)

TOOL_WORKFLOW = "Tool-using"
SUPERVISOR_WORKFLOW = "Supervisor-worker"
REFLECTION_WORKFLOW = "Reflection"
WORKFLOW_KEYS = {
    TOOL_WORKFLOW: "tool_using",
    SUPERVISOR_WORKFLOW: "supervisor_worker",
    REFLECTION_WORKFLOW: "reflection",
}
EXAMPLES = {
    TOOL_WORKFLOW: (
        "Define AI",
        "What is the square of the average of 10 and 5?",
        "What does an AI agent do?",
    ),
    SUPERVISOR_WORKFLOW: (
        "What is the square of the average of 10 and 5?",
        "What is the leave balance for Alice?",
        "How many PTO days does Bob have?",
    ),
    REFLECTION_WORKFLOW: (
        "Explain why Python is good for beginners in exactly two sentences. Mention simple syntax, community support, and libraries.",
        "Explain one benefit and one limitation of using AI in education.",
    ),
}


def clear_conversation() -> None:
    workflow = st.session_state.get("workflow_selector", TOOL_WORKFLOW)
    workflow_key = WORKFLOW_KEYS[workflow]
    st.session_state.conversations[workflow_key] = []
    st.session_state[f"suggested_{workflow_key}"] = None


def configured_api_key() -> str | None:
    try:
        secret = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        secret = None
    return secret or os.getenv("OPENAI_API_KEY")


def render_reflection_history(history: list[dict[str, object]]) -> None:
    if not history:
        return
    with st.expander(f"Review rounds ({len(history)})", icon=":material/rate_review:"):
        for round_info in history:
            st.markdown(f"**Draft {round_info['attempt']}**")
            st.markdown(str(round_info.get("draft", "")))
            if round_info.get("status") == "approved":
                st.badge("Approved", icon=":material/check_circle:", color="green")
            else:
                st.badge("Revision requested", icon=":material/edit:", color="orange")
            if round_info.get("feedback"):
                st.caption(f"Critic feedback: {round_info['feedback']}")


if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversations" not in st.session_state:
    st.session_state.conversations = {
        WORKFLOW_KEYS[TOOL_WORKFLOW]: st.session_state.messages,
        WORKFLOW_KEYS[SUPERVISOR_WORKFLOW]: [],
        WORKFLOW_KEYS[REFLECTION_WORKFLOW]: [],
    }

selected_workflow = st.segmented_control(
    "Choose a demonstration",
    options=[TOOL_WORKFLOW, SUPERVISOR_WORKFLOW, REFLECTION_WORKFLOW],
    default=TOOL_WORKFLOW,
    key="workflow_selector",
)
workflow_key = WORKFLOW_KEYS[selected_workflow]
messages = st.session_state.conversations[workflow_key]

with st.sidebar:
    st.markdown("## Agentic workbench")
    st.caption("Compare two agentic workflow patterns.")
    if configured_api_key():
        st.badge("Model configured", icon=":material/check_circle:", color="green")
    else:
        st.badge("API key needed", icon=":material/key:", color="orange")
    st.markdown("#### Workflow")
    if selected_workflow == TOOL_WORKFLOW:
        st.caption("Reasoning agent → math tool or general-answer fallback")
    elif selected_workflow == SUPERVISOR_WORKFLOW:
        st.caption("Supervisor → math worker or leave-balance worker")
    else:
        st.caption("Generator → critic → revise until approved or max attempts")
    st.button(
        "New conversation",
        icon=":material/add:",
        on_click=clear_conversation,
        type="secondary",
        width="stretch",
    )

if selected_workflow == TOOL_WORKFLOW:
    st.title("Tool-using agent")
    st.caption("Ask a calculation, a definition, or a general question.")
elif selected_workflow == SUPERVISOR_WORKFLOW:
    st.title("Supervisor-worker agent")
    st.caption("The supervisor routes calculations and leave requests to specialist workers.")
else:
    st.title("Reflection agent")
    st.caption("A generator drafts, a critic reviews, and the generator revises from feedback.")

for message in messages:
    with st.chat_message(message["role"]):
        if message.get("route_label"):
            st.caption(message["route_label"])
        if message.get("error"):
            st.error(message["content"])
        else:
            st.markdown(message["content"])
            if message.get("reflection_history"):
                render_reflection_history(message["reflection_history"])

question = st.chat_input("Ask your question", key=f"chat_input_{workflow_key}")
if not messages:
    selected_example = st.pills(
        "Try a question",
        options=EXAMPLES[selected_workflow],
        key=f"suggested_{workflow_key}",
        label_visibility="collapsed",
    )
    question = question or selected_example

if question:
    messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            with st.status("Routing your question…", expanded=False) as status:
                if selected_workflow == TOOL_WORKFLOW:
                    result = answer_question(question, api_key=configured_api_key())
                    route = result.get("route", "general")
                    route_label = "Math agent" if route == "math" else "General fallback"
                    response_text = result.get("answer", "The workflow returned no answer.")
                elif selected_workflow == SUPERVISOR_WORKFLOW:
                    result = run_supervisor_query(question, api_key=configured_api_key())
                    route = result.get("worker", "math")
                    route_labels = {
                        "math": "Math worker",
                        "leave": "Leave-balance worker",
                        "general": "General-answer worker",
                    }
                    route_label = route_labels.get(route, "General-answer worker")
                    response_text = result.get("result", "The workflow returned no result.")
                else:
                    result = run_reflection_query(question, api_key=configured_api_key())
                    attempts = result.get("attempts", 0)
                    reflection_status = result.get("status", "completed")
                    route_label = f"Reflection {reflection_status} · {attempts} attempt(s)"
                    response_text = result.get(
                        "final_answer", result.get("draft", "No answer was returned.")
                    )
                status.update(label=f"Answered by {route_label.lower()}", state="complete")
            st.caption(route_label)
            if selected_workflow == SUPERVISOR_WORKFLOW and route == "math":
                st.caption(f"Expression: `{result.get('expression', '')}`")
            elif selected_workflow == SUPERVISOR_WORKFLOW and route == "leave":
                st.caption(f"Employee: {result.get('employee_name', 'Unknown')}")
            st.markdown(response_text)
            reflection_history = result.get("history", [])
            if selected_workflow == REFLECTION_WORKFLOW:
                render_reflection_history(reflection_history)
            messages.append(
                {
                    "role": "assistant",
                    "content": response_text,
                    "route_label": route_label,
                    "reflection_history": reflection_history,
                }
            )
        except Exception as error:
            response_text = (
                "I couldn't complete that request. Check your API key and connection, "
                "then try again. "
                f"Details: {error}"
            )
            st.error(response_text)
            messages.append(
                {"role": "assistant", "content": response_text, "error": True}
            )