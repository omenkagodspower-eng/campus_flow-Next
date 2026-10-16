import copy
import tempfile
import unittest
from pathlib import Path

from campusflow.notes import add_note, get_notes, next_note_id
from campusflow.storage import load_tickets, save_tickets
from campusflow.tickets import create_ticket


def open_ticket(ticket_id=1, **extra):
    ticket = {"id": ticket_id, "status": "open"}
    ticket.update(extra)
    return ticket


class TestAddNote(unittest.TestCase):
    def test_first_note_gets_n001(self):
        tickets = [open_ticket()]

        note = add_note(tickets, 1, "Mentor A", "Wi-Fi router reboot attempted")

        self.assertEqual(note["note_id"], "N001")
        self.assertEqual(tickets[0]["notes"], [note])

    def test_note_ids_are_per_ticket(self):
        tickets = [open_ticket(1), open_ticket(2)]

        add_note(tickets, 1, "A", "First ticket note")
        add_note(tickets, 1, "A", "Second ticket note")
        note = add_note(tickets, 2, "A", "Other ticket note")

        self.assertEqual(note["note_id"], "N001")

    def test_in_progress_ticket_accepts_notes(self):
        tickets = [open_ticket(status="in_progress")]

        note = add_note(tickets, 1, "A", "Started investigating")

        self.assertEqual(note["note_id"], "N001")

    def test_resolved_ticket_rejects_note_and_stays_unchanged(self):
        tickets = [open_ticket(status="resolved")]
        before = copy.deepcopy(tickets)

        with self.assertRaises(ValueError):
            add_note(tickets, 1, "A", "Too late for this one")

        self.assertEqual(tickets, before)

    def test_rejected_notes_do_not_consume_an_id(self):
        tickets = [open_ticket()]

        for author, message in (("A", "hi"), ("   ", "valid message"),
                                ("A", "x" * 301)):
            with self.assertRaises(ValueError):
                add_note(tickets, 1, author, message)

        note = add_note(tickets, 1, "A", "Finally a valid note")

        self.assertEqual(note["note_id"], "N001")

    def test_message_length_boundaries(self):
        for length, accepted in ((4, False), (5, True), (300, True), (301, False)):
            tickets = [open_ticket()]

            if accepted:
                add_note(tickets, 1, "A", "x" * length)
            else:
                with self.assertRaises(ValueError):
                    add_note(tickets, 1, "A", "x" * length)

    def test_length_is_measured_after_trimming(self):
        tickets = [open_ticket()]

        with self.assertRaises(ValueError):
            add_note(tickets, 1, "A", "     ab     ")

    def test_message_and_author_are_stored_trimmed(self):
        tickets = [open_ticket()]

        note = add_note(tickets, 1, "  Mentor A  ", "  Rebooted the router  ")

        self.assertEqual(note["author"], "Mentor A")
        self.assertEqual(note["message"], "Rebooted the router")

    def test_non_string_author_or_message_rejected(self):
        for author, message in ((None, "valid message"), (123, "valid message"),
                                ("A", None), ("A", 12345678)):
            tickets = [open_ticket()]

            with self.assertRaises(ValueError):
                add_note(tickets, 1, author, message)

            self.assertNotIn("notes", tickets[0])

    def test_unknown_ticket_rejected(self):
        with self.assertRaises(ValueError):
            add_note([open_ticket()], 99, "A", "valid message here")

    def test_notes_survive_resolve_and_reopen(self):
        tickets = [open_ticket()]
        add_note(tickets, 1, "A", "Before resolving")

        tickets[0]["status"] = "resolved"
        self.assertEqual(len(get_notes(tickets, 1)), 1)

        tickets[0]["status"] = "open"
        note = add_note(tickets, 1, "A", "After reopening")

        self.assertEqual(note["note_id"], "N002")
        self.assertEqual(len(get_notes(tickets, 1)), 2)


class TestNoteIdContinuity(unittest.TestCase):
    def test_next_id_follows_highest_existing_number(self):
        ticket = open_ticket(notes=[{"note_id": "N010"}, {"note_id": "N002"}])

        self.assertEqual(next_note_id(ticket), "N011")

    def test_next_id_after_reload_does_not_collide(self):
        ticket = open_ticket(notes=[
            {"note_id": "N001", "author": "A", "message": "first one"},
            {"note_id": "N002", "author": "A", "message": "second one"},
        ])

        self.assertEqual(next_note_id(ticket), "N003")

    def test_get_notes_returns_id_order(self):
        tickets = [open_ticket(notes=[
            {"note_id": "N002", "author": "B", "message": "second one"},
            {"note_id": "N001", "author": "A", "message": "first one"},
        ])]

        ids = [note["note_id"] for note in get_notes(tickets, 1)]

        self.assertEqual(ids, ["N001", "N002"])


class TestBugHunter(unittest.TestCase):
    """Bug-hunter test for Engineer A's notes data layer.

    Initial state : ticket 1 is open and its "notes" field is null (what a
                    hand-edited or half-migrated JSON file can contain).
    Input         : add_note(tickets, 1, "Mentor A", "valid message here")
    Expected      : a friendly ValueError and a completely unchanged ticket.
    Actual (found): TypeError: 'NoneType' object is not iterable - a raw
                    crash that the CLI would not catch.
    Code change   : notes.py now validates the notes field shape in
                    _notes_of() BEFORE any mutation, so damaged data is
                    rejected with ValueError instead of crashing.
    Invariant     : an invalid action leaves the whole collection unchanged.
    """

    DAMAGED_SHAPES = (None, "text", {"a": 1}, [None], [{"note_id": "X1"}],
                      [{"nope": 1}])

    def test_damaged_notes_field_is_rejected_not_crashed_on(self):
        for damaged in self.DAMAGED_SHAPES:
            tickets = [open_ticket(notes=damaged)]
            before = copy.deepcopy(tickets)

            with self.assertRaises(ValueError):
                add_note(tickets, 1, "Mentor A", "valid message here")

            self.assertEqual(tickets, before)

    def test_viewing_damaged_notes_is_rejected_not_crashed_on(self):
        for damaged in self.DAMAGED_SHAPES:
            tickets = [open_ticket(notes=damaged)]

            with self.assertRaises(ValueError):
                get_notes(tickets, 1)


class TestNoteIdsAcrossReload(unittest.TestCase):
    """Note IDs must continue from the highest existing ID after reload."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.filepath = Path(self.temp_dir.name) / "tickets.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_note_ids_continue_after_save_and_reload(self):
        tickets = [
            create_ticket(1, "Wi-Fi problem", "Network", "medium", 2)
        ]

        add_note(tickets, 1, "Staff A", "Router restarted, monitoring")

        save_tickets(tickets, self.filepath)
        reloaded = load_tickets(self.filepath)

        note = add_note(reloaded, 1, "Staff A", "Connection looks stable now")

        self.assertEqual(note["note_id"], "N002")


if __name__ == "__main__":
    unittest.main()

