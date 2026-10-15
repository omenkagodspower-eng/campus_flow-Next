import unittest

from campusflow.reports import generate_ticket_report


class TestTicketReports(unittest.TestCase):

    def setUp(self):
        self.tickets = [
            {
                "id": 1,
                "title": "Login issue",
                "category": "Software",
                "priority": "high",
                "status": "resolved",
                "assigned_to": "Alex",
            },
            {
                "id": 2,
                "title": "Network issue",
                "category": "Network",
                "priority": "medium",
                "status": "open",
                "assigned_to": None,
            },
            {
                "id": 3,
                "title": "Computer issue",
                "category": "Hardware",
                "priority": "low",
                "status": "in_progress",
                "assigned_to": "Sam",
            },
        ]

    def test_report_counts_total_status_priority_and_category(self):
        report = generate_ticket_report(self.tickets)

        self.assertEqual(report["total"], 3)
        self.assertEqual(report["by_status"]["resolved"], 1)
        self.assertEqual(report["by_status"]["open"], 1)
        self.assertEqual(report["by_status"]["in_progress"], 1)
        self.assertEqual(report["by_priority"]["high"], 1)
        self.assertEqual(report["by_category"]["Software"], 1)
        self.assertEqual(report["by_category"]["Network"], 1)

    def test_report_counts_resolved_and_unresolved(self):
        report = generate_ticket_report(self.tickets)

        self.assertEqual(report["resolved"], 1)
        self.assertEqual(report["unresolved"], 2)

    def test_report_calculates_resolution_percentage(self):
        report = generate_ticket_report(self.tickets)

        self.assertAlmostEqual(
            report["resolution_percentage"], 100 / 3
        )

    def test_empty_report_returns_zero_values(self):
        report = generate_ticket_report([])

        self.assertEqual(report["total"], 0)
        self.assertEqual(report["resolved"], 0)
        self.assertEqual(report["unresolved"], 0)
        self.assertEqual(report["resolution_percentage"], 0.0)

    def test_reopened_ticket_counts_by_current_status(self):
        tickets = [dict(self.tickets[0])]
        tickets[0]["status"] = "open"

        report = generate_ticket_report(tickets)

        self.assertEqual(report["by_status"]["open"], 1)
        self.assertEqual(report["resolved"], 0)
        self.assertEqual(report["unresolved"], 1)
        self.assertEqual(report["resolution_percentage"], 0.0)

    def test_invalid_status_raises_error(self):
        tickets = [dict(self.tickets[0])]
        tickets[0]["status"] = "pending"

        with self.assertRaises(ValueError):
            generate_ticket_report(tickets)


if __name__ == "__main__":
    unittest.main()
