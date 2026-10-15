from campusflow.queue import get_work_queue
from campusflow.reports import generate_ticket_report
from campusflow.search import search_tickets
from campusflow.storage import load_tickets, save_tickets
from campusflow.tickets import create_ticket, VALID_CATEGORIES
from campusflow.workflow import assign_ticket, update_ticket_status
from campusflow.quiz import run_quiz

DATA_FILE = "tickets.json"


def display_ticket(ticket):
    """Display a ticket's details."""
    print(f"\nTicket ID: {ticket['id']}")
    print(f"Title: {ticket['title']}")
    print(f"Category: {ticket['category']}")
    print(f"Urgency: {ticket['urgency']}")
    print(f"Affected users: {ticket['affected_users']}")
    print(f"Priority: {ticket['priority']}")
    print(f"Status: {ticket['status']}")
    print(f"Assigned to: {ticket['assigned_to'] or 'Unassigned'}")


def list_tickets(tickets):
    """Display all tickets."""
    if not tickets:
        print("\nNo tickets found.")
        return

    for ticket in sorted(tickets, key=lambda item: item["id"]):
        display_ticket(ticket)


def view_ticket(tickets):
    """Display one ticket by ID."""
    try:
        ticket_id = int(input("Ticket ID: "))
    except ValueError:
        print("\nError: Ticket ID must be a number.")
        return

    ticket = find_ticket(tickets, ticket_id)
    if ticket is None:
        print("Ticket not found.")
        return

    display_ticket(ticket)


def search_existing_tickets(tickets):
    """Search tickets using optional filters."""
    print("\n--- Search Tickets ---")
    print("Leave a filter blank to ignore it.")

    keyword = input("Title keyword: ").strip()

    print("Categories:", ", ".join(VALID_CATEGORIES))
    category = input("Category: ").strip()
    category = category or None

    print("Statuses: open, in_progress, resolved")
    status = input("Status: ").strip().lower()
    status = status or None

    print("Priorities: critical, high, medium, low")
    priority = input("Priority: ").strip().lower()
    priority = priority or None

    try:
        results = search_tickets(
            tickets,
            keyword=keyword,
            category=category,
            status=status,
            priority=priority,
        )

        if not results:
            print("\nNo matching tickets found.")
            return

        print(f"\nFound {len(results)} matching ticket(s):")

        for ticket in sorted(results, key=lambda item: item["id"]):
            display_ticket(ticket)

    except ValueError as error:
        print(f"\nError: {error}")


def create_new_ticket(tickets):
    """Collect ticket details and create a ticket."""
    try:
        ticket_id = max(
            (ticket["id"] for ticket in tickets),
            default=0,
        ) + 1

        title = input("Ticket title: ").strip()

        print("Categories:", ", ".join(VALID_CATEGORIES))
        category = input("Category: ").strip()

        urgency = input("Urgency (low/medium/high): ").strip().lower()
        affected_users = int(input("Number of affected users: "))

        ticket = create_ticket(
            ticket_id,
            title,
            category,
            urgency,
            affected_users,
        )

        tickets.append(ticket)
        save_tickets(tickets, DATA_FILE)

        print(f"\nTicket #{ticket_id} created successfully.")

    except ValueError as error:
        print(f"\nError: {error}")


def show_work_queue(tickets):
    """Display unresolved tickets in priority order."""
    try:
        queue = get_work_queue(tickets)

        if not queue:
            print("\nThe work queue is empty.")
            return

        print("\n--- Work Queue ---")

        for ticket in queue:
            print(
                f"#{ticket['id']} | "
                f"{ticket['priority'].upper()} | "
                f"{ticket['status']} | "
                f"{ticket['title']}"
            )

    except ValueError as error:
        print(f"\nError: {error}")


def assign_existing_ticket(tickets):
    """Assign a ticket to a staff member."""
    try:
        ticket_id = int(input("Ticket ID: "))
        ticket = find_ticket(tickets, ticket_id)

        if ticket is None:
            print("Ticket not found.")
            return

        staff_member = input("Staff member's name: ")
        assign_ticket(ticket, staff_member)
        save_tickets(tickets, DATA_FILE)

        print(f"Ticket #{ticket_id} assigned successfully.")

    except ValueError as error:
        print(f"\nError: {error}")


def change_ticket_status(tickets):
    """Update the status of an existing ticket."""
    try:
        ticket_id = int(input("Ticket ID: "))
        ticket = find_ticket(tickets, ticket_id)

        if ticket is None:
            print("Ticket not found.")
            return

        print("Available statuses: open, in_progress, resolved")
        new_status = input("New status: ").strip().lower()

        update_ticket_status(ticket, new_status)
        save_tickets(tickets, DATA_FILE)

        print(f"Ticket #{ticket_id} status updated successfully.")

    except ValueError as error:
        print(f"\nError: {error}")


def find_ticket(tickets, ticket_id):
    """Find a ticket by its numeric ID."""
    for ticket in tickets:
        if ticket["id"] == ticket_id:
            return ticket

    return None


def show_report(tickets):
    """Display ticket counts by status and priority."""
    try:
        report = generate_ticket_report(tickets)

        print("\n--- Ticket Report ---")
        print(f"Total tickets: {report['total']}")

        print("\nBy status:")
        for status, count in report["by_status"].items():
            print(f"  {status}: {count}")

        print("\nBy priority:")
        for priority, count in report["by_priority"].items():
            print(f"  {priority}: {count}")

    except ValueError as error:
        print(f"\nError: {error}")


def display_menu():
    """Display the main menu."""
    print("\n====== CampusFlow Ticket Manager ======")
    print("1. Create ticket")
    print("2. List all tickets")
    print("3. View ticket by ID")
    print("4. View work queue")
    print("5. Assign ticket")
    print("6. Update ticket status")
    print("7. View reports")
    print("8. Search tickets")
    print("9. Take understanding quiz")
    print("0. Exit")


def main():
    """Run the CampusFlow command-line application."""
    try:
        tickets = load_tickets(DATA_FILE)
    except ValueError as error:
        print(f"Unable to load tickets: {error}")
        return

    print(f"Loaded {len(tickets)} ticket(s).")

    while True:
        try:
            display_menu()
            choice = input("Choose an option: ").strip()

            if choice == "1":
                create_new_ticket(tickets)
            elif choice == "2":
                list_tickets(tickets)
            elif choice == "3":
                view_ticket(tickets)
            elif choice == "4":
                show_work_queue(tickets)
            elif choice == "5":
                assign_existing_ticket(tickets)
            elif choice == "6":
                change_ticket_status(tickets)
            elif choice == "7":
                show_report(tickets)
            elif choice == "8":
                search_existing_tickets(tickets)
            elif choice == "0":
                print("Goodbye!")
                break
            elif choice == "9":
                  run_quiz()
            else:
                print("Invalid option. Please choose 0–8.")

        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()
