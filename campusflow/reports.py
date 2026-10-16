PRIORITIES = ("critical", "high", "medium", "low")
STATUSES = ("open", "in_progress", "resolved")
CATEGORIES = ("Network", "Hardware", "Software", "Other")


def calculate_resolution_percentage(total, resolved):
    """Return the percentage of resolved tickets, avoiding divide-by-zero."""
    if total <= 0:
        return 0.0
    return (resolved / total) * 100.0


def generate_ticket_report(tickets):
    """Generate ticket statistics by status, priority, and category."""

    if not isinstance(tickets, list):
        raise ValueError("Tickets must be provided as a list.")

    report = {
        "total": len(tickets),
        "by_status": {status: 0 for status in STATUSES},
        "by_priority": {priority: 0 for priority in PRIORITIES},
        "by_category": {category: 0 for category in CATEGORIES},
        "unresolved": 0,
        "resolved": 0,
        "resolution_percentage": 0.0,
    }

    for ticket in tickets:
        if not isinstance(ticket, dict):
            raise ValueError("Each ticket must be a dictionary.")

        status = ticket.get("status")
        priority = ticket.get("priority")
        category = ticket.get("category")

        if status not in STATUSES:
            raise ValueError("Each ticket must have a valid status.")
        if priority not in PRIORITIES:
            raise ValueError("Each ticket must have a valid priority.")

        if category is not None and category not in CATEGORIES:
            raise ValueError("Each ticket must have a valid category.")

        report["by_status"][status] += 1
        report["by_priority"][priority] += 1

        if category is not None:
            report["by_category"][category] += 1

        if status == "resolved":
            report["resolved"] += 1
        else:
            report["unresolved"] += 1

    report["resolution_percentage"] = calculate_resolution_percentage(
        report["total"], report["resolved"]
    )

    return report
