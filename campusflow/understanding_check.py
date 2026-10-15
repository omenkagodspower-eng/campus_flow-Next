"""Scoring logic for the Engineering Understanding Check.

Pure functions: no input() and no print(). The question bank lives in
understanding_questions.py, and the interactive loop lives in main.py, so
scoring can be tested without typing anything.
"""

from campusflow.understanding_questions import QUESTIONS

VALID_CHOICES = ("A", "B", "C", "D")


def parse_choice(raw):
    """Return the uppercase A-D letter for raw, or raise ValueError."""
    choice = str(raw).strip().upper()

    if choice not in VALID_CHOICES:
        raise ValueError("Please answer with A, B, C or D.")

    return choice


def is_correct(question, choice):
    """Return True if choice is the question's correct option."""
    return choice == question["correct"]


def score_answers(answers, questions=QUESTIONS):
    """Return the number of correct answers (one point each).

    answers maps a question id to the choice actually submitted. Missing or
    invalid answers score zero; the score never depends on explanations.
    """
    return sum(
        1
        for question in questions
        if answers.get(question["id"]) is not None
        and is_correct(question, answers[question["id"]])
    )


def format_question(question, number, total):
    """Return the text to display for one question."""
    lines = [f"\nQuestion {number} of {total}: {question['prompt']}"]

    for key in VALID_CHOICES:
        lines.append(f"  {key}. {question['options'][key]}")

    return "\n".join(lines)
