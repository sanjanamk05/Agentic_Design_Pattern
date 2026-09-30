# Agentic design pattern: tool-using agent

A small LangGraph workflow that answers arithmetic questions with a calculator and routes definitions or other non-arithmetic requests to a general-answer fallback. A Streamlit chat interface is included.

## How it works

1. The reasoning agent classifies the question and extracts an arithmetic expression when appropriate.
2. Arithmetic questions go to the math agent, which evaluates the expression and returns the result.
3. General questions go to the fallback agent, which answers in natural language.
4. If a generated math expression is invalid or cannot be evaluated, the workflow falls back to a natural-language answer instead of stopping with a calculator error.

The calculator parses an allowlisted arithmetic syntax tree; it does not use Python `eval`. It supports numeric literals, parentheses, unary signs, addition, subtraction, multiplication, division, floor division, modulo, and bounded exponentiation.

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

The app opens at `http://localhost:8501`. Try prompts such as `Define AI` or `What is the square of the average of 10 and 5?`. The chat labels which route answered each question. Conversation history stays in Streamlit session state and is cleared with **New conversation**.

The backend can also be run without the UI:

```powershell
python -m patterns.using_tools.run
```

Run module commands from the repository root so package-relative imports resolve correctly.

## Tests

```powershell
python -m unittest discover -s tests -v
```

Tests cover arithmetic evaluation and safety, math/general routing, fallback after an invalid calculation, and initial Streamlit rendering. They mock the model calls, so no API key or network access is needed to run tests.

## Project layout

```text
app.py                         Streamlit chat UI
config/llm.py                  OpenAI chat-model configuration
patterns/using_tools/graph.py  LangGraph workflow and public answer function
patterns/using_tools/nodes.py  Routing, math, and fallback agents
tools/calculator.py            Safe arithmetic evaluator
tests/test_workflow.py         Backend and UI tests
```
