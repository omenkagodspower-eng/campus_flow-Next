import unittest
from unittest.mock import patch

import main


def run_with_inputs(function, answers):
    """Run a CLI function with scripted input answers and captured output.

    Every answer list must be finite so a bug cannot hang a test.
    """
    with patch("builtins.input", side_effect=answers) as mock_input, \
            patch("builtins.print") as printed:
        result = function()

    output = "\n".join(str(call.args[0]) for call in printed.call_args_list)

    return result, output, mock_input, printed


class TestTicketViewing(unittest.TestCase):
    def setUp(self):
        self.ticket = {
            "id": 4,
            "title": "Wi-Fi problem",
            "category": "Network",
            "urgency": "high",
            "affected_users": 5,
            "priority": "high",
            "status": "open",
            "assigned_to": None,
        }

    def test_views_ticket_by_id(self):
        _, output, _, _ = run_with_inputs(
            lambda: main.view_ticket([self.ticket]), ["4"]
        )

        self.assertIn("Ticket ID: 4", output)
        self.assertIn("Title: Wi-Fi problem", output)

    def test_invalid_ticket_id_then_valid(self):
        _, output, _, _ = run_with_inputs(
            lambda: main.view_ticket([self.ticket]), ["not-a-number", "4"]
        )

        self.assertIn("Invalid input: Ticket ID must be a number.", output)
        self.assertIn("Please try again.", output)
        self.assertIn("Title: Wi-Fi problem", output)

    def test_unknown_ticket_id_reprompts(self):
        _, output, _, _ = run_with_inputs(
            lambda: main.view_ticket([self.ticket]), ["99", "4"]
        )

        self.assertIn("Invalid input: Ticket not found.", output)
        self.assertIn("Please try again.", output)
        self.assertIn("Title: Wi-Fi problem", output)


class TestCreateTicketRetries(unittest.TestCase):
    def create(self, answers):
        tickets = []
        with patch("main.save_tickets") as save:
            _, output, _, _ = run_with_inputs(
                lambda: main.create_new_ticket(tickets), answers
            )

        return tickets, output, save

    def test_creates_ticket_when_all_answers_valid(self):
        tickets, output, _ = self.create(
            ["Broken projector", "hardware", "medium", "3"]
        )

        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0]["title"], "Broken projector")
        self.assertEqual(tickets[0]["category"], "Hardware")
        self.assertEqual(tickets[0]["urgency"], "medium")
        self.assertEqual(tickets[0]["affected_users"], 3)
        self.assertIn("Ticket #1 created successfully.", output)

    def test_blank_title_reprompts_and_keeps_flow(self):
        tickets, output, _ = self.create(
            ["", "Broken projector", "Hardware", "medium", "3"]
        )

        self.assertIn("Invalid input: Ticket title cannot be empty.", output)
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0]["title"], "Broken projector")

    def test_bad_category_reprompts_and_keeps_earlier_answers(self):
        tickets, output, _ = self.create(
            ["Lab printer jammed", "computers", "Hardware", "low", "1"]
        )

        self.assertIn(
            "Invalid input: Category must be Network, Hardware, Software, or Other.",
            output,
        )
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0]["title"], "Lab printer jammed")
        self.assertEqual(tickets[0]["category"], "Hardware")

    def test_bad_urgency_reprompts_using_library_message(self):
        tickets, output, _ = self.create(
            ["Wi-Fi down", "Network", "urgent", "high", "5"]
        )

        self.assertIn(
            "Invalid input: Urgency must be low, medium, or high.", output
        )
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0]["urgency"], "high")

    def test_affected_users_reprompts_through_three_bad_answers(self):
        tickets, output, _ = self.create(
            ["Wi-Fi down", "Network", "high", "bad", "0", "-2", "5"]
        )

        self.assertIn(
            "Invalid input: Affected users must be a whole number.", output
        )
        self.assertIn(
            "Invalid input: Affected users must be at least 1.", output
        )
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0]["affected_users"], 5)

    def test_back_at_first_prompt_cancels_and_creates_nothing(self):
        tickets = []

        def attempt():
            with patch("main.save_tickets"):
                run_with_inputs(
                    lambda: main.create_new_ticket(tickets), ["back"]
                )

        with self.assertRaises(main.CancelledInput):
            attempt()

        self.assertEqual(tickets, [])

    def test_back_midway_cancels_and_keeps_no_partial_ticket(self):
        tickets = []

        def attempt():
            with patch("main.save_tickets"):
                run_with_inputs(
                    lambda: main.create_new_ticket(tickets),
                    ["Wi-Fi down", "back"],
                )

        with self.assertRaises(main.CancelledInput):
            attempt()

        self.assertEqual(tickets, [])


