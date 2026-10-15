# CampusFlow

CampusFlow is a command-line campus IT helpdesk ticket manager written in
Python. Campus staff record technical support requests — Wi-Fi outages,
faulty laptops, broken dev environments — as tickets. The application
prioritises them automatically, assigns responsibility, tracks each ticket
from open to resolved, and saves everything to a JSON file so nothing is
lost between runs.

## Requirements

- Python 3.8 or later
- Standard library only — no package installation needed

## Run

From the project directory:

```sh
python3 main.py
```

The application loads existing tickets from `tickets.json` in the current
working directory (a missing file starts a fresh, empty collection) and
offers this menu:

1. Create ticket
2. List all tickets
3. View ticket by ID
4. View work queue
5. Assign ticket
6. Update ticket status
7. View reports
8. Search tickets
9. Add follow-up note
10. View ticket notes
11. Engineering Understanding Check
0. Exit

## How tickets work

**Creating:** enter a title, a category (`Network`, `Hardware`, `Software`,
`Other`), an urgency (`low`, `medium`, `high`) and the number of affected
users. The priority is calculated automatically and the ticket gets the next
available integer ID. Each answer is validated before the ticket is created,
and the collection is saved to disk immediately.

**Priority** is calculated from urgency and reach, first match wins:

| Rule | Priority |
|---|---|
| high urgency AND at least 10 affected users | critical |
| high urgency OR at least 10 affected users | high |
| medium urgency OR at least 3 affected users | medium |
| anything else | low |

**Status flow:** `open` → `in_progress` → `resolved`. A ticket must be
assigned to a staff member before it can move to `in_progress`, and it must be
in progress before it can be resolved. A resolved ticket has to be reopened
(status `open`) before anything else can change on it. Workflow-rule
violations print an error and return you to the menu.

**Work queue:** shows OPEN tickets only (in-progress and resolved tickets
are excluded), sorted by priority, then by ticket ID. Use Search to find
in-progress work.

**Search (read-only):** title text (case-insensitive substring) plus optional
category, status and priority filters. Supplied filters combine with logical
AND; a blank filter means "do not filter by that field"; an invalid filter
option re-prompts. Results show ID, title, category, priority, status and
assignee, and can optionally be sorted by priority then ticket ID. Search never
modifies tickets. The Open Work Queue (menu 4) is a separate view and is
unchanged.

**Follow-up notes:** each ticket holds a `notes` list. A note is
`{"note_id": "N001", "author": ..., "message": ...}` with per-ticket IDs
`N001`, `N002`, ... Notes can only be added to `open` or `in_progress` tickets;
the author cannot be blank and the message must be 5-300 characters after
trimming. A rejected note never consumes an ID, notes survive resolve and
reopen, and the next note ID continues after a reload.

**Reports:** total tickets; counts by status, priority and category; the
unresolved count (open + in_progress); the resolved count; and the resolution
percentage (resolved / total x 100). An empty dataset reports 0% without a
division error. Each ticket is counted once, by its current status.

**Engineering Understanding Check:** six multiple-choice scenario questions
about this application's behaviour. Answers must be A, B, C or D (anything else
re-prompts). One point per correct submitted answer, final score 0-6. You are
then asked to explain two answers in your own words; explanations are saved to
`learning-note.md` (gitignored) for mentor discussion and are never
auto-graded. The question bank (`campusflow/understanding_questions.py`) is
separate from the scoring logic (`campusflow/understanding_check.py`).

## Data format

`tickets.json` is a JSON list of ticket objects. Each ticket has `id`, `title`,
`category`, `urgency`, `affected_users`, `priority`, `status`, `assigned_to`
and, once a note has been added, `notes` (a list of note objects as above).
Tickets saved before notes existed have no `notes` field and remain valid.

## Where data lives

Tickets are saved to `tickets.json` in the working directory. The file is
created and maintained by the application and is not tracked by git. It is
validated on load: malformed files or duplicate/invalid ticket IDs stop the
application with a clear message rather than corrupting data.

## Run tests

```sh
python3 -m unittest discover -s tests -v
```

## Known limitations

- Single-user tool; there is no authentication or multi-user locking.
- Tickets are held in memory and rewritten to disk on each change; it is not
  designed for very large collections.
- The report and queue views validate every ticket on each call, so a
  hand-edited `tickets.json` with an invalid field is rejected rather than
  partially displayed.

## Team and Contributions

- **Partner A — ticket creation, validation and priority engine:**
  Okoh Destiny (melodexs). PR: #13 (retry-on-invalid-input),
  #17 (validation and notes), #18 (choice hints), #19 (quiz revision)
- **Partner B — workflow, work queue, reports and storage:**
  Michael Oogwu (dab00gieman). PR: #14 (docs and storage polish),
  #15 (search, insights and understanding check), #16 (open work queue),
  #20 (question polish)

Each partner keeps their own entries in `docs/ai-learning-log.md`.
