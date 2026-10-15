import unittest

from campusflow.reports import (
    calculate_resolution_percentage,
    generate_ticket_report,
)
from campusflow.workflow import assign_ticket, update_ticket_status


def make_ticket(ticket_id, category, priority, status):
    return {
        "id": ticket_id,
        "title": f"Ticket {ticket_id}",
        "category": category,
        "urgency": "medium",
        "affected_users": 3,
        "priority": priority,
        "status": status,
        "assigned_to": "Ada" if status != "open" else None,
    }


class TestEnhancedReport(unittest.TestCase):
    def setUp(self):
        self.tickets = [
            make_ticket(1, "Network", "critical", "open"),
            make_ticket(2, "Network", "high", "in_progress"),
            make_ticket(3, "Hardware", "medium", "resolved"),
            make_ticket(4, "Software", "low", "resolved"),
        ]

    def test_empty_report_is_zero_percent_without_error(self):
        report = generate_ticket_report([])

        self.assertEqual(report["total"], 0)
        self.assertEqual(report["unresolved"], 0)
        self.assertEqual(report["resolved"], 0)
        self.assertEqual(report["resolution_percentage"], 0.0)

    def test_zero_total_percentage_does_not_divide_by_zero(self):
        self.assertEqual(calculate_resolution_percentage(0, 0), 0.0)

    def test_counts_match_known_fixture(self):
        report = generate_ticket_report(self.tickets)

        self.assertEqual(report["total"], 4)
        self.assertEqual(
            report["by_status"],
            {"open": 1, "in_progress": 1, "resolved": 2},
        )
        self.assertEqual(
            report["by_priority"],
            {"critical": 1, "high": 1, "medium": 1, "low": 1},
        )
        self.assertEqual(
            report["by_category"],
            {"Network": 2, "Hardware": 1, "Software": 1, "Other": 0},
        )

    def test_unresolved_includes_open_and_in_progress(self):
        report = generate_ticket_report(self.tickets)

        self.assertEqual(report["unresolved"], 2)
        self.assertEqual(report["resolved"], 2)

    def test_in_progress_ticket_counts_as_unresolved_not_resolved(self):
        tickets = [make_ticket(1, "Other", "low", "in_progress")]

        report = generate_ticket_report(tickets)

        self.assertEqual(report["unresolved"], 1)
        self.assertEqual(report["resolved"], 0)

    def test_resolution_percentage(self):
        report = generate_ticket_report(self.tickets)

        self.assertEqual(report["resolution_percentage"], 50.0)

    def test_status_counts_always_add_up_to_total(self):
        report = generate_ticket_report(self.tickets)

        self.assertEqual(sum(report["by_status"].values()), report["total"])
        self.assertEqual(
            report["unresolved"] + report["resolved"], report["total"]
        )

    def test_counts_follow_resolve_then_reopen_without_double_counting(self):
        ticket = make_ticket(1, "Network", "high", "open")
        assign_ticket(ticket, "Ada")
        tickets = [ticket]

        update_ticket_status(ticket, "in_progress")
        update_ticket_status(ticket, "resolved")
        resolved_report = generate_ticket_report(tickets)

        self.assertEqual(resolved_report["resolved"], 1)
        self.assertEqual(resolved_report["unresolved"], 0)
        self.assertEqual(resolved_report["resolution_percentage"], 100.0)

        update_ticket_status(ticket, "open")
        reopened_report = generate_ticket_report(tickets)

        # Counted by CURRENT status only: no ticket appears in two statuses.
        self.assertEqual(reopened_report["resolved"], 0)
        self.assertEqual(reopened_report["unresolved"], 1)
        self.assertEqual(reopened_report["resolution_percentage"], 0.0)
        self.assertEqual(
            sum(reopened_report["by_status"].values()), reopened_report["total"]
        )

    def test_report_without_category_field_still_works(self):
        """Older stored tickets may lack a category; they must not crash."""
        tickets = [{"id": 1, "priority": "low", "status": "open"}]

        report = generate_ticket_report(tickets)

        self.assertEqual(report["total"], 1)
        self.assertEqual(sum(report["by_category"].values()), 0)

    def test_original_report_keys_are_preserved(self):
        report = generate_ticket_report(self.tickets)

        for key in ("total", "by_status", "by_priority"):
            self.assertIn(key, report)

    def test_report_does_not_modify_tickets(self):
        import copy

        before = copy.deepcopy(self.tickets)

        generate_ticket_report(self.tickets)

        self.assertEqual(self.tickets, before)


if __name__ == "__main__":
    unittest.main()
