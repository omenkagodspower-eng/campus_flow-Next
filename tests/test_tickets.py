
import unittest

from campusflow.tickets import calculate_priority, create_ticket


class TestCalculatePriority(unittest.TestCase):

    def test_critical_priority(self):
        self.assertEqual(calculate_priority("high", 10), "critical")
        self.assertEqual(calculate_priority("high", 15), "critical")

    def test_high_priority_from_urgency(self):
        self.assertEqual(calculate_priority("high", 2), "high")

    def test_high_priority_from_affected_users(self):
        self.assertEqual(calculate_priority("low", 10), "high")

    def test_medium_priority_from_urgency(self):
        self.assertEqual(calculate_priority("medium", 1), "medium")

    def test_medium_priority_from_affected_users(self):
        self.assertEqual(calculate_priority("low", 3), "medium")

    def test_low_priority(self):
        self.assertEqual(calculate_priority("low", 1), "low")

    def test_invalid_urgency(self):
        with self.assertRaises(ValueError):
            calculate_priority("urgent", 5)

    def test_zero_affected_users(self):
        with self.assertRaises(ValueError):
            calculate_priority("low", 0)

    def test_negative_affected_users(self):
        with self.assertRaises(ValueError):
            calculate_priority("low", -2)

    def test_non_integer_affected_users(self):
        with self.assertRaises(ValueError):
            calculate_priority("low", 2.5)


class TestCreateTicket(unittest.TestCase):

    def test_creates_ticket_with_correct_fields(self):
        ticket = create_ticket(
            1, "Campus Wi-Fi is down", "Network", "high", 12
        )

        self.assertEqual(ticket["id"], 1)
        self.assertEqual(ticket["title"], "Campus Wi-Fi is down")
        self.assertEqual(ticket["category"], "Network")
        self.assertEqual(ticket["urgency"], "high")
        self.assertEqual(ticket["affected_users"], 12)
        self.assertEqual(ticket["priority"], "critical")
        self.assertEqual(ticket["status"], "open")
        self.assertIsNone(ticket["assigned_to"])
        self.assertEqual(ticket["notes"], [])

    def test_strips_extra_spaces_from_title(self):
        ticket = create_ticket(
            2, "  Printer problem  ", "Hardware", "low", 1
        )
        self.assertEqual(ticket["title"], "Printer problem")

    def test_rejects_empty_title(self):
        with self.assertRaises(ValueError):
            create_ticket(1, "   ", "Network", "low", 1)

    def test_rejects_invalid_category(self):
        with self.assertRaises(ValueError):
            create_ticket(1, "Wi-Fi problem", "Electricity", "low", 1)

    def test_rejects_invalid_ticket_id(self):
        with self.assertRaises(ValueError):
            create_ticket(0, "Wi-Fi problem", "Network", "low", 1)

    def test_new_ticket_starts_with_empty_notes(self):
        ticket = create_ticket(
            1, "Wi-Fi problem", "Network", "low", 1
        )
        self.assertEqual(ticket["notes"], [])

    def test_rejects_non_integer_ticket_id(self):
        with self.assertRaises(ValueError):
            create_ticket("one", "Wi-Fi problem", "Network", "low", 1)


if __name__ == "__main__":
    unittest.main()
