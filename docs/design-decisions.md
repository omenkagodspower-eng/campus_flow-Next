# Design Decisions — CampusFlow

Team: Okoh Destiny (Partner A, repository owner), Michael Oogwu (Partner B)
Repository: melodexs/campus_flow

This document describes the code as it actually is on `main`. Every claim was
checked against the source; where behaviour is planned to change, it is
marked as such.

## 1. Ticket Structure

Every ticket is a dictionary with exactly eight fields:

- `id` — positive integer (1, 2, 3, ...)
- `title` — non-empty string
- `category` — one of `Network`, `Hardware`, `Software`, `Other`
- `urgency` — one of `low`, `medium`, `high`
- `affected_users` — positive integer (bool rejected)
- `priority` — one of `critical`, `high`, `medium`, `low` (calculated, never typed)
- `status` — one of `open`, `in_progress`, `resolved`
- `assigned_to` — staff name string, or `None` while unassigned

## 2. Ticket IDs

IDs are plain positive integers, generated as one above the highest existing
ID in the collection. Uniqueness is enforced by `validate_tickets` on every
save and load, so IDs remain unique across restarts.

## 3. Priority Rules

`calculate_priority(urgency, affected_users)` in `tickets.py` applies these
rules in order — the first match wins:

1. High urgency AND at least 10 affected users → `critical`
2. High urgency OR at least 10 affected users → `high`
3. Medium urgency OR at least 3 affected users → `medium`
4. Otherwise → `low`

The order matters: a high-urgency ticket with 10 affected users is
`critical`, not `high`.

## 4. Status Workflow

New tickets start as `open`. The normal flow is
`open → in_progress → resolved`. `update_ticket_status` in `workflow.py`
enforces:

- `in_progress` requires the ticket to be assigned first
- `open` tickets cannot jump straight to `resolved` (they must be started)
- a `resolved` ticket only accepts `open` (explicit reopen) before any other
  change
- the current status must itself be valid before any transition

## 5. Assignment Rules

`assign_ticket` in `workflow.py` rejects empty or whitespace-only names and
rejects changes to `resolved` tickets (they must be reopened first).
Assignment is required before a ticket can move to `in_progress`.

## 6. Work Queue

`get_work_queue` in `queue.py` includes tickets whose status is `open` ONLY —
in-progress and resolved tickets are excluded — sorted by priority (critical
first) and then by ticket ID. Inputs are validated: each ticket must be a
dictionary with a valid priority, status and positive integer ID, and
in-progress tickets present in the collection are still validated even though
they are not queued.

History: before CampusFlow Next, the queue included every unresolved ticket
(open and in-progress). The sprint brief requires open tickets only, so this
was corrected with a targeted regression test; see PR for
`fix/open-work-queue`. In-progress work is visible via Search (menu 8) with
the status filter, and in the Reports counts.

## 7. JSON Persistence

Tickets are stored in `tickets.json` in the working directory by default.
`save_tickets` validates the collection, creates the destination folder if it
does not exist, and writes indented JSON ending with a trailing newline.
`load_tickets` returns an empty list when the file is missing, and raises a
clear `ValueError` when the JSON is malformed or fails validation (not a
list, non-dictionary entries, invalid or duplicate IDs). The data file is
gitignored; it is local runtime state.

Saved notes are validated with the same depth as tickets: every note entry
must be a dictionary with a `note_id` in `N###` form that is unique within
the ticket, a non-blank `author`, and a text `message` within the 5-300
character limits enforced by the notes module. A ticket saved before notes
existed may omit the `notes` field; it is accepted as empty, matching the
notes module's own rule, so old files still load.

## 8. Testing

Run the suite from the project root:

    python3 -m unittest discover -s tests -v

Tests use only the standard library `unittest` plus `unittest.mock.patch` for
CLI input/output. Library code is tested without mocking; only `main.py`
needs mocks.

## 9. Error-Handling Style

Library modules (`campusflow/*.py`) never call `input()` or `print()`. On bad
data they raise `ValueError` with a clear, specific message. `main.py` is the
only module that reads input and prints; it catches `ValueError` at the action
boundary, prints the message, and returns to the menu. `EOFError` and
`KeyboardInterrupt` exit the application cleanly.

## 10. Conventions

- Python 3.8+ compatible syntax, standard library only, no dependencies.
- Four-space indentation, double quotes, docstrings on every function.
- Module constants in upper case at the top of the module
  (`VALID_CATEGORIES`, `VALID_STATUSES`, `PRIORITY_ORDER`, `PRIORITIES`).
- Each library module owns one concern: creation/priority (`tickets.py`),
  workflow (`workflow.py`), queue (`queue.py`), reports (`reports.py`),
  persistence (`storage.py`); `main.py` owns all interaction.

## 11. Search, Insights and Understanding Check (Engineer B)

- `search.py` is pure: `search_tickets(tickets, title_text, category, status,
  priority)` returns a new list and never mutates its input. Filters combine
  with AND because a staff member narrowing a search expects every added
  filter to shrink the results, not widen them. Title matching uses
  `casefold()`, which handles more Unicode cases than `lower()`. Matching is
  substring-only; there is no fuzzy matching, so `wi-fi` does not match `wifi`.
- Sorting results uses `(priority rank, numeric ticket ID)`. IDs are compared as
  integers, so ticket 10 sorts after ticket 2 (text comparison would not).
- The original Open Work Queue (`queue.py`) is deliberately untouched; the
  priority-sorted search view is a separate option.
- `reports.generate_ticket_report` keeps its original keys and adds
  `by_category`, `unresolved`, `resolved` and `resolution_percentage`. A zero
  total reports 0.0% instead of dividing by zero.
- `notes.py` is the interface the CLI calls for notes:
  `add_note(tickets, ticket_id, author, message)` and
  `get_notes(tickets, ticket_id)`. Both raise `ValueError` on rejection and
  validate before mutating, so a rejected action leaves the collection
  unchanged. A damaged `notes` field is rejected with `ValueError` rather than
  crashing.
- The understanding check keeps data (`understanding_questions.py`), scoring
  (`understanding_check.py`) and interaction (`main.py`) in separate places so
  scoring is testable without typing.
