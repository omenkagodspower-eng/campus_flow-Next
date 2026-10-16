from campusflow.notes import add_note, get_notes
from campusflow.queue import get_work_queue
from campusflow.reports import generate_ticket_report
from campusflow.search import VALID_PRIORITIES, search_tickets
from campusflow.storage import load_tickets, save_tickets
from campusflow.tickets import create_ticket, VALID_CATEGORIES, calculate_priority
from campusflow.workflow import assign_ticket, update_ticket_status
from campusflow.understanding_check import (
    format_question,
    is_correct,
    parse_choice,
    score_answers,
)
from campusflow.understanding_questions import QUESTIONS
from campusflow.validation import VALID_STATUSES

DATA_FILE = "tickets.json"
LEARNING_NOTE_FILE = "learning-note.md"
CANCEL_WORD = "back"


class CancelledInput(Exception):
    """Raised when the user types the cancel word at a prompt."""


def ask(prompt, parse):
    """Ask a question until parse() accepts the answer.

    parse is a function that takes the raw input string, raises ValueError
    with a clear message for bad answers, and returns the cleaned value.
    EOFError and KeyboardInterrupt are not caught here; main() handles them.
    """
    while True:
        raw = input(f"{prompt} (or '{CANCEL_WORD}' to cancel): ")

        if raw.strip().lower() == CANCEL_WORD:
            raise CancelledInput()

        try:
            return parse(raw)
        except ValueError as error:
            print(f"Invalid input: {error} Please try again.")


def parse_title(raw):
    """Validate a ticket title."""
    title = raw.strip()

    if not title:
        raise ValueError("Ticket title cannot be empty.")

    return title


def parse_category(raw):
    """Validate a category against the library's accepted categories."""
    category = raw.strip().title()

    if category not in VALID_CATEGORIES:
        raise ValueError("Category must be Network, Hardware, Software, or Other.")

    return category


def parse_urgency(raw):
    """Validate urgency by reusing the library's own rule."""
    urgency = raw.strip().lower()

    calculate_priority(urgency, 1)

    return urgency


def parse_affected_users(raw):
    """Validate the affected-users count by reusing the library's rules."""
    try:
        affected_users = int(raw.strip())
    except ValueError:
        raise ValueError("Affected users must be a whole number.")

    calculate_priority("low", affected_users)

    return affected_users


def parse_staff_name(raw):
    """Validate a staff member's name."""
    staff_member = raw.strip()

    if not staff_member:
        raise ValueError("Staff member name cannot be empty.")

    return staff_member


def parse_status(raw):
    """Validate a status against the library's accepted statuses."""
    status = raw.strip().lower()

    if status not in VALID_STATUSES:
        raise ValueError("Status must be open, in_progress, or resolved.")

    return status


def parse_author(raw):
    """Validate a note author label."""
    author = raw.strip()

    if not author:
        raise ValueError("Note author cannot be blank.")

    return author


def parse_note_message(raw):
    """Validate a note message length (5-300 characters after trimming)."""
    message = raw.strip()

    if not 5 <= len(message) <= 300:
        raise ValueError("Note message must be 5-300 characters.")

    return message


def normalise_choice(raw, valid_options):
    """Accept optional blank values and validate the cleaned choice."""
    text = raw.strip()

    if text == "":
        return None

    choice = text.lower()
    options = {option.lower(): option for option in valid_options}

    if choice not in options:
        raise ValueError("Must be one of: " + ", ".join(valid_options) + ".")

    return options[choice]


def make_filter_parser(valid_options):
    """Build a parser for an optional filter: blank means 'any'."""
    def parse(raw):
        return normalise_choice(raw, valid_options)

    return parse


def sort_by_priority(tickets):
    """Return tickets ordered by the project priority ranking."""
    return sorted(
        tickets,
        key=lambda ticket: (VALID_PRIORITIES.index(ticket["priority"]), ticket["id"]),
    )


def format_ticket_row(ticket):
    """Return a compact one-line summary for a ticket."""
    return f"#{ticket['id']} | {ticket['title']}"


