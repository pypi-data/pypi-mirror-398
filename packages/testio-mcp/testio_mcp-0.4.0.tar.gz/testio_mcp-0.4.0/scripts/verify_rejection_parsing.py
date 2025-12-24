import sqlite3
import json
import os

# Define the rejection reasons as provided by the user
REJECTION_REASONS = [
    {
        "key": "device_not_relevant",
        "name": "This device is not relevant and the bug will not be fixed.",
        "default_comment": "This device is not relevant and the bug will not be fixed."
    },
    {
        "key": "ignored_instructions",
        "name": "The test instructions were not followed.",
        "default_comment": "The test instructions were not followed."
    },
    {
        "key": "intended_behavior",
        "name": "The behaviour/design described here is intentional.",
        "default_comment": "The behaviour/design described here is intentional."
    },
    {
        "key": "irrelevant",
        "name": "This bug is not relevant and will not be fixed.",
        "default_comment": "This bug is not relevant and will not be fixed."
    },
    {
        "key": "known_bug",
        "name": "This is a legit bug but already known.",
        "default_comment": "This is a legit bug but already known."
    },
    {
        "key": "not_reproducible",
        "name": "With the information provided it was not possible to reproduce this bug.",
        "default_comment": "With the information provided it was not possible to reproduce this bug."
    }
]

def parse_rejection_reason(comments):
    """
    Simulate the parsing logic:
    Iterate through comments and check if any body matches a default_comment.
    """
    if not comments:
        return None

    for comment in comments:
        body = comment.get("body", "")
        # Check for partial match or exact match?
        # The user said "matches bug comments against a known list".
        # Let's try simple substring matching first, as comments might have extra whitespace or newlines.
        for reason in REJECTION_REASONS:
            if reason["default_comment"] in body:
                return reason
    return None

db_path = os.path.expanduser("~/.testio-mcp/cache.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all rejected bugs
cursor.execute("SELECT id, raw_data FROM bugs WHERE status = 'rejected'")
rows = cursor.fetchall()

print(f"Found {len(rows)} rejected bugs.")

matched_count = 0
unmatched_count = 0

for bug_id, raw_data in rows:
    data = json.loads(raw_data)
    comments = data.get("comments", [])

    reason = parse_rejection_reason(comments)

    if reason:
        matched_count += 1
        print(f"[MATCH] Bug {bug_id}: {reason['key']}")
    else:
        unmatched_count += 1
        print(f"[NO MATCH] Bug {bug_id}")
        # Print comments for unmatched bugs to see why
        for c in comments:
            print(f"  - {c.get('author', {}).get('name')}: {c.get('body')[:100]}...")

print("-" * 30)
print(f"Total Rejected: {len(rows)}")
print(f"Matched: {matched_count}")
print(f"Unmatched: {unmatched_count}")

conn.close()
