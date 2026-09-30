# Agentic design pattern: tool-using agent

A set of LangGraph agentic-pattern demonstrations with a Streamlit chat interface. Choose between the tool-using workflow and the supervisor-worker workflow from the selector at the top of the app.

## How it works

1. The reasoning agent classifies the question and extracts an arithmetic expression when appropriate.
2. Arithmetic questions go to the math agent, which evaluates the expression and returns the result.
3. General questions go to the fallback agent, which answers in natural language.
4. If a generated math expression is invalid or cannot be evaluated, the workflow falls back to a natural-language answer instead of stopping with a calculator error.

The calculator parses an allowlisted arithmetic syntax tree; it does not use Python `eval`. It supports numeric literals, parentheses, unary signs, addition, subtraction, multiplication, division, floor division, modulo, and bounded exponentiation.

### Supervisor-worker workflow

1. The supervisor classifies a request as `math`, `leave`, or `general`.
2. Math requests go to a math worker, which asks the model for an arithmetic expression and evaluates it with the same safe calculator.
3. Leave requests go to a leave worker, which extracts an employee name and queries SQLite.
4. Definitions, explanations, and other non-math/non-leave requests go to a general-answer worker.

The leave database is created on first use at `tools/employee_leaves.db` and seeded with demo balances: Alice (12), Bob (5), and Charlie (18). The database file is ignored by Git.

## Requirements

- Python 3.10 or later
- An OpenAI API key

## Setup

From the repository root in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` and replace the placeholder with your API key. The loader checks `.env` in the repository first and then the parent workspace directory. The app also accepts `OPENAI_API_KEY` from the process environment or Streamlit secrets. Never commit `.env` or `.streamlit/secrets.toml`.

To use Streamlit secrets instead, create `.streamlit/secrets.toml`:

```toml
OPENAI_API_KEY = "your-key"
```

The model defaults to `gpt-4o-mini`. Set `OPENAI_MODEL` in `.env` to choose a compatible chat model.

## Run the app

```powershell
streamlit run app.py
```

The app opens at `http://localhost:8501`. Select a workflow, then try prompts such as `Define AI`, `What is the square of the average of 10 and 5?`, or `What is the leave balance for Alice?`. The chat labels the selected route or worker. Each workflow has its own in-memory conversation history; **New conversation** clears the selected workflow's history.

The backend can also be run without the UI:

```powershell
python -m patterns.using_tools.run
```

Run module commands from the repository root so package-relative imports resolve correctly.

## Tests

```powershell
python -m unittest discover -s tests -v
```

Tests cover arithmetic evaluation and safety, math/general routing, fallback after an invalid calculation, all supervisor-worker routes, and switching the Streamlit UI between workflows. They mock model calls, so no API key or network access is needed to run tests.

## Project layout

```text
app.py                         Streamlit chat UI
config/llm.py                  OpenAI chat-model configuration
patterns/using_tools/graph.py  LangGraph workflow and public answer function
patterns/using_tools/nodes.py  Routing, math, and fallback agents
patterns/supervisor_worker/    Supervisor-worker LangGraph workflow
tools/calculator.py            Safe arithmetic evaluator
tools/leaves_db.py             SQLite leave-balance demo data
tests/test_workflow.py         Backend and UI tests
```
