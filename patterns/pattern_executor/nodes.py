from config.llm import get_llm
from .state import PlanState

llm = get_llm()

# -------------------------------
# PLANNER AGENT (WITH EXAMPLES)
# -------------------------------
def planner(state: PlanState):
    print("\n[Planner] Creating execution plan...")

    prompt = f"""
            You are a planning agent.

            Your job:
            - Break the task into AT MOST 3 steps
            - Each step MUST start with a dash (-)
            - Do NOT add explanations

            Examples:

            Task: Explain Python basics
            Plan:
            - Explain what Python is
            - Give 2 simple Python examples
            - Create 2 quiz questions

            Task: Summarize a research paper
            Plan:
            - Identify the main topic
            - Summarize key contributions
            - List 2 limitations

            Now plan the following task:

            Task: {state['task']}
            Plan:
            """

    response = llm.invoke(prompt).content.strip()
    plan = response.split("\n")

    print("[Planner] Generated plan:")
    for step in plan:
        print(step)

    return {"plan": plan}

# -------------------------------
# EXECUTOR AGENT
# -------------------------------
def executor(state: PlanState):
    print("\n[Executor] Executing plan...")

    results = []

    for step in state["plan"]:
        step = step.strip()

        # Safety checks
        if not step:
            continue
        if not step.startswith("-"):
            continue

        print(f"[Executor] Running step: {step}")

        prompt =f"""
                Execute the following step clearly and concisely.
                
                Step:
                {step}
            """

        response = llm.invoke(prompt).content
        # response = response.content
        results.append(response)

    return {"output": "\n\n".join(results)}