def make_ticket_id_parser(tickets):
    """Build a parser that accepts a whole number matching a real ticket."""
    def parse(raw):
        try:
            ticket_id = int(raw.strip())
        except ValueError:
            raise ValueError("Ticket ID must be a number.")

        if find_ticket(tickets, ticket_id) is None:
            raise ValueError("Ticket not found.")

        return ticket_id

    return parse


def display_ticket(ticket):
    """Display a ticket's details."""
    print(f"\nTicket ID: {ticket['id']}")
    print(f"Title: {ticket['title']}")
    print(f"Category: {ticket['category']}")
    print(f"Urgency: {ticket['urgency']}")
    print(f"Affected users: {ticket['affected_users']}")
    print(f"Priority: {ticket['priority']}")
    print(f"Status: {ticket['status']}")
    print(f"Assigned to: {ticket['assigned_to'] or 'Unassigned'}")


def list_tickets(tickets):
    """Display all tickets."""
    if not tickets:
        print("\nNo tickets found.")
        return

    for ticket in sorted(tickets, key=lambda item: item["id"]):
        display_ticket(ticket)


def view_ticket(tickets):
    """Display one ticket by ID."""
    ticket_id = ask("Ticket ID", make_ticket_id_parser(tickets))
    ticket = find_ticket(tickets, ticket_id)
    if ticket is None:
        print("Ticket not found.")
        return

    display_ticket(ticket)


def search_existing_tickets(tickets):
    """Search tickets using optional filters."""
    print("\n--- Search Tickets ---")
    print("Leave a filter blank to ignore it.")

    keyword = input("Title keyword: ").strip()

    print("Categories:", ", ".join(VALID_CATEGORIES))
    category = input("Category: ").strip()
    category = category or None

    print("Statuses: open, in_progress, resolved")
    status = input("Status: ").strip().lower()
    status = status or None

    print("Priorities: critical, high, medium, low")
    priority = input("Priority: ").strip().lower()
    priority = priority or None

    try:
        results = search_tickets(
            tickets,
            keyword=keyword,
            category=category,
            status=status,
            priority=priority,
        )

        if not results:
            print("\nNo matching tickets found.")
            return

        print(f"\nFound {len(results)} matching ticket(s):")

        for ticket in sorted(results, key=lambda item: item["id"]):
            display_ticket(ticket)

    except ValueError as error:
        print(f"\nError: {error}")


def create_new_ticket(tickets):
    """Collect ticket details and create a ticket."""
    title = ask("Ticket title", parse_title)
    category = ask(
        "Category (" + "/".join(VALID_CATEGORIES) + ")",
        parse_category,
    )
    urgency = ask("Urgency (low/medium/high)", parse_urgency)
    affected_users = ask(
        "Number of affected users (whole number, at least 1)",
        parse_affected_users,
    )

    try:
        ticket_id = max(
            (ticket["id"] for ticket in tickets),
            default=0,
        ) + 1

        ticket = create_ticket(
            ticket_id,
            title,
            category,
            urgency,
            affected_users,
        )

        tickets.append(ticket)
        save_tickets(tickets, DATA_FILE)

        print(f"\nTicket #{ticket_id} created successfully.")

    except ValueError as error:
        print(f"\nError: {error}")


def show_work_queue(tickets):
    """Display unresolved tickets in priority order."""
    try:
        queue = get_work_queue(tickets)

        if not queue:
            print("\nThe work queue is empty.")
            return

        print("\n--- Work Queue ---")

        for ticket in queue:
            print(
                f"#{ticket['id']} | "
                f"{ticket['priority'].upper()} | "
                f"{ticket['status']} | "
                f"{ticket['title']}"
            )

    except ValueError as error:
        print(f"\nError: {error}")


def assign_existing_ticket(tickets):
    """Assign a ticket to a staff member."""
    ticket_id = ask("Ticket ID", make_ticket_id_parser(tickets))
    ticket = find_ticket(tickets, ticket_id)
    staff_member = ask("Staff member's name", parse_staff_name)

    try:
        assign_ticket(ticket, staff_member)
        save_tickets(tickets, DATA_FILE)

        print(f"Ticket #{ticket_id} assigned successfully.")

    except ValueError as error:
        print(f"\nError: {error}")


