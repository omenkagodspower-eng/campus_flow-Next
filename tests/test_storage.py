import json
import tempfile
import unittest
from pathlib import Path

from campusflow.storage import save_tickets, load_tickets


class TestTicketStorage(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.filepath = Path(self.temp_dir.name) / "tickets.json"

        self.tickets = [
            {
                "id": 1,
                "title": "Wi-Fi problem",
                "category": "Network",
                "urgency": "medium",
                "affected_users": 5,
                "priority": "medium",
                "status": "open",
                "assigned_to": None,
                "notes": [],
            }
        ]

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_tickets_creates_json_file(self):
        save_tickets(self.tickets, self.filepath)

        self.assertTrue(self.filepath.exists())

    def test_saved_file_ends_with_newline(self):
        save_tickets(self.tickets, self.filepath)

        contents = self.filepath.read_text(encoding="utf-8")
        self.assertTrue(contents.endswith("\n"))

    def test_save_creates_missing_parent_folder(self):
        nested_path = (
            Path(self.temp_dir.name) / "data" / "tickets.json"
        )

        save_tickets(self.tickets, nested_path)

        self.assertTrue(nested_path.exists())
        self.assertEqual(load_tickets(nested_path), self.tickets)

    def test_load_tickets_returns_saved_tickets(self):
        save_tickets(self.tickets, self.filepath)

        loaded = load_tickets(self.filepath)

        self.assertEqual(loaded, self.tickets)

    def test_missing_file_returns_empty_list(self):
        loaded = load_tickets(self.filepath)

        self.assertEqual(loaded, [])

    def test_malformed_json_raises_clear_error(self):
        self.filepath.write_text(
            "{invalid json",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "Invalid JSON"):
            load_tickets(self.filepath)

    def test_json_must_contain_a_list(self):
        self.filepath.write_text(
            json.dumps({"id": 1}),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "JSON list"):
            load_tickets(self.filepath)

    def test_saves_and_loads_ticket_notes(self):
        self.tickets[0]["notes"] = [
            {
                "note_id": "N001",
                "author": "Ada",
                "message": "Checked the router.",
            }
        ]

        save_tickets(self.tickets, self.filepath)

        loaded = load_tickets(self.filepath)

        self.assertEqual(
            loaded[0]["notes"],
            self.tickets[0]["notes"],
        )

    def test_rejects_duplicate_ticket_ids(self):
        duplicate_tickets = [
            self.tickets[0].copy(),
            self.tickets[0].copy(),
        ]

        with self.assertRaisesRegex(ValueError, "Duplicate ticket ID"):
            save_tickets(duplicate_tickets, self.filepath)

    def test_invalid_save_does_not_overwrite_existing_file(self):
        save_tickets(self.tickets, self.filepath)
        original_content = self.filepath.read_text(encoding="utf-8")

        invalid_tickets = [
            {
                "id": 2,
                "title": "Invalid ticket",
                "category": "Network",
                "urgency": "medium",
                "affected_users": 5,
                "priority": "low",
                "status": "open",
                "assigned_to": None,
                "notes": [],
            }
        ]

        with self.assertRaises(ValueError):
            save_tickets(invalid_tickets, self.filepath)

        updated_content = self.filepath.read_text(encoding="utf-8")

        self.assertEqual(updated_content, original_content)

    def test_rejects_invalid_note_when_loading(self):
        invalid_tickets = [
            {
                **self.tickets[0],
                "notes": [
                    {
                        "note_id": "N001",
                        "author": "",
                        "message": "Checked the router.",
                    }
                ],
            }
        ]

        self.filepath.write_text(
            json.dumps(invalid_tickets),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "author"):
            load_tickets(self.filepath)

    def test_note_id_continuity_after_reload(self):
        from campusflow.notes import add_note

        self.tickets[0]["notes"] = [
            {
                "note_id": "N001",
                "author": "Ada",
                "message": "Initial router check.",
            },
            {
                "note_id": "N003",
                "author": "Chidi",
                "message": "Replacement router ordered.",
            },
        ]

        save_tickets(self.tickets, self.filepath)

        loaded_tickets = load_tickets(self.filepath)
        ticket = loaded_tickets[0]

        note = add_note(
            ticket,
            "Ada",
            "Router replacement completed.",
        )

        self.assertEqual(note["note_id"], "N004")
        self.assertEqual(len(ticket["notes"]), 3)


def valid_ticket():
    """Return a complete, valid ticket record as saved on disk."""
    return {
        "id": 1,
        "title": "Wi-Fi problem",
        "category": "Network",
        "urgency": "high",
        "affected_users": 5,
        "priority": "high",
        "status": "open",
        "assigned_to": None,
    }


def valid_note():
    """Return a complete, valid note entry as saved on disk."""
    return {
        "note_id": "N001",
        "author": "Staff A",
        "message": "Router restarted, watching for drops",
    }


class TestDeepRecordValidation(unittest.TestCase):
    """The whole collection is validated before it replaces real data."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.filepath = Path(self.temp_dir.name) / "tickets.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_tickets(self, tickets):
        self.filepath.write_text(
            json.dumps(tickets, indent=4), encoding="utf-8"
        )

    def assert_rejected(self):
        with self.assertRaises(ValueError):
            load_tickets(self.filepath)

    def test_valid_ticket_with_notes_loads(self):
        ticket = valid_ticket()
        ticket["notes"] = [valid_note()]
        self.write_tickets([ticket])

        loaded = load_tickets(self.filepath)

        self.assertEqual(loaded[0]["notes"], [valid_note()])

    def test_ticket_without_notes_field_is_accepted(self):
        self.write_tickets([valid_ticket()])

        loaded = load_tickets(self.filepath)

        self.assertEqual(loaded, [valid_ticket()])

    def test_missing_required_field_is_rejected(self):
        ticket = valid_ticket()
        del ticket["assigned_to"]
        self.write_tickets([ticket])
        self.assert_rejected()

    def test_blank_title_is_rejected(self):
        ticket = valid_ticket()
        ticket["title"] = "   "
        self.write_tickets([ticket])
        self.assert_rejected()

    def test_invalid_category_is_rejected(self):
        ticket = valid_ticket()
        ticket["category"] = "Electricity"
        self.write_tickets([ticket])
        self.assert_rejected()

    def test_invalid_urgency_is_rejected(self):
        ticket = valid_ticket()
        ticket["urgency"] = "urgent"
        self.write_tickets([ticket])
        self.assert_rejected()

    def test_boolean_affected_users_is_rejected(self):
        ticket = valid_ticket()
        ticket["affected_users"] = True
        self.write_tickets([ticket])
        self.assert_rejected()

    def test_zero_affected_users_is_rejected(self):
        ticket = valid_ticket()
        ticket["affected_users"] = 0
        self.write_tickets([ticket])
        self.assert_rejected()

    def test_invalid_priority_is_rejected(self):
        ticket = valid_ticket()
        ticket["priority"] = "urgent"
        self.write_tickets([ticket])
        self.assert_rejected()

    def test_invalid_status_is_rejected(self):
        ticket = valid_ticket()
        ticket["status"] = "closed"
        self.write_tickets([ticket])
        self.assert_rejected()

    def test_blank_assignee_is_rejected(self):
        ticket = valid_ticket()
        ticket["assigned_to"] = "   "
        self.write_tickets([ticket])
        self.assert_rejected()

    def test_non_text_assignee_is_rejected(self):
        ticket = valid_ticket()
        ticket["assigned_to"] = 7
        self.write_tickets([ticket])
        self.assert_rejected()

    def test_notes_that_are_not_a_list_are_rejected(self):
        ticket = valid_ticket()
        ticket["notes"] = "N001"
        self.write_tickets([ticket])
        self.assert_rejected()

    def test_invalid_note_entry_is_rejected(self):
        ticket = valid_ticket()
        ticket["notes"] = [{"note_id": "X1", "author": "A", "message": "ok note"}]
        self.write_tickets([ticket])
        self.assert_rejected()

    def test_duplicate_note_ids_are_rejected(self):
        ticket = valid_ticket()
        ticket["notes"] = [valid_note(), valid_note()]
        self.write_tickets([ticket])
        self.assert_rejected()

    def test_blank_note_author_is_rejected(self):
        ticket = valid_ticket()
        note = valid_note()
        note["author"] = "  "
        ticket["notes"] = [note]
        self.write_tickets([ticket])
        self.assert_rejected()

    def test_too_short_note_message_is_rejected(self):
        ticket = valid_ticket()
        note = valid_note()
        note["message"] = "no"
        ticket["notes"] = [note]
        self.write_tickets([ticket])
        self.assert_rejected()

    def test_note_message_boundaries_are_accepted(self):
        ticket = valid_ticket()
        short = valid_note()
        short["message"] = "abcde"
        long = valid_note()
        long["note_id"] = "N002"
        long["message"] = "x" * 300
        ticket["notes"] = [short, long]
        self.write_tickets([ticket])

        loaded = load_tickets(self.filepath)

        self.assertEqual(len(loaded[0]["notes"]), 2)

    def test_save_rejects_damaged_ticket(self):
        ticket = valid_ticket()
        ticket["status"] = "closed"

        with self.assertRaises(ValueError):
            save_tickets([ticket], self.filepath)

        self.assertFalse(self.filepath.exists())

    def test_rejected_load_keeps_existing_records(self):
        self.write_tickets([valid_ticket()])
        session = load_tickets(self.filepath)

        ticket = valid_ticket()
        ticket["id"] = 1
        ticket["title"] = ""
        self.write_tickets([ticket])

        with self.assertRaises(ValueError):
            load_tickets(self.filepath)

        self.assertEqual(session[0]["title"], "Wi-Fi problem")


if __name__ == "__main__":
    unittest.main()