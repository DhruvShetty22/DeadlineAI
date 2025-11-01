import sqlite3
from datetime import date
from typing import List
from agent import Deadline # We import our data structure from agent.py

# Define the database file name
DB_FILE = "deadlines.db"

def create_table():
    """Connects to the DB and creates the 'deadlines' table if it doesn't exist."""
    
    # 'with' statement handles opening and closing the connection
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # We use "IF NOT EXISTS" so we can run this script safely many times.
        # We add a "status" field for our UI later (e.g., 'pending', 'done')
        # We add "UNIQUE (task_name, course_name)" to prevent duplicate entries
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
                # We convert the 'date' object to a string in 'YYYY-MM-DD' format
                due_date_str = deadline.due_date.isoformat()
                
                # We use "INSERT OR IGNORE" which uses the UNIQUE constraint.
                # If a deadline with the same task, course, and date
                # already exists, it will be ignored, not duplicated.
                cursor.execute("""
                INSERT OR IGNORE INTO deadlines (task_name, course_name, due_date)
                VALUES (?, ?, ?)
                """, (deadline.task_name, deadline.course_name, due_date_str))
                
                # cursor.rowcount tells us if a row was actually inserted (1) or ignored (0)
                if cursor.rowcount > 0:
                    saved_count += 1
                else:
                    ignored_count += 1
                    
            except sqlite3.Error as e:
                print(f"Error saving deadline {deadline.task_name}: {e}")
        
        conn.commit()
        print(f"Database update complete: {saved_count} new deadlines saved, {ignored_count} duplicates ignored.")


# --- This part runs when you execute the script directly ---
if __name__ == "__main__":
    print("Initializing database...")
    # 1. Create the table
    create_table()
    
    # 2. Create some "dummy" deadlines to test saving
    dummy_deadlines = [
        Deadline(task_name="Test Assignment 1", due_date=date(2025, 11, 15), course_name="CS101"),
        Deadline(task_name="Test Quiz", due_date=date(2025, 11, 12), course_name="PHY202")
    ]
    
    print("\nSaving dummy deadlines...")
    # 3. Save the dummy deadlines
    save_deadlines(dummy_deadlines)
    
    print("\nSaving dummy deadlines again (to test duplicate prevention)...")
    # 4. Save them again to make sure duplicates are ignored
    save_deadlines(dummy_deadlines)