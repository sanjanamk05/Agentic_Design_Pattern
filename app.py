import os

import streamlit as st
from dotenv import load_dotenv

from patterns.using_tools.graph import answer_question


load_dotenv()

st.set_page_config(
    page_title="Tool-using agent",
    page_icon=":material/hub:",
    layout="centered",
)

EXAMPLES = (
    "Define AI",
    "What is the square of the average of 10 and 5?",
    "What does an AI agent do?",
)


def clear_conversation() -> None:
    st.session_state.messages = []
    st.session_state.suggested_question = None


def configured_api_key() -> str | None:
    try:
        secret = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        secret = None
    return secret or os.getenv("OPENAI_API_KEY")


if "messages" not in st.session_state:
    st.session_state.messages = []
if "suggested_question" not in st.session_state:
    st.session_state.suggested_question = None

with st.sidebar:
    st.markdown("## Agentic workbench")
    st.caption("A two-agent workflow with a general-question fallback.")
    if configured_api_key():
        st.badge("Model configured", icon=":material/check_circle:", color="green")
    else:
        st.badge("API key needed", icon=":material/key:", color="orange")
    st.markdown("#### Workflow")
    st.caption("Reasoning agent → math tool or general-answer fallback")
    st.button(
        "New conversation",
        icon=":material/add:",
        on_click=clear_conversation,
        type="secondary",
        width="stretch",
    )

st.title("Tool-using agent")
st.caption("Ask a calculation, a definition, or a general question.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("route"):
            route_label = "Math agent" if message["route"] == "math" else "General fallback"
            st.caption(route_label)
        if message.get("error"):
            st.error(message["content"])
        else:
            st.markdown(message["content"])

question = st.chat_input("Ask your question", key="chat_input")
if not st.session_state.messages:
    selected_example = st.pills(
        "Try a question",
        options=EXAMPLES,
        key="suggested_question",
        label_visibility="collapsed",
    )
    question = question or selected_example

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            with st.status("Routing your question…", expanded=False) as status:
                result = answer_question(question, api_key=configured_api_key())
                route = result.get("route", "general")
                route_label = "Math agent" if route == "math" else "General fallback"
                status.update(label=f"Answered with {route_label.lower()}", state="complete")
            response_text = result.get("answer", "The workflow returned no answer.")
            st.caption(route_label)
            st.markdown(response_text)
            st.session_state.messages.append(
                {"role": "assistant", "content": response_text, "route": route}
            )
        except Exception as error:
            response_text = (
                "I couldn't complete that request. Check your API key and connection, "
                "then try again. "
                f"Details: {error}"
            )
            st.error(response_text)
            st.session_state.messages.append(
                {"role": "assistant", "content": response_text, "error": True}
            )