def change_ticket_status(tickets):
    """Update the status of an existing ticket."""
    ticket_id = ask("Ticket ID", make_ticket_id_parser(tickets))
    ticket = find_ticket(tickets, ticket_id)
    new_status = ask(
        "New status (" + "/".join(VALID_STATUSES) + ")",
        parse_status,
    )

    try:
        update_ticket_status(ticket, new_status)
        save_tickets(tickets, DATA_FILE)

        print(f"Ticket #{ticket_id} status updated successfully.")

    except ValueError as error:
        print(f"\nError: {error}")


def find_ticket(tickets, ticket_id):
    """Find a ticket by its numeric ID."""
    for ticket in tickets:
        if ticket["id"] == ticket_id:
            return ticket

    return None


def add_followup_note(tickets):
    """Add a follow-up note to a ticket using the notes API."""
    ticket_id = ask("Ticket ID", make_ticket_id_parser(tickets))
    author = ask("Note author", parse_author)
    message = ask("Note message (5-300 characters)", parse_note_message)

    try:
        note = add_note(tickets, ticket_id, author, message)
        save_tickets(tickets, DATA_FILE)

        print(f"Note {note['note_id']} added to ticket #{ticket_id}.")

    except ValueError as error:
        print(f"\nError: {error}")


def view_ticket_notes(tickets):
    """Display every note on a ticket in note ID order."""
    ticket_id = ask("Ticket ID", make_ticket_id_parser(tickets))

    try:
        notes = get_notes(tickets, ticket_id)
    except ValueError as error:
        print(f"\nError: {error}")
        return

    if not notes:
        print(f"\nTicket #{ticket_id} has no notes.")
        return

    print(f"\n--- Notes for ticket #{ticket_id} ---")

    for note in notes:
        print(f"{note['note_id']} | {note['author']}: {note['message']}")


def search_tickets_view(tickets):
    """Search tickets by title text and optional combined filters (read-only)."""
    title_text = ask("Title contains (blank for any)", lambda raw: raw.strip())
    category = ask(
        "Category filter (" + "/".join(VALID_CATEGORIES) + ", blank for any)",
        make_filter_parser(VALID_CATEGORIES),
    )
    status = ask(
        "Status filter (" + "/".join(VALID_STATUSES) + ", blank for any)",
        make_filter_parser(VALID_STATUSES),
    )
    priority = ask(
        "Priority filter (" + "/".join(VALID_PRIORITIES) + ", blank for any)",
        make_filter_parser(VALID_PRIORITIES),
    )

    matches = search_tickets(tickets, title_text, category, status, priority)

    if not matches:
        print("\nNo tickets match those filters.")
        return

    sort_choice = ask(
        "Sort results by priority? (y/n, blank for no)",
        lambda raw: raw.strip().lower(),
    )

    if sort_choice in ("y", "yes"):
        matches = sort_by_priority(matches)

    print(f"\n--- Search Results ({len(matches)}) ---")

    for ticket in matches:
        print(format_ticket_row(ticket))


def run_understanding_check():
    """Run the six-question Engineering Understanding Check."""
    answers = {}

    print("\n====== Engineering Understanding Check ======")
    print("Answer each question with A, B, C or D.")

    for number, question in enumerate(QUESTIONS, start=1):
        print(format_question(question, number, len(QUESTIONS)))

        choice = ask("Your answer", parse_choice)
        answers[question["id"]] = choice

        if is_correct(question, choice):
            print("Correct.")
        else:
            print(f"Not quite. The expected answer was {question['correct']}.")

    score = score_answers(answers)
    total = len(QUESTIONS)

    print(f"\nFinal score: {score} / {total}")

    collect_explanations(answers)

    return score


