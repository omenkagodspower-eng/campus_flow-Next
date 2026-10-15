import json
from pathlib import Path


QUESTIONS = [
    {
        "question": "Which Python data type stores key-value pairs?",
        "options": {
            "A": "List",
            "B": "Dictionary",
            "C": "String",
            "D": "Tuple",
        },
        "answer": "B",
    },
    {
        "question": "Which keyword defines a function in Python?",
        "options": {
            "A": "func",
            "B": "define",
            "C": "def",
            "D": "function",
        },
        "answer": "C",
    },
    {
        "question": "Which data format does CampusFlow use to store tickets?",
        "options": {
            "A": "JSON",
            "B": "MP3",
            "C": "PNG",
            "D": "HTML",
        },
        "answer": "A",
    },
    {
        "question": "Which collection uses square brackets?",
        "options": {
            "A": "Dictionary",
            "B": "Tuple",
            "C": "Set",
            "D": "List",
        },
        "answer": "D",
    },
    {
        "question": "Which status indicates that work has been completed?",
        "options": {
            "A": "open",
            "B": "resolved",
            "C": "in_progress",
            "D": "pending",
        },
        "answer": "B",
    },
    {
        "question": "Which keyword sends a value back from a function?",
        "options": {
            "A": "print",
            "B": "input",
            "C": "return",
            "D": "break",
        },
        "answer": "C",
    },
]


def get_input(prompt):
    """Read input and handle a closed input stream."""
    try:
        return input(prompt)
    except EOFError:
        print("\nQuiz cancelled because no input was available.")
        return None


def run_quiz():
    """Run six multiple-choice questions and collect explanations."""
    score = 0
    explanations = []

    print("\n--- CampusFlow Understanding Quiz ---")
    print("Choose A, B, C, or D for each question.")

    for number, question in enumerate(QUESTIONS, start=1):
        print(f"\nQuestion {number}: {question['question']}")

        for letter, option in question["options"].items():
            print(f"  {letter}. {option}")

        while True:
            choice = get_input("Your answer: ")

            if choice is None:
                return

            choice = choice.strip().upper()

            if choice in ("A", "B", "C", "D"):
                break

            print("Invalid choice. Please enter A, B, C, or D.")

        if choice == question["answer"]:
            print("Correct!")
            score += 1
        else:
            print(f"Incorrect. Correct answer: {question['answer']}.")

        if number in (2, 5):
            explanation = get_input(
                "Briefly explain your answer for mentor discussion: "
            )

            if explanation is None:
                return

            explanations.append({
                "question": question["question"],
                "answer": choice,
                "explanation": explanation.strip(),
            })

    print(f"\nQuiz complete! Your score: {score}/{len(QUESTIONS)}")

    print("\n--- Explanations for Mentor Discussion ---")

    for item in explanations:
        print(f"\nQuestion: {item['question']}")
        print(f"Your answer: {item['answer']}")
        print(
            "Your explanation: "
            f"{item['explanation'] or '(No explanation provided)'}"
        )

    save = get_input("\nSave your explanations? (y/n): ")

    if save is None:
        print("Explanations were not saved.")
        return

    if save.strip().lower() == "y":
        file_path = Path("quiz_explanations.json")
        existing = []

        if file_path.exists():
            try:
                existing = json.loads(
                    file_path.read_text(encoding="utf-8")
                )
                if not isinstance(existing, list):
                    existing = []
            except (json.JSONDecodeError, OSError):
                existing = []

        existing.append({
            "score": score,
            "total": len(QUESTIONS),
            "explanations": explanations,
        })

        try:
            file_path.write_text(
                json.dumps(existing, indent=4),
                encoding="utf-8",
            )
            print("Explanations saved to quiz_explanations.json.")
        except OSError as error:
            print(f"Could not save explanations: {error}")
    else:
        print("Explanations were not saved.")


if __name__ == "__main__":
    run_quiz()
