"""Ticket note helpers.

The project uses two compatible note APIs during the transition:
- a single-ticket helper used by storage validation tests
- a list-based helper used by the CLI and the ticket management tests
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
    """Return the notes list for a ticket or raise ValueError if damaged."""
    notes = ticket.get("notes", [])

    if not isinstance(notes, list):
        raise ValueError("Ticket notes are damaged: expected a list.")

    for note in notes:
        if not isinstance(note, dict):
            raise ValueError("Ticket notes are damaged: invalid note entry.")

        note_id = note.get("note_id")
        if (
            not isinstance(note_id, str)
            or not note_id.startswith("N")
            or not note_id[1:].isdigit()
        ):
            raise ValueError("Ticket notes are damaged: invalid note entry.")

    return notes


def next_note_id(ticket):
    """Return the next available note ID for the given ticket."""
    highest = 0

    for note in _notes_of(ticket):
        note_id = note.get("note_id")
        if isinstance(note_id, str) and note_id.startswith("N"):
            digits = note_id[1:]
            if digits.isdigit():
                highest = max(highest, int(digits))

    return f"N{highest + 1:03d}"


def _validate_note_fields(author, message):
    """Validate note author and message content."""
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

    return author.strip(), cleaned


def _add_note_to_ticket(ticket, author, message):
    """Add a note to a single ticket dict in place."""
    if not isinstance(ticket, dict):
        raise ValueError("Ticket must be a dictionary.")

    if ticket.get("status") not in NOTE_ALLOWED_STATUSES:
        raise ValueError("Reopen the ticket before adding a note.")

    notes = ticket.get("notes", [])
    if notes is None or not isinstance(notes, list):
        raise ValueError("Ticket notes are damaged: expected a list.")

    for existing_note in notes:
        if not isinstance(existing_note, dict):
            raise ValueError("Ticket notes are damaged: invalid note entry.")

        note_id = existing_note.get("note_id")
        if (
            not isinstance(note_id, str)
            or not note_id.startswith("N")
            or not note_id[1:].isdigit()
        ):
            raise ValueError("Ticket notes are damaged: invalid note entry.")

        author_value = existing_note.get("author")
        msg_value = existing_note.get("message")
        if not isinstance(author_value, str) or not author_value.strip():
            raise ValueError("Each note must have a valid author.")

        if not isinstance(msg_value, str) or not 5 <= len(msg_value.strip()) <= 300:
            raise ValueError("Each note must have a valid message.")

    author, cleaned = _validate_note_fields(author, message)
    note_id = next_note_id(ticket)
    note = {"note_id": note_id, "author": author, "message": cleaned}
    notes.append(note)
    ticket["notes"] = notes
    return note


def add_note(ticket_or_tickets, ticket_id_or_author, author_or_message=None, message=None):
    """Support both the dict-style and ticket-list style APIs."""
    if isinstance(ticket_or_tickets, dict):
        if message is not None:
            raise TypeError("Single-ticket add_note accepts only (ticket, author, message).")
        return _add_note_to_ticket(ticket_or_tickets, ticket_id_or_author, author_or_message)

    if message is None:
        raise ValueError("Note message must be text.")

    tickets = ticket_or_tickets
    ticket_id = ticket_id_or_author
    author = author_or_message
    ticket = _find_ticket(tickets, ticket_id)
    _notes_of(ticket)

    if ticket.get("status") not in NOTE_ALLOWED_STATUSES:
        raise ValueError("Reopen the ticket before adding a note.")

    author, cleaned = _validate_note_fields(author, message)
    note = {
        "note_id": next_note_id(ticket),
        "author": author,
        "message": cleaned,
    }

    if "notes" not in ticket or ticket["notes"] is None:
        ticket["notes"] = []
    elif not isinstance(ticket["notes"], list):
        raise ValueError("Ticket notes are damaged: expected a list.")

    ticket["notes"].append(note)
    return note


def get_notes(tickets_or_ticket, ticket_id=None):
    """Return notes for a single ticket or for a ticket collection."""
    if ticket_id is None and isinstance(tickets_or_ticket, dict):
        ticket = tickets_or_ticket
        return sorted(_notes_of(ticket), key=lambda note: int(note["note_id"][1:]))

    ticket = _find_ticket(tickets_or_ticket, ticket_id)
    return sorted(_notes_of(ticket), key=lambda note: int(note["note_id"][1:]))
