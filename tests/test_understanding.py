import unittest
from unittest.mock import patch

import main
from campusflow.understanding_check import (
    VALID_CHOICES,
    format_question,
    is_correct,
    parse_choice,
    score_answers,
)
from campusflow.understanding_questions import QUESTIONS


class TestQuestionBank(unittest.TestCase):
    def test_bank_has_six_questions(self):
        self.assertEqual(len(QUESTIONS), 6)

    def test_every_question_has_four_options_and_a_valid_answer(self):
        for question in QUESTIONS:
            self.assertEqual(tuple(question["options"]), VALID_CHOICES)
            self.assertIn(question["correct"], VALID_CHOICES)

    def test_question_ids_are_unique(self):
        ids = [question["id"] for question in QUESTIONS]

        self.assertEqual(len(ids), len(set(ids)))

    def test_bank_contains_no_scoring_logic(self):
        import campusflow.understanding_questions as bank

        public_functions = [
            name
            for name, value in vars(bank).items()
            if callable(value) and not name.startswith("_")
        ]

        self.assertEqual(public_functions, [])


class TestScoring(unittest.TestCase):
    def all_correct(self):
        return {q["id"]: q["correct"] for q in QUESTIONS}

    def test_perfect_score_is_six(self):
        self.assertEqual(score_answers(self.all_correct()), 6)

    def test_no_answers_scores_zero(self):
        self.assertEqual(score_answers({}), 0)

    def test_one_point_per_correct_answer(self):
        answers = self.all_correct()

        # Force exactly two questions wrong, without depending on which
        # letter is correct for any question.
        for question in QUESTIONS[:2]:
            wrong = next(
                letter for letter in VALID_CHOICES
                if letter != question["correct"]
            )
            answers[question["id"]] = wrong

        self.assertEqual(score_answers(answers), 4)

    def test_score_reflects_submitted_answers_only(self):
        answers = {q["id"]: "D" for q in QUESTIONS}
        expected = sum(1 for q in QUESTIONS if q["correct"] == "D")

        self.assertEqual(score_answers(answers), expected)

    def test_is_correct(self):
        question = QUESTIONS[0]

        self.assertTrue(is_correct(question, question["correct"]))
        self.assertFalse(is_correct(question, "A" if question["correct"] != "A" else "B"))


class TestChoiceParsing(unittest.TestCase):
    def test_accepts_lowercase_and_whitespace(self):
        self.assertEqual(parse_choice(" b "), "B")

    def test_rejects_invalid_choices(self):
        for bad in ("E", "", "AB", "1", "z"):
            with self.assertRaises(ValueError):
                parse_choice(bad)

    def test_format_question_lists_all_four_options(self):
        text = format_question(QUESTIONS[0], 1, 6)

        for letter in VALID_CHOICES:
            self.assertIn(f"{letter}.", text)


class TestInteractiveCheck(unittest.TestCase):
    def run_quiz(self, answers):
        with patch("builtins.input", side_effect=answers), \
                patch("builtins.print") as printed, \
                patch("main.save_learning_note") as saved:
            score = main.run_understanding_check()

        output = "\n".join(str(c.args[0]) for c in printed.call_args_list)
        return score, output, saved

    def explanations(self):
        return ["Q1", "Rejected actions must keep data unchanged", "Q2", "Empty data must show zero percent"]

    def test_invalid_answer_is_rejected_then_retried(self):
        correct = [q["correct"] for q in QUESTIONS]
        answers = ["Z", "9"] + correct + self.explanations()

        score, output, _ = self.run_quiz(answers)

        self.assertIn("Please answer with A, B, C or D.", output)
        self.assertEqual(score, 6)

    def test_invalid_answers_never_count_as_points(self):
        answers = ["X"] * 3 + ["A"] * 6 + self.explanations()
        expected = sum(1 for q in QUESTIONS if q["correct"] == "A")

        score, _, _ = self.run_quiz(answers)

        self.assertEqual(score, expected)

    def test_final_score_is_displayed(self):
        correct = [q["correct"] for q in QUESTIONS]

        _, output, _ = self.run_quiz(correct + self.explanations())

        self.assertIn("Final score: 6 / 6", output)

    def test_explanations_are_saved_for_two_questions(self):
        correct = [q["correct"] for q in QUESTIONS]

        _, _, saved = self.run_quiz(correct + self.explanations())

        saved.assert_called_once()
        entries = saved.call_args.args[0]
        self.assertEqual(len(entries), 2)

    def test_one_word_explanation_is_rejected_not_auto_accepted(self):
        correct = [q["correct"] for q in QUESTIONS]
        answers = correct + ["Q1", "yes", "Rejected actions keep data unchanged", "Q2", "Empty data shows zero percent"]

        _, output, saved = self.run_quiz(answers)

        self.assertIn("Please write at least a short sentence.", output)
        self.assertEqual(len(saved.call_args.args[0]), 2)


if __name__ == "__main__":
    unittest.main()
