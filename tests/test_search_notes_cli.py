import copy
import unittest
from unittest.mock import patch

import main


def make_ticket(ticket_id, title, category, priority, status, assigned_to=None):
    return {
        "id": ticket_id,
        "title": title,
        "category": category,
        "urgency": "high",
        "affected_users": 5,
        "priority": priority,
        "status": status,
        "assigned_to": assigned_to,
    }


def run_cli(function, tickets, answers):
    """Run one CLI action with scripted answers; always finite."""
    with patch("builtins.input", side_effect=answers), \
            patch("builtins.print") as printed, \
            patch("main.save_tickets") as save:
        function(tickets)

    output = "\n".join(str(c.args[0]) for c in printed.call_args_list)
    return output, save


class TestSearchView(unittest.TestCase):
    def setUp(self):
        self.tickets = [
            make_ticket(1, "Wifi down", "Network", "critical", "open"),
            make_ticket(2, "WIFI slow", "Network", "medium", "resolved"),
            make_ticket(3, "Projector", "Hardware", "low", "open"),
        ]

    def test_combined_filters_through_the_cli(self):
        output, _ = run_cli(
            main.search_tickets_view,
            self.tickets,
            ["wifi", "network", "open", "", ""],
        )

        self.assertIn("#1 | Wifi down", output)
        self.assertNotIn("#2", output)
        self.assertNotIn("#3", output)

    def test_invalid_filter_reprompts_then_accepts(self):
        output, _ = run_cli(
            main.search_tickets_view,
            self.tickets,
            ["", "printers", "hardware", "", "", ""],
        )

        self.assertIn("Invalid input: Must be one of:", output)
        self.assertIn("#3 | Projector", output)

    def test_no_matches_shows_friendly_message(self):
        output, _ = run_cli(
            main.search_tickets_view,
            self.tickets,
            ["nothing like this", "", "", ""],
        )

        self.assertIn("No tickets match those filters.", output)

    def test_search_never_saves_or_changes_data(self):
        before = copy.deepcopy(self.tickets)

        _, save = run_cli(
            main.search_tickets_view,
            self.tickets,
            ["wifi", "", "", "", "y"],
        )

        save.assert_not_called()
        self.assertEqual(self.tickets, before)

    def test_priority_sort_option_orders_results(self):
        output, _ = run_cli(
            main.search_tickets_view,
            self.tickets,
            ["", "", "", "", "y"],
        )

        self.assertLess(output.index("#1 |"), output.index("#2 |"))
        self.assertLess(output.index("#2 |"), output.index("#3 |"))


class TestNotesMenus(unittest.TestCase):
    def setUp(self):
        self.tickets = [
            make_ticket(1, "Wifi down", "Network", "high", "open", "Ada"),
        ]

    def test_brief_example_note_lifecycle(self):
        """open -> N001 -> N002 -> resolve -> N003 rejected -> reopen -> N003."""
        run_cli(main.add_followup_note, self.tickets,
                ["1", "Mentor A", "Wi-Fi router reboot attempted"])
        run_cli(main.add_followup_note, self.tickets,
                ["1", "Mentor B", "Investigating switch ports"])

        self.tickets[0]["status"] = "resolved"
        output, _ = run_cli(main.add_followup_note, self.tickets,
                            ["1", "Mentor C", "Should be rejected now"])

        self.assertIn("Reopen the ticket before adding a note.", output)
        self.assertEqual(len(self.tickets[0]["notes"]), 2)

        self.tickets[0]["status"] = "open"
        output, _ = run_cli(main.add_followup_note, self.tickets,
                            ["1", "Mentor C", "Accepted after reopening"])

        self.assertIn("Note N003 added", output)
        self.assertEqual(
            [n["note_id"] for n in self.tickets[0]["notes"]],
            ["N001", "N002", "N003"],
        )

    def test_short_message_is_reprompted_without_consuming_id(self):
        output, _ = run_cli(main.add_followup_note, self.tickets,
                            ["1", "Mentor A", "hi", "A proper follow-up"])

        self.assertIn("Note message must be 5-300 characters.", output)
        self.assertEqual(self.tickets[0]["notes"][0]["note_id"], "N001")

    def test_blank_author_is_reprompted(self):
        output, _ = run_cli(main.add_followup_note, self.tickets,
                            ["1", "   ", "Mentor A", "A proper follow-up"])

        self.assertIn("Note author cannot be blank.", output)
        self.assertEqual(self.tickets[0]["notes"][0]["author"], "Mentor A")

    def test_rejected_note_saves_nothing(self):
        self.tickets[0]["status"] = "resolved"
        before = copy.deepcopy(self.tickets)

        _, save = run_cli(main.add_followup_note, self.tickets,
                          ["1", "Mentor A", "This will be rejected"])

        save.assert_not_called()
        self.assertEqual(self.tickets, before)

    def test_view_notes_in_id_order(self):
        self.tickets[0]["notes"] = [
            {"note_id": "N002", "author": "B", "message": "Second note here"},
            {"note_id": "N001", "author": "A", "message": "First note here"},
        ]

        output, _ = run_cli(main.view_ticket_notes, self.tickets, ["1"])

        self.assertLess(output.index("N001"), output.index("N002"))

    def test_view_notes_on_ticket_without_notes(self):
        output, _ = run_cli(main.view_ticket_notes, self.tickets, ["1"])

        self.assertIn("has no notes", output)

    def test_resolved_ticket_keeps_notes_visible(self):
        self.tickets[0]["notes"] = [
            {"note_id": "N001", "author": "A", "message": "Earlier note kept"},
        ]
        self.tickets[0]["status"] = "resolved"

        output, _ = run_cli(main.view_ticket_notes, self.tickets, ["1"])

        self.assertIn("Earlier note kept", output)

    def test_unknown_ticket_id_reprompts(self):
        output, _ = run_cli(main.view_ticket_notes, self.tickets, ["99", "1"])

        self.assertIn("Invalid input: Ticket not found.", output)


class TestMainMenuChoices(unittest.TestCase):
    @patch("main.load_tickets", return_value=[])
    def test_invalid_menu_choice_is_handled_not_a_crash(self, _load):
        with patch("builtins.input", side_effect=["42", "abc", "0"]), \
                patch("builtins.print") as printed:
            main.main()

        output = "\n".join(str(c.args[0]) for c in printed.call_args_list)
        self.assertIn("Invalid option", output)
        self.assertIn("Goodbye!", output)

    @patch("main.load_tickets", return_value=[])
    def test_new_menu_entries_are_listed(self, _load):
        with patch("builtins.input", side_effect=["0"]), \
                patch("builtins.print") as printed:
            main.main()

        output = "\n".join(str(c.args[0]) for c in printed.call_args_list)
        for entry in (
            "Search tickets",
            "Add follow-up note",
            "View ticket notes",
            "Engineering Understanding Check",
        ):
            self.assertIn(entry, output)


if __name__ == "__main__":
    unittest.main()
