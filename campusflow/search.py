VALID_CATEGORIES = ("Network", "Hardware", "Software", "Other")
VALID_STATUSES = ("open", "in_progress", "resolved")
VALID_PRIORITIES = ("critical", "high", "medium", "low")


def search_tickets(
    tickets,
    keyword="",
    category=None,
    status=None,
    priority=None,
):
    """Search tickets using optional filters."""

    if category is not None and category not in VALID_CATEGORIES:
        raise ValueError("Invalid category.")

    if status is not None and status not in VALID_STATUSES:
        raise ValueError("Invalid status.")

    if priority is not None and priority not in VALID_PRIORITIES:
        raise ValueError("Invalid priority.")

    results = []
    keyword = keyword.strip().casefold()

    for ticket in tickets:
        if keyword and keyword not in ticket["title"].casefold():
            continue

        if category and ticket["category"] != category:
            continue

        if status and ticket["status"] != status:
            continue

        if priority and ticket["priority"] != priority:
            continue

        results.append(ticket)

    return results
