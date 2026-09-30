import os

import streamlit as st
from dotenv import load_dotenv

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
WORKFLOW_KEYS = {
    TOOL_WORKFLOW: "tool_using",
    SUPERVISOR_WORKFLOW: "supervisor_worker",
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


if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversations" not in st.session_state:
    st.session_state.conversations = {
        WORKFLOW_KEYS[TOOL_WORKFLOW]: st.session_state.messages,
        WORKFLOW_KEYS[SUPERVISOR_WORKFLOW]: [],
    }

selected_workflow = st.segmented_control(
    "Choose a demonstration",
    options=[TOOL_WORKFLOW, SUPERVISOR_WORKFLOW],
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
    else:
        st.caption("Supervisor → math worker or leave-balance worker")
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
else:
    st.title("Supervisor-worker agent")
    st.caption("The supervisor routes calculations and leave requests to specialist workers.")

for message in messages:
    with st.chat_message(message["role"]):
        if message.get("route_label"):
            st.caption(message["route_label"])
        if message.get("error"):
            st.error(message["content"])
        else:
            st.markdown(message["content"])

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
                else:
                    result = run_supervisor_query(question, api_key=configured_api_key())
                    route = result.get("worker", "math")
                    route_labels = {
                        "math": "Math worker",
                        "leave": "Leave-balance worker",
                        "general": "General-answer worker",
                    }
                    route_label = route_labels.get(route, "General-answer worker")
                    response_text = result.get("result", "The workflow returned no result.")
                status.update(label=f"Answered by {route_label.lower()}", state="complete")
            st.caption(route_label)
            if selected_workflow == SUPERVISOR_WORKFLOW and route == "math":
                st.caption(f"Expression: `{result.get('expression', '')}`")
            elif selected_workflow == SUPERVISOR_WORKFLOW and route == "leave":
                st.caption(f"Employee: {result.get('employee_name', 'Unknown')}")
            st.markdown(response_text)
            messages.append(
                {
                    "role": "assistant",
                    "content": response_text,
                    "route_label": route_label,
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