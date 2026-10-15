def add_note(ticket, author, message):
    """Add a validated note to an open or in-progress ticket."""

    # Validate the ticket before making any changes.
    if not isinstance(ticket, dict):
        raise ValueError("Ticket must be a dictionary.")

    if ticket.get("status") not in ("open", "in_progress"):
        raise ValueError("Notes can only be added to active tickets.")

    # Validate the author.
    if not isinstance(author, str) or not author.strip():
        raise ValueError("Note author cannot be empty.")

    # Validate and normalize the message.
    if not isinstance(message, str):
        raise ValueError("Note message must be text.")

    message = message.strip()

    if not 5 <= len(message) <= 300:
        raise ValueError(
            "Note message must contain between 5 and 300 characters."
        )

    # Validate existing notes before adding another one.
    notes = ticket.get("notes")

    if not isinstance(notes, list):
        raise ValueError("Ticket notes must be a list.")

    existing_ids = set()

    for existing_note in notes:
        if not isinstance(existing_note, dict):
            raise ValueError("Each note must be a dictionary.")

        note_id = existing_note.get("note_id")

        if (
            not isinstance(note_id, str)
            or not note_id.startswith("N")
            or not note_id[1:].isdigit()
            or int(note_id[1:]) < 1
        ):
            raise ValueError("Each note must have a valid note ID.")

        if note_id in existing_ids:
            raise ValueError(f"Duplicate note ID found: {note_id}")

        existing_ids.add(note_id)

        existing_author = existing_note.get("author")
        existing_message = existing_note.get("message")

        if not isinstance(existing_author, str) or not existing_author.strip():
            raise ValueError("Each note must have a valid author.")

        if (
            not isinstance(existing_message, str)
            or not 5 <= len(existing_message.strip()) <= 300
        ):
            raise ValueError("Each note must have a valid message.")

    # Generate the next ID only after validation succeeds.
    highest_id = max(
        (int(note_id[1:]) for note_id in existing_ids),
        default=0,
    )
    next_id = highest_id + 1
    new_note_id = f"N{next_id:03d}"

    note = {
        "note_id": new_note_id,
        "author": author.strip(),
        "message": message,
    }

    # This is the first mutation of the ticket.
    notes.append(note)

    return note
=======
"""Follow-up notes for tickets.

CONTRACT (agreed interface with Engineer A, who owns the notes data layer):

    add_note(tickets, ticket_id, author, message) -> note dict
        Raises ValueError with a clear message on any rejection and leaves
        the ticket collection completely unchanged when it does.

    get_notes(tickets, ticket_id) -> list of note dicts in note_id order
        Raises ValueError if the ticket does not exist.

This module is the interface the CLI calls. Engineer A's implementation of the
same functions replaces the bodies below without any change to main.py.
"""

NOTE_MIN_LENGTH = 5
NOTE_MAX_LENGTH = 300
NOTE_ALLOWED_STATUSES = ("open", "in_progress")


def _find_ticket(tickets, ticket_id):
    """Return the ticket with ticket_id or raise ValueError."""
    for ticket in tickets:
        if ticket["id"] == ticket_id:
            return ticket

    raise ValueError("Ticket not found.")


def _notes_of(ticket):
    """Return the ticket's notes list, treating a missing field as empty.

    Raise ValueError (never TypeError) if the field exists but is not a list
    of note dictionaries, so a damaged record is rejected, not crashed on.
    """
    notes = ticket.get("notes", [])

    if not isinstance(notes, list):
        raise ValueError("Ticket notes are damaged: expected a list.")

    for note in notes:
        if (
            not isinstance(note, dict)
            or not isinstance(note.get("note_id"), str)
            or not note["note_id"].startswith("N")
            or not note["note_id"][1:].isdigit()
        ):
            raise ValueError("Ticket notes are damaged: invalid note entry.")

    return notes


def next_note_id(ticket):
    """Return the next per-ticket note ID (N001, N002, ...).

    Based on the highest existing note number, so IDs never collide after a
    reload.
    """
    highest = 0

    for note in _notes_of(ticket):
        highest = max(highest, int(note["note_id"][1:]))

    return f"N{highest + 1:03d}"


def add_note(tickets, ticket_id, author, message):
    """Add a follow-up note to an open or in_progress ticket.

    All validation happens before anything is changed, so a rejected note
    never consumes a note ID or alters the ticket.
    """
    ticket = _find_ticket(tickets, ticket_id)
    _notes_of(ticket)

    if ticket.get("status") not in NOTE_ALLOWED_STATUSES:
        raise ValueError("Reopen the ticket before adding a note.")

    if not isinstance(author, str) or not author.strip():
        raise ValueError("Note author cannot be blank.")

    if not isinstance(message, str):
        raise ValueError("Note message must be text.")

    cleaned = message.strip()

    if not NOTE_MIN_LENGTH <= len(cleaned) <= NOTE_MAX_LENGTH:
        raise ValueError(
            f"Note message must be {NOTE_MIN_LENGTH}-{NOTE_MAX_LENGTH} "
            "characters."
        )

    note = {
        "note_id": next_note_id(ticket),
        "author": author.strip(),
        "message": cleaned,
    }

    if "notes" not in ticket:
        ticket["notes"] = []

    ticket["notes"].append(note)
    return note


def get_notes(tickets, ticket_id):
    """Return a ticket's notes in note ID order (empty list if none)."""
    ticket = _find_ticket(tickets, ticket_id)

    return sorted(
        _notes_of(ticket),
        key=lambda note: int(note["note_id"][1:]),
    )
