import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
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


class FakeTextLLM:
    def __init__(self, *responses: str):
        self.responses = iter(responses)

    def invoke(self, _messages):
        return FakeResponse(next(self.responses))


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


class SupervisorWorkerTests(unittest.TestCase):
    def test_supervisor_routes_calculation_to_math_worker(self):
        from patterns.supervisor_worker.graph import build_graph as build_supervisor_graph

        fake_llm = FakeTextLLM("math", "((10 + 5) / 2) ** 2")
        with patch("patterns.supervisor_worker.nodes._llm_for_config", return_value=fake_llm):
            result = build_supervisor_graph().invoke(
                {"query": "What is the square of the average of 10 and 5?"}
            )

        self.assertEqual(result["worker"], "math")
        self.assertEqual(result["result"], "56.25")

    def test_supervisor_routes_leave_request_to_leave_worker(self):
        from patterns.supervisor_worker.graph import build_graph as build_supervisor_graph

        fake_llm = FakeTextLLM("leave", "Alice")
        with (
            patch("patterns.supervisor_worker.nodes._llm_for_config", return_value=fake_llm),
            patch(
                "patterns.supervisor_worker.nodes.get_leave_balance",
                return_value="Alice has 12 leave days remaining.",
            ),
        ):
            result = build_supervisor_graph().invoke(
                {"query": "What is the leave balance for Alice?"}
            )

        self.assertEqual(result["worker"], "leave")
        self.assertEqual(result["employee_name"], "Alice")
        self.assertEqual(result["result"], "Alice has 12 leave days remaining.")


class ReflectionTests(unittest.TestCase):
    def test_critic_feedback_causes_revision_then_approval(self):
        from patterns.reflection.graph import run_query

        fake_llm = FakeTextLLM(
            "First draft.",
            '{"needs_revision": true, "feedback": "Add one concrete detail."}',
            "Revised draft with a concrete detail.",
            '{"needs_revision": false, "feedback": "The task is satisfied."}',
        )
        with patch("patterns.reflection.nodes._llm_for_config", return_value=fake_llm):
            result = run_query("Write a short explanation.")

        self.assertEqual(result["attempts"], 2)
        self.assertEqual(result["status"], "approved")
        self.assertEqual(result["final_answer"], "Revised draft with a concrete detail.")
        self.assertEqual(len(result["history"]), 2)
        self.assertEqual(result["history"][0]["feedback"], "Add one concrete detail.")
        self.assertEqual(result["history"][1]["status"], "approved")

    def test_reflection_stops_after_three_drafts(self):
        from patterns.reflection.graph import run_query

        fake_llm = FakeTextLLM(
            "Draft one.",
            '{"needs_revision": true, "feedback": "Try again."}',
            "Draft two.",
            '{"needs_revision": true, "feedback": "Try again."}',
            "Draft three.",
            '{"needs_revision": true, "feedback": "Still needs work."}',
        )
        with patch("patterns.reflection.nodes._llm_for_config", return_value=fake_llm):
            result = run_query("Write a short explanation.")

        self.assertEqual(result["attempts"], 3)
        self.assertEqual(len(result["history"]), 3)
        self.assertEqual(result["status"], "needs_improvement")

    def test_supervisor_routes_generic_question_to_general_worker(self):
        from patterns.supervisor_worker.graph import build_graph as build_supervisor_graph

        fake_llm = FakeTextLLM("general", "AI is the field of building intelligent systems.")
        with patch("patterns.supervisor_worker.nodes._llm_for_config", return_value=fake_llm):
            result = build_supervisor_graph().invoke({"query": "Define AI"})

        self.assertEqual(result["worker"], "general")
        self.assertEqual(result["answer"], "AI is the field of building intelligent systems.")
        self.assertEqual(result["result"], result["answer"])

    def test_leave_database_returns_case_insensitive_seeded_balance(self):
        from tools.leaves_db import get_leave_balance

        with TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "employee_leaves.db"
            with patch("tools.leaves_db.DB_PATH", database_path):
                result = get_leave_balance("alice")

        self.assertEqual(result, "Alice has 12 leave days remaining.")


class StreamlitAppTests(unittest.TestCase):
    def test_chat_app_renders_without_a_configured_api_key(self):
        from streamlit.testing.v1 import AppTest

        app_path = Path(__file__).resolve().parents[1] / "app.py"
        app = AppTest.from_file(str(app_path)).run(timeout=20)

        self.assertFalse(list(app.exception))
        self.assertEqual([item.value for item in app.title], ["Tool-using agent"])

        app.segmented_control[0].set_value("Supervisor-worker").run()
        self.assertFalse(list(app.exception))
        self.assertEqual([item.value for item in app.title], ["Supervisor-worker agent"])

        with patch(
            "patterns.supervisor_worker.graph.run_query",
            return_value={
                "worker": "general",
                "answer": "AI is the field of building intelligent systems.",
                "result": "AI is the field of building intelligent systems.",
            },
        ):
            app.chat_input[0].set_value("Define AI").run()

        self.assertFalse(list(app.exception))
        self.assertIn("General-answer worker", [item.value for item in app.caption])

        app.segmented_control[0].set_value("Reflection").run()
        self.assertFalse(list(app.exception))
        self.assertEqual([item.value for item in app.title], ["Reflection agent"])

        reflection_result = {
            "attempts": 2,
            "status": "approved",
            "final_answer": "Python has readable syntax.",
            "history": [
                {
                    "attempt": 1,
                    "draft": "Python is good.",
                    "feedback": "Be more specific.",
                    "status": "needs_improvement",
                },
                {
                    "attempt": 2,
                    "draft": "Python has readable syntax.",
                    "feedback": "Looks good.",
                    "status": "approved",
                },
            ],
        }
        with patch("patterns.reflection.graph.run_query", return_value=reflection_result):
            app.chat_input[0].set_value("Explain Python syntax.").run()

        self.assertFalse(list(app.exception))
        self.assertTrue(
            any("Reflection approved" in item.value for item in app.caption)
        )
        feedback_captions = [
            item.value for item in app.caption if item.value.startswith("Critic feedback:")
        ]
        self.assertEqual(len(feedback_captions), 2)


if __name__ == "__main__":
    unittest.main()