import json
import re
from pathlib import Path

from campusflow.tickets import calculate_priority
from campusflow.validation import (
    VALID_CATEGORIES,
    VALID_URGENCIES,
    VALID_STATUSES,
    validate_ticket_details,
    validate_ticket_id,
)


def validate_tickets(tickets):
    """Validate an entire collection of tickets and their notes."""

from campusflow.notes import NOTE_MAX_LENGTH, NOTE_MIN_LENGTH
from campusflow.search import VALID_PRIORITIES
from campusflow.tickets import calculate_priority, VALID_CATEGORIES
from campusflow.workflow import VALID_STATUSES

REQUIRED_FIELDS = (
    "id",
    "title",
    "category",
    "urgency",
    "affected_users",
    "priority",
    "status",
    "assigned_to",
)


def _validate_note(note, ticket_id, seen_note_ids):
    """Validate one saved note entry against the notes module's rules."""
    if not isinstance(note, dict):
        raise ValueError(f"Ticket {ticket_id} has a damaged note entry.")

    note_id = note.get("note_id")

    if (
        not isinstance(note_id, str)
        or not note_id.startswith("N")
        or not note_id[1:].isdigit()
        or note_id in seen_note_ids
    ):
        raise ValueError(f"Ticket {ticket_id} has an invalid note ID.")

    seen_note_ids.add(note_id)

    author = note.get("author")

    if not isinstance(author, str) or not author.strip():
        raise ValueError(f"Note {note_id} must have a non-blank author.")

    message = note.get("message")

    if not isinstance(message, str):
        raise ValueError(f"Note {note_id} must have a text message.")

    if not NOTE_MIN_LENGTH <= len(message) <= NOTE_MAX_LENGTH:
        raise ValueError(
            f"Note {note_id} message must be {NOTE_MIN_LENGTH}-"
            f"{NOTE_MAX_LENGTH} characters."
        )


def _validate_notes(ticket):
    """Validate a ticket's notes list; a missing field counts as empty.

    Older files saved before notes existed may not have the field, so it is
    accepted as empty rather than rejected, matching the notes module.
    """
    notes = ticket.get("notes")

    if notes is None:
        return

    if not isinstance(notes, list):
        raise ValueError(f"Ticket {ticket['id']} notes must be a list.")

    seen_note_ids = set()

    for note in notes:
        _validate_note(note, ticket["id"], seen_note_ids)


def _validate_ticket_record(ticket):
    """Validate every field of one ticket record before it is trusted.

    Runs before the record can replace valid in-memory data, so a damaged
    entry is rejected whole instead of silently corrupting the session.
    """
    ticket_id = ticket.get("id")

    for field in REQUIRED_FIELDS:
        if field not in ticket:
            raise ValueError(
                f"Ticket {ticket_id} is missing the '{field}' field."
            )

    title = ticket["title"]

    if not isinstance(title, str) or not title.strip():
        raise ValueError(f"Ticket {ticket_id} must have a non-empty title.")

    if ticket["category"] not in VALID_CATEGORIES:
        raise ValueError(f"Ticket {ticket_id} has an invalid category.")

    if ticket["priority"] not in VALID_PRIORITIES:
        raise ValueError(f"Ticket {ticket_id} has an invalid priority.")

    if ticket["status"] not in VALID_STATUSES:
        raise ValueError(f"Ticket {ticket_id} has an invalid status.")

    assigned_to = ticket["assigned_to"]

    if assigned_to is not None and (
        not isinstance(assigned_to, str) or not assigned_to.strip()
    ):
        raise ValueError(f"Ticket {ticket_id} has an invalid assignee.")

    try:
        calculate_priority(ticket["urgency"], ticket["affected_users"])
    except ValueError as error:
        raise ValueError(f"Ticket {ticket_id}: {error}") from error

    _validate_notes(ticket)


def validate_tickets(tickets):
    """Validate that tickets form a list of unique, complete records."""
    if not isinstance(tickets, list):
        raise ValueError("The tickets file must contain a JSON list.")

    seen_ticket_ids = set()

    for ticket in tickets:
        if not isinstance(ticket, dict):
            raise ValueError("Each ticket must be a dictionary.")

        # Validate ticket ID and uniqueness.
        ticket_id = ticket.get("id")
        validate_ticket_id(ticket_id)

        if ticket_id in seen_ticket_ids:
            raise ValueError(f"Duplicate ticket ID found: {ticket_id}")

        seen_ticket_ids.add(ticket_id)

        # Validate the ticket's required details.
        validate_ticket_details(
            ticket.get("title"),
            ticket.get("category"),
            ticket.get("urgency"),
            ticket.get("affected_users"),
        )

        if ticket["category"] not in VALID_CATEGORIES:
            raise ValueError("Invalid ticket category.")

        if ticket["urgency"] not in VALID_URGENCIES:
            raise ValueError("Invalid ticket urgency.")

        # Check that the stored priority matches the ticket details.
        expected_priority = calculate_priority(
            ticket["urgency"],
            ticket["affected_users"],
        )

        if ticket.get("priority") != expected_priority:
            raise ValueError("Ticket priority does not match its details.")

        # Validate status.
        if ticket.get("status") not in VALID_STATUSES:
            raise ValueError("Ticket has an invalid status.")

        # Validate assignment.
        assigned_to = ticket.get("assigned_to")

        if assigned_to is not None:
            if not isinstance(assigned_to, str) or not assigned_to.strip():
                raise ValueError(
                    "Assigned staff member must be a nonempty name or None."
                )

        # Every ticket must have a notes list.
        notes = ticket.get("notes")

        if not isinstance(notes, list):
            raise ValueError("Ticket notes must be a list.")

        seen_note_ids = set()

        for note in notes:
            if not isinstance(note, dict):
                raise ValueError("Each note must be a dictionary.")

            note_id = note.get("note_id")

            if (
                not isinstance(note_id, str)
                or re.fullmatch(r"N\d{3,}", note_id) is None
                or int(note_id[1:]) < 1
            ):
                raise ValueError("Each note must have a valid note ID.")

            if note_id in seen_note_ids:
                raise ValueError(f"Duplicate note ID found: {note_id}")

            seen_note_ids.add(note_id)

            author = note.get("author")
            message = note.get("message")

            if not isinstance(author, str) or not author.strip():
                raise ValueError("Each note must have a nonempty author.")

            if not isinstance(message, str):
                raise ValueError("Each note message must be text.")

            if not 5 <= len(message.strip()) <= 300:
                raise ValueError(
                    "Each note message must contain between 5 and 300 characters."
                )

        _validate_ticket_record(ticket)


def save_tickets(tickets, filename="tickets.json"):
    """Validate and save tickets to a JSON file."""

    # Validate everything before opening the destination file.
    validate_tickets(tickets)

    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(tickets, file, indent=4)
        file.write("\n")


def load_tickets(filename="tickets.json"):
    """Load and validate tickets from a JSON file.


    Return an empty list if the file does not exist.
    Raise a clear error if the JSON is malformed or invalid, so corrupted
    data is never handed to the rest of the application.
    """
    path = Path(filename)

    if not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8") as file:
            tickets = json.load(file)

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON in {path}: {error}"
        ) from error

    # Support older records that predate the notes feature.
    # Only add an empty notes list when the field is absent.
    if isinstance(tickets, list):
        for ticket in tickets:
            if isinstance(ticket, dict) and "notes" not in ticket:
                ticket["notes"] = []

    validate_tickets(tickets)

    return tickets