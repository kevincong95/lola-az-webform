import unittest
from unittest.mock import patch
from langgraph.graph import StateGraph
from lola_graph import primary_graph, route_to_subgraph, PrimaryState
from cassie_graph import lesson_graph, LessonState
from dud_graph import dud_graph, DudState

class TestSubgraphRouting(unittest.TestCase):
    """Tests for primary assistant routing logic"""

    def setUp(self):
        # Create state as a dictionary with the required keys
        self.initial_state = {
            "messages": [],
            "user_topic": "Arrays",
            "session_type": "lesson",
            "subgraph_state": None
        }

    def test_routing_to_cassie(self):
        """Ensure that the primary assistant correctly routes to Cassie Graph."""
        state = self.initial_state.copy()
        state["session_type"] = "lesson"  # Lesson session directs to Cassie
        result = route_to_subgraph(state)
        self.assertEqual(result, "cassie_entry", "Failed to route to Cassie Graph.")

    def test_routing_to_dud(self):
        """Ensure that the primary assistant correctly routes to Dud Graph."""
        state = self.initial_state.copy()
        state["session_type"] = "quiz"  # Quiz session directs to Dud
        result = route_to_subgraph(state)
        self.assertEqual(result, "dud_entry", "Failed to route to Dud Graph.")

    def test_invalid_routing(self):
        """Ensure an invalid session type raises an error."""
        state = self.initial_state.copy()
        state["session_type"] = "unknown_mode"  # Invalid session type

        with self.assertRaises(ValueError):
            route_to_subgraph(state)

    @patch("cassie_graph.lesson_graph.invoke")
    @patch("dud_graph.dud_graph.invoke")
    def test_multiple_routings(self, mock_dud_invoke, mock_cassie_invoke):
        """Simulate multiple subgraph transitions with mock outputs."""
        state = self.initial_state.copy()

        # Mock Cassie Graph returning a lesson completion state
        mock_cassie_invoke.return_value = {
            "messages": ["Lesson complete!"],
            "user_topic": "Algebra",
            "session_type": "quiz",  # Switch to quiz mode after lesson
            "subgraph_state": {
                "topic": "Algebra",
                "lesson_plan": [],
                "current_step": 3,
                "current_question": "What is 2x + 3 = 7?",
                "attempts": 1,
                "summary": "Great job! You've completed the lesson on Algebra.",
                "user_answer": "x = 2",
                "awaiting_answer": False,
            }
        }

        # Mock Dud Graph returning a quiz completion state
        mock_dud_invoke.return_value = {
            "messages": ["Quiz complete!"],
            "user_topic": "Algebra",
            "session_type": "lesson",  # Switch back to lesson
            "subgraph_state": {
                "correct_answers": 8,
                "mistakes": 2,
                "golden_bridge": True,
                "current_question": "Solve for x: 3x - 4 = 5",
                "user_answer": "x = 3",
                "awaiting_answer": False,
                "summary": "Well done! You scored 8/10 on the quiz. Ready for your next lesson?"
            }
        }

        # Step 1: Start in lesson mode (route to Cassie)
        next_step = route_to_subgraph(state)
        self.assertEqual(next_step, "cassie_entry")
        state = mock_cassie_invoke(state)

        # Validate Cassie Graph summary
        self.assertIsInstance(state["subgraph_state"], dict)
        self.assertTrue(state["subgraph_state"]["summary"])
        self.assertEqual(state["subgraph_state"]["summary"], "Great job! You've completed the lesson on Algebra.")

        # Step 2: After lesson, session_type should switch to quiz (route to Dud)
        next_step = route_to_subgraph(state)
        self.assertEqual(next_step, "dud_entry")
        state = mock_dud_invoke(state)

        # Validate Dud Graph summary
        self.assertIsInstance(state["subgraph_state"], dict)
        self.assertTrue(state["subgraph_state"]["summary"])
        self.assertEqual(state["subgraph_state"]["summary"], "Well done! You scored 8/10 on the quiz. Ready for your next lesson?")

        # Step 3: After quiz, session_type should switch back to lesson (route to Cassie)
        next_step = route_to_subgraph(state)
        self.assertEqual(next_step, "cassie_entry")

if __name__ == '__main__':
    unittest.main()