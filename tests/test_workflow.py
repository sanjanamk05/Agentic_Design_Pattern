import unittest
from pathlib import Path
from unittest.mock import patch

from patterns.using_tools.graph import build_graph
from patterns.using_tools.nodes import RouteDecision
from tools.calculator import calculator


class FakePlanner:
    def __init__(self, decision: RouteDecision):
        self.decision = decision

    def invoke(self, _messages):
        return self.decision


class FakeResponse:
    def __init__(self, content: str):
        self.content = content


class FakeLLM:
    def __init__(self, decision: RouteDecision, answer: str = "Artificial intelligence is..."):
        self.decision = decision
        self.answer = answer

    def with_structured_output(self, _schema):
        return FakePlanner(self.decision)

    def invoke(self, _messages):
        return FakeResponse(self.answer)


class CalculatorTests(unittest.TestCase):
    def test_evaluates_arithmetic(self):
        self.assertEqual(calculator("((10 + 5) / 2) ** 2"), "56.25")

    def test_rejects_python_calls(self):
        with self.assertRaises(ValueError):
            calculator("__import__('os').system('whoami')")

    def test_rejects_excessive_exponents(self):
        with self.assertRaises(ValueError):
            calculator("2 ** 101")


class WorkflowTests(unittest.TestCase):
    def test_routes_arithmetic_to_math_agent(self):
        fake = FakeLLM(RouteDecision(route="math", expression="((10 + 5) / 2) ** 2"))
        with patch("patterns.using_tools.nodes.get_llm", return_value=fake):
            result = build_graph().invoke({"question": "Square the average of 10 and 5"})

        self.assertEqual(result["route"], "math")
        self.assertEqual(result["result"], "56.25")
        self.assertEqual(result["answer"], "The answer is 56.25.")

    def test_routes_general_question_to_fallback(self):
        fake = FakeLLM(RouteDecision(route="general"), "AI is the field of building intelligent systems.")
        with patch("patterns.using_tools.nodes.get_llm", return_value=fake):
            result = build_graph().invoke({"question": "Define AI"})

        self.assertEqual(result["route"], "general")
        self.assertEqual(result["answer"], "AI is the field of building intelligent systems.")

    def test_invalid_math_expression_uses_fallback(self):
        fake = FakeLLM(RouteDecision(route="math", expression="1 / 0"), "Division by zero is undefined.")
        with patch("patterns.using_tools.nodes.get_llm", return_value=fake):
            result = build_graph().invoke({"question": "What is one divided by zero?"})

        self.assertEqual(result["route"], "general")
        self.assertEqual(result["answer"], "Division by zero is undefined.")


class StreamlitAppTests(unittest.TestCase):
    def test_chat_app_renders_without_a_configured_api_key(self):
        from streamlit.testing.v1 import AppTest

        app_path = Path(__file__).resolve().parents[1] / "app.py"
        app = AppTest.from_file(str(app_path)).run(timeout=20)

        self.assertFalse(list(app.exception))
        self.assertEqual([item.value for item in app.title], ["Tool-using agent"])


if __name__ == "__main__":
    unittest.main()