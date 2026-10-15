import unittest

from campusflow.search import search_tickets


class TestTicketSearch(unittest.TestCase):

    def setUp(self):
        self.tickets = [
            {
                "id": 1,
                "title": "Cannot Login",
                "category": "Software",
                "urgency": "high",
                "affected_users": 2,
                "priority": "high",
                "status": "open",
                "assigned_to": None,
            },
            {
                "id": 2,
                "title": "Network Connection Failed",
                "category": "Network",
                "urgency": "medium",
                "affected_users": 5,
                "priority": "medium",
                "status": "in_progress",
                "assigned_to": "Alex",
            },
        ]

    def test_search_is_case_insensitive(self):
        results = search_tickets(self.tickets, keyword="LOGIN")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], 1)

    def test_search_combines_filters(self):
        results = search_tickets(
            self.tickets,
            category="Software",
            status="open",
            priority="high",
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], 1)

    def test_search_without_filters_returns_all_tickets(self):
        results = search_tickets(self.tickets)
        self.assertEqual(len(results), 2)

    def test_search_with_no_matches_returns_empty_list(self):
        results = search_tickets(self.tickets, keyword="Printer")
        self.assertEqual(results, [])

    def test_search_does_not_modify_original_tickets(self):
        original_title = self.tickets[0]["title"]
        search_tickets(self.tickets, keyword="LOGIN")
        self.assertEqual(self.tickets[0]["title"], original_title)

    def test_invalid_category_raises_error(self):
        with self.assertRaises(ValueError):
            search_tickets(self.tickets, category="Food")

    def test_invalid_status_raises_error(self):
        with self.assertRaises(ValueError):
            search_tickets(self.tickets, status="pending")

    def test_invalid_priority_raises_error(self):
        with self.assertRaises(ValueError):
            search_tickets(self.tickets, priority="urgent")


if __name__ == "__main__":
    unittest.main()