def collect_explanations(answers):
    """Ask for short written explanations of two answers and save them.

    Explanations are stored in a local learning note for mentor discussion.
    They are never auto-graded, so no keyword matching happens here.
    """
    print(
        "\nPick two questions and explain, in your own words, why the "
        "correct answer is right (use an example from your code)."
    )

    valid_ids = [question["id"] for question in QUESTIONS]
    entries = []

    for round_number in (1, 2):
        question_id = ask(
            f"Explanation {round_number} of 2 - which question ("
            + ", ".join(valid_ids)
            + ")",
            lambda raw: parse_question_id(raw, valid_ids),
        )
        explanation = ask("Your explanation", parse_explanation)
        entries.append((question_id, answers[question_id], explanation))

    save_learning_note(entries)


def parse_question_id(raw, valid_ids):
    """Validate a question ID such as Q3 (case-insensitive)."""
    question_id = raw.strip().upper()

    if question_id not in valid_ids:
        raise ValueError("Choose one of: " + ", ".join(valid_ids) + ".")

    return question_id


def parse_explanation(raw):
    """Require a real sentence, not a blank or one-word answer."""
    explanation = raw.strip()

    if len(explanation.split()) < 4:
        raise ValueError("Please write at least a short sentence.")

    return explanation


def save_learning_note(entries, path=LEARNING_NOTE_FILE):
    """Append the quiz explanations to a local learning note file."""
    with open(path, "a", encoding="utf-8") as file:
        file.write("\n## Understanding Check explanations\n")

        for question_id, submitted, explanation in entries:
            file.write(
                f"- {question_id} (I answered {submitted}): {explanation}\n"
            )

    print(f"Saved your explanations to {path} for mentor discussion.")


def show_report(tickets):
    """Display ticket counts by status and priority."""
    try:
        report = generate_ticket_report(tickets)

        print("\n--- Ticket Report ---")
        print(f"Total tickets: {report['total']}")

        print("\nBy status:")
        for status, count in report["by_status"].items():
            print(f"  {status}: {count}")

        print("\nBy priority:")
        for priority, count in report["by_priority"].items():
            print(f"  {priority}: {count}")

        print("\nBy category:")
        for category, count in report["by_category"].items():
            print(f"  {category}: {count}")

        print(f"\nUnresolved (open + in_progress): {report['unresolved']}")
        print(f"Resolved: {report['resolved']}")
        print(f"Resolution rate: {report['resolution_percentage']}%")

    except ValueError as error:
        print(f"\nError: {error}")


def display_menu():
    """Display the main menu."""
    print("\n====== CampusFlow Ticket Manager ======")
    print("1. Create ticket")
    print("2. List all tickets")
    print("3. View ticket by ID")
    print("4. View work queue")
    print("5. Assign ticket")
    print("6. Update ticket status")
    print("7. View reports")
    print("8. Search tickets")
    print("9. Engineering Understanding Check")
    print("10. Add follow-up note")
    print("11. View ticket notes")
    print("0. Exit")


def main():
    """Run the CampusFlow command-line application."""
    try:
        tickets = load_tickets(DATA_FILE)
    except ValueError as error:
        print(f"Unable to load tickets: {error}")
        return

    print(f"Loaded {len(tickets)} ticket(s).")

    while True:
        try:
            display_menu()
            choice = input("Choose an option: ").strip()

            if choice == "1":
                create_new_ticket(tickets)
            elif choice == "2":
                list_tickets(tickets)
            elif choice == "3":
                view_ticket(tickets)
            elif choice == "4":
                show_work_queue(tickets)
            elif choice == "5":
                assign_existing_ticket(tickets)
            elif choice == "6":
                change_ticket_status(tickets)
            elif choice == "7":
                show_report(tickets)
            elif choice == "8":
                search_existing_tickets(tickets)
            elif choice == "9":
                run_understanding_check()
            elif choice == "10":
                add_followup_note(tickets)
            elif choice == "11":
                view_ticket_notes(tickets)
            elif choice == "0":
                print("Goodbye!")
                break

            else:
                print("Invalid option. Please choose a valid menu option.")

        except CancelledInput:
            print("\nCancelled. Returning to the main menu.")

        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()
