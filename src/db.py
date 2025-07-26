import os
import sqlite3
from pathlib import Path
import argparse

# Default path for the SQLite database
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "database" / "events.db"
# Allow overriding the database location via environment variable
DB_FILE = os.environ.get("EVENTS_DB_FILE", str(DEFAULT_DB_PATH))

def connect_db():
    """Connect to the SQLite database and return a connection."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

def init_db():
    """Create the events table and insert seed data if the database is empty."""
    conn = connect_db()
    cur = conn.cursor()
    # Create events table with necessary fields
    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY,
            category TEXT,
            topic TEXT,
            name TEXT,
            country TEXT,
            date_start TEXT,
            date_end TEXT,
            description TEXT,
            tag TEXT UNIQUE,
            affected_by TEXT,
            affects TEXT
        )
    """)
    conn.commit()
    # Check if table is empty; if so, insert seed events
    cur.execute("SELECT COUNT(*) FROM events")
    count = cur.fetchone()[0]
    if count == 0:
        seed_events = [
            {
                "category": "Politics", "topic": "War", "name": "World War I", "country": "Global",
                "date_start": "1914-07-28", "date_end": "1918-11-11",
                "description": "A global war originating in Europe.",
                "tag": "Politics_War_World_War_I_1914",
                "affected_by": "",
                "affects": "Politics_War_World_War_II_1939"
            },
            {
                "category": "Politics", "topic": "War", "name": "World War II", "country": "Global",
                "date_start": "1939-09-01", "date_end": "1945-09-02",
                "description": "Global war involving most world nations.",
                "tag": "Politics_War_World_War_II_1939",
                "affected_by": "Politics_War_World_War_I_1914",
                "affects": "Politics_Conflict_Cold_War_1947,Science_Space_Moon_Landing_1969"
            },
            {
                "category": "Politics", "topic": "Conflict", "name": "Cold War", "country": "Global",
                "date_start": "1947-03-12", "date_end": "1991-12-26",
                "description": "Geopolitical tension post-WWII between Eastern and Western blocs.",
                "tag": "Politics_Conflict_Cold_War_1947",
                "affected_by": "Politics_War_World_War_II_1939",
                "affects": "Politics_Conflict_Fall_of_Berlin_Wall_1989"
            },
            {
                "category": "Politics", "topic": "Conflict", "name": "Fall of Berlin Wall", "country": "Germany",
                "date_start": "1989-11-09", "date_end": None,
                "description": "Demolition of the Berlin Wall, ending East/West German separation.",
                "tag": "Politics_Conflict_Fall_of_Berlin_Wall_1989",
                "affected_by": "Politics_Conflict_Cold_War_1947",
                "affects": ""
            },
            {
                "category": "Science", "topic": "Space", "name": "Moon Landing", "country": "USA",
                "date_start": "1969-07-20", "date_end": None,
                "description": "Apollo 11 mission lands the first humans on the Moon.",
                "tag": "Science_Space_Moon_Landing_1969",
                "affected_by": "Politics_War_World_War_II_1939",
                "affects": ""
            },
            {
                "category": "Culture", "topic": "Music", "name": "Woodstock Festival", "country": "USA",
                "date_start": "1969-08-15", "date_end": "1969-08-18",
                "description": "Iconic music festival of 1969.",
                "tag": "Culture_Music_Woodstock_Festival_1969",
                "affected_by": "",
                "affects": ""
            }
        ]
        for ev in seed_events:
            cur.execute("""
                INSERT INTO events 
                (category, topic, name, country, date_start, date_end, description, tag, affected_by, affects)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ev["category"], ev["topic"], ev["name"], ev["country"],
                ev["date_start"], ev["date_end"], ev["description"], ev["tag"],
                ev["affected_by"], ev["affects"]
            ))
        conn.commit()
    conn.close()

def get_events():
    """Retrieve all events from the database as a list of dictionaries."""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM events")
    rows = cur.fetchall()
    events = [dict(row) for row in rows]
    conn.close()
    return events

def get_event_by_tag(tag):
    """Retrieve a single event by its tag (unique identifier)."""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM events WHERE tag = ?", (tag,))
    row = cur.fetchone()
    event = dict(row) if row else None
    conn.close()
    return event

def insert_event(category, topic, name, country, date_start, date_end, description, tag, affected_by, affects):
    """Insert a new event record into the database."""
    conn = connect_db()
    cur = conn.cursor()
    try:
        cur.execute(
            """
        INSERT INTO events
        (category, topic, name, country, date_start, date_end, description, tag, affected_by, affects)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (category, topic, name, country, date_start, date_end, description, tag, affected_by, affects),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise ValueError("An event with this tag already exists.") from exc
    finally:
        conn.close()
# --- add below insert_event() -----------------------------------------------
def update_event(event_id, **fields):
    """
    Update any subset of columns for a given event_id.
    Usage: update_event(5, name="New Name", description="…")
    """
    if not fields:
        return
    cols = ", ".join(f"{k}=?" for k in fields.keys())
    values = list(fields.values()) + [event_id]
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(f"UPDATE events SET {cols} WHERE id = ?", values)
    conn.commit()
    conn.close()

def delete_event(event_id):
    """Remove an event entirely (and clean dangling links)."""
    conn = connect_db()
    cur = conn.cursor()
    # First pull its tag so we can strip it from other rows’ affects/affected_by
    cur.execute("SELECT tag FROM events WHERE id = ?", (event_id,))
    row = cur.fetchone()
    tag = row["tag"] if row else None
    # Delete the event itself
    cur.execute("DELETE FROM events WHERE id = ?", (event_id,))
    if tag:
        # Remove the tag from all other rows’ link fields
        for field in ("affects", "affected_by"):
            # Fetch rows referencing the tag
            cur.execute(f"SELECT id, {field} FROM events WHERE INSTR({field}, ?) > 0", (tag,))
            for row in cur.fetchall():
                parts = [t for t in (row[field] or "").split(',') if t and t != tag]
                new_val = ",".join(parts)
                cur.execute(f"UPDATE events SET {field} = ? WHERE id = ?", (new_val, row["id"]))
    conn.commit()
    conn.close()
    
def add_relation_tag(event_tag, field, related_tag):
    """
    Append a related event tag to an existing event's `affects` or `affected_by` field.
    This maintains a two-way link between events.
    """
    if field not in ("affects", "affected_by"):
        return
    conn = connect_db()
    cur = conn.cursor()
    # Get current list of related tags for the given event
    cur.execute(f"SELECT {field} FROM events WHERE tag = ?", (event_tag,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return
    current_val = row[0] if row[0] is not None else ""
    existing_tags = [t for t in current_val.split(",") if t]  # split by comma to list
    if related_tag in existing_tags:
        conn.close()
        return  # already linked
    # Append the new tag to the comma-separated list
    new_val = related_tag if current_val == "" or current_val is None else current_val + "," + related_tag
    cur.execute(f"UPDATE events SET {field} = ? WHERE tag = ?", (new_val, event_tag))
    conn.commit()
    conn.close()

def main():
    """Optional CLI to initialize the database."""
    parser = argparse.ArgumentParser(description="Manage the events database")
    parser.add_argument(
        "--db",
        default=os.environ.get("EVENTS_DB_FILE", str(DEFAULT_DB_PATH)),
        help="Path to the SQLite database file",
    )
    args = parser.parse_args()
    global DB_FILE
    DB_FILE = args.db
    init_db()
    print(f"Initialized database at {DB_FILE}")


if __name__ == "__main__":
    main()