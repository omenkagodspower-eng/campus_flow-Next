import unittest
from unittest.mock import patch

from campusflow.quiz import run_quiz


class TestQuiz(unittest.TestCase):

    @patch("campusflow.quiz.get_input")
    def test_invalid_choice_is_rejected(self, mock_input):
        mock_input.side_effect = [
            "X", "B",       # Question 1: invalid, then correct
            "C", "Explanation 2",
            "A",
            "D",
            "B", "Explanation 5",
            "C",
            "n",
        ]

        with patch("builtins.print") as mock_print:
            run_quiz()

        output = " ".join(
            str(call) for call in mock_print.call_args_list
        )
        self.assertIn("Invalid choice", output)
        self.assertIn("6/6", output)

    @patch("campusflow.quiz.get_input")
    def test_perfect_score(self, mock_input):
        mock_input.side_effect = [
            "B",
            "C", "Explanation 2",
            "A",
            "D",
            "B", "Explanation 5",
            "C",
            "n",
        ]

        with patch("builtins.print") as mock_print:
            run_quiz()

        output = " ".join(
            str(call) for call in mock_print.call_args_list
        )
        self.assertIn("6/6", output)

    @patch("campusflow.quiz.get_input")
    def test_incorrect_answers_reduce_score(self, mock_input):
        mock_input.side_effect = [
            "A",
            "A", "Explanation 2",
            "B",
            "C",
            "D", "Explanation 5",
            "A",
            "n",
        ]

        with patch("builtins.print") as mock_print:
            run_quiz()

        output = " ".join(
            str(call) for call in mock_print.call_args_list
        )
        self.assertIn("0/6", output)


if __name__ == "__main__":
    unittest.main()