class TestAssignTicketRetries(unittest.TestCase):
    def setUp(self):
        self.ticket = {
            "id": 4,
            "title": "Wi-Fi problem",
            "category": "Network",
            "urgency": "high",
            "affected_users": 5,
            "priority": "high",
            "status": "open",
            "assigned_to": None,
        }

    def assign(self, answers):
        tickets = [self.ticket]
        with patch("main.save_tickets") as save:
            _, output, _, _ = run_with_inputs(
                lambda: main.assign_existing_ticket(tickets), answers
            )

        return tickets, output, save

    def test_assigns_ticket_after_bad_id_and_blank_name(self):
        tickets, output, _ = self.assign(
            ["not-a-number", "99", "4", "", "Ada Lovelace"]
        )

        self.assertIn("Invalid input: Ticket ID must be a number.", output)
        self.assertIn("Invalid input: Ticket not found.", output)
        self.assertIn(
            "Invalid input: Staff member name cannot be empty.", output
        )
        self.assertEqual(tickets[0]["assigned_to"], "Ada Lovelace")
        self.assertIn("Ticket #4 assigned successfully.", output)

    def test_back_at_id_prompt_cancels_assign(self):
        tickets = [self.ticket]

        def attempt():
            with patch("main.save_tickets"):
                run_with_inputs(
                    lambda: main.assign_existing_ticket(tickets), ["back"]
                )

        with self.assertRaises(main.CancelledInput):
            attempt()

        self.assertIsNone(tickets[0]["assigned_to"])


class TestChangeStatusRetries(unittest.TestCase):
    def setUp(self):
        self.ticket = {
            "id": 4,
            "title": "Wi-Fi problem",
            "category": "Network",
            "urgency": "high",
            "affected_users": 5,
            "priority": "high",
            "status": "open",
            "assigned_to": "Ada Lovelace",
        }

    def change_status(self, answers):
        tickets = [self.ticket]
        with patch("main.save_tickets") as save:
            _, output, _, _ = run_with_inputs(
                lambda: main.change_ticket_status(tickets), answers
            )

        return tickets, output, save

    def test_bad_status_reprompts_then_updates(self):
        tickets, output, _ = self.change_status(
            ["4", "waiting", "in_progress"]
        )

        self.assertIn(
            "Invalid input: Status must be open, in_progress, or resolved.",
            output,
        )
        self.assertEqual(tickets[0]["status"], "in_progress")
        self.assertIn("Ticket #4 status updated successfully.", output)

    def test_workflow_rule_error_returns_to_menu(self):
        """Workflow rules are not input typos: error, no re-ask."""
        tickets, output, _ = self.change_status(["4", "resolved"])

        self.assertIn("Error: A ticket must be in progress", output)
        self.assertEqual(tickets[0]["status"], "open")


class TestCliExit(unittest.TestCase):
    @patch("main.load_tickets", return_value=[])
    def test_eof_exits_cleanly(self, _load):
        with patch("builtins.input", side_effect=EOFError), \
                patch("builtins.print") as printed:
            main.main()

        output = "\n".join(str(call.args[0]) for call in printed.call_args_list)
        self.assertIn("Goodbye!", output)

    @patch("main.load_tickets", return_value=[])
    def test_eof_during_action_exits_cleanly(self, _load):
        with patch("builtins.input", side_effect=["3", EOFError]), \
                patch("builtins.print") as printed:
            main.main()

        output = "\n".join(str(call.args[0]) for call in printed.call_args_list)
        self.assertIn("Goodbye!", output)

    @patch("main.load_tickets", return_value=[])
    def test_cancelled_input_returns_to_menu(self, _load):
        with patch("builtins.input", side_effect=["3", "back", "0"]), \
                patch("builtins.print") as printed:
            main.main()

        output = "\n".join(str(call.args[0]) for call in printed.call_args_list)
        self.assertIn("Cancelled. Returning to the main menu.", output)
        self.assertIn("Goodbye!", output)

    @patch("main.load_tickets", return_value=[])
    def test_eof_inside_retry_loop_exits_cleanly(self, _load):
        with patch("builtins.input", side_effect=["3", "not-a-number", EOFError]), \
                patch("builtins.print") as printed:
            main.main()

        output = "\n".join(str(call.args[0]) for call in printed.call_args_list)
        self.assertIn("Goodbye!", output)


if __name__ == "__main__":
    unittest.main()
