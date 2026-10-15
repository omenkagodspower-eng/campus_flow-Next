PRIORITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}


def get_work_queue(tickets):
    """Return open tickets ordered by priority and ticket ID."""

    if not isinstance(tickets, list):
        raise ValueError("Tickets must be provided as a list.")

    for ticket in tickets:
        if not isinstance(ticket, dict):
            raise ValueError("Each ticket must be a dictionary.")

        if ticket.get("priority") not in PRIORITY_ORDER:
            raise ValueError("Each ticket must have a valid priority.")

        ticket_id = ticket.get("id")

        if (
            not isinstance(ticket_id, int)
            or isinstance(ticket_id, bool)
            or ticket_id < 1
        ):
            raise ValueError("Each ticket must have a positive integer ID.")

        if ticket.get("status") not in ("open", "in_progress", "resolved"):
            raise ValueError("Each ticket must have a valid status.")

    open_tickets = [
        ticket
        for ticket in tickets
        if ticket["status"] == "open"
    ]

    return sorted(
        open_tickets,
        key=lambda ticket: (
            PRIORITY_ORDER[ticket["priority"]],
            ticket["id"],
        ),
    )