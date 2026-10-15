"""Question bank for the Engineering Understanding Check.

Data only: no scoring and no input/output lives here. Each question has an
id, a scenario prompt, four options keyed A-D, and the correct key.

Every scenario matches behaviour that is verified by the test suite, so the
correct option describes what the application actually does.
"""

QUESTIONS = (
    {
        "id": "Q1",
        "prompt": (
            "Ticket 1 is open and unassigned. A user tries to move it to "
            "in_progress. What should the application do?"
        ),
        "options": {
            "A": "Reject it and keep the ticket exactly as it is",
            "B": "Accept it, then ask for an assignee afterwards",
            "C": "Reject it and change the status to resolved",
            "D": "Start it anyway and leave the assignee blank",
        },
        "correct": "A",
    },
    {
        "id": "Q2",
        "prompt": (
            "The app has zero tickets. What should the report's resolution "
            "percentage display?"
        ),
        "options": {
            "A": "Show 100%, since nothing is unresolved",
            "B": "Show N/A and skip the percentage",
            "C": "Wait until at least one ticket exists before showing a report",
            "D": "Show 0%",
        },
        "correct": "D",
    },
    {
        "id": "Q3",
        "prompt": (
            "Filter title='wifi', category='Network', status='open'. "
            "Which records should match?"
        ),
        "options": {
            "A": "Any record matching at least one supplied filter",
            "B": "Only records matching every supplied filter",
            "C": "All network records",
            "D": "All open records",
        },
        "correct": "B",
    },
    {
        "id": "Q4",
        "prompt": (
            "A resolved ticket receives 'Add note'. What should happen?"
        ),
        "options": {
            "A": "Reject it and require the ticket to be reopened first",
            "B": "Reopen the ticket automatically and add the note",
            "C": "Accept it, but only if the author is not blank",
            "D": "Accept it and flag the note for review later",
        },
        "correct": "A",
    },
    {
        "id": "Q5",
        "prompt": (
            "The JSON file includes two tickets with the same ID. "
            "What should load do?"
        ),
        "options": {
            "A": "Keep the first ticket and silently drop the second",
            "B": "Load them and let later writes overwrite the duplicate",
            "C": "Reject the load without changing current memory",
            "D": "Load everything, then renumber the duplicate ticket automatically",
        },
        "correct": "C",
    },
    {
        "id": "Q6",
        "prompt": (
            "Ticket 1 has note N001. A note with only 3 characters is "
            "rejected, then a valid note is added to the same ticket. "
            "What ID does the valid note get?"
        ),
        "options": {
            "A": "N003, because the rejected note used N002",
            "B": "N001, because IDs restart after a rejection",
            "C": "No ID, because the ticket is locked after a rejection",
            "D": "N002, because rejected notes do not consume an ID",
        },
        "correct": "D",
    },
)
