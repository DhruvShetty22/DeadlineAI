import sqlite3
from datetime import date
from typing import List
from agent import Deadline # We import our data structure from agent.py

# Define the database file name
DB_FILE = "deadlines.db"

def create_table():
    """Connects to the DB and creates the 'deadlines' table if it doesn't exist."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS deadlines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT NOT NULL,
            course_name TEXT,
            due_date TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            UNIQUE(task_name, course_name, due_date)
        );
        """)
        conn.commit()
        print("Database and table verified successfully.")


def save_deadlines(deadline_list: List[Deadline]):
    """Saves a list of Deadline objects to the SQLite database."""
    if not deadline_list:
        print("No new deadlines to save.")
        return

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        saved_count = 0
        ignored_count = 0
        
        for deadline in deadline_list:
            try:
                due_date_str = deadline.due_date.isoformat()
                cursor.execute("""
                INSERT OR IGNORE INTO deadlines (task_name, course_name, due_date)
                VALUES (?, ?, ?)
                """, (deadline.task_name, deadline.course_name, due_date_str))
                
                if cursor.rowcount > 0:
                    saved_count += 1
                else:
                    ignored_count += 1
            except sqlite3.Error as e:
                print(f"Error saving deadline {deadline.task_name}: {e}")
        
        conn.commit()
        print(f"Database update complete: {saved_count} new deadlines saved, {ignored_count} duplicates ignored.")

# --- NEW FUNCTION ---
def cleanup_past_deadlines():
    """
    Deletes any 'pending' deadlines where the due date has already passed.
    This keeps the 'pending' list clean. 'Done' tasks are kept as a record.
    """
    today_str = date.today().isoformat()
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            # Only delete PENDING tasks that are in the past
            cursor.execute("DELETE FROM deadlines WHERE status = 'pending' AND due_date < ?", (today_str,))
            count = cursor.rowcount
            conn.commit()
            if count > 0:
                print(f"Cleanup complete: Removed {count} past-due 'pending' tasks.")
            else:
                print("Cleanup: No past-due tasks to remove.")
    except sqlite3.Error as e:
        print(f"Error during cleanup: {e}")

# --- This part is just for testing, you can ignore it ---
if __name__ == "__main__":
    print("Initializing database...")
    create_table()
    print("\nCleaning up any old tasks...")
    cleanup_past_deadlines()