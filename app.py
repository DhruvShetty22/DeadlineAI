import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

DB_FILE = "deadlines.db"

def get_db_connection():
    
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row # This lets us access columns by name
    return conn

def get_deadlines(filter_query=""):
    """Fetches deadlines from the database, optionally filtering."""
    conn = get_db_connection()
    
    # Base query
    query = "SELECT id, task_name, course_name, due_date, status FROM deadlines"
    
    # Apply filters from chat commands
    if "latest" in filter_query:
        query += " WHERE status = 'pending' ORDER BY due_date ASC"
    elif "quiz" in filter_query:
        query += " WHERE status = 'pending' AND (task_name LIKE '%quiz%' OR course_name LIKE '%quiz%') ORDER BY due_date ASC"
    elif "assignment" in filter_query:
        query += " WHERE status = 'pending' AND (task_name LIKE '%assignment%' OR task_name LIKE '%p-set%') ORDER BY due_date ASC"
    elif "done" in filter_query:
        query += " WHERE status = 'done' ORDER BY due_date DESC"
    else: # Default: show pending
        query += " WHERE status = 'pending' ORDER BY due_date ASC"
        
    # --- THIS IS THE FIX ---
    # We add 'parse_dates' to tell pandas to convert the 'due_date' column
    # from a string (TEXT) into a datetime object.
    df = pd.read_sql_query(query, conn, parse_dates=["due_date"])
    
    conn.close()
    return df

def update_status(deadline_id, new_status):
    """Updates the status of a specific deadline."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE deadlines SET status = ? WHERE id = ?", (new_status, deadline_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error updating database: {e}")
        return False

# --- Streamlit App UI ---
st.set_page_config(page_title="Deadline Agent", layout="wide")

# --- 1. Main Title ---
st.title("🎓 Email Deadline Agent")
st.write("This app displays deadlines found by the AI agent. Run `main.py` to scan for new emails.")

# --- 2. Chat UI ---
st.header("💬 Chat Interface")
st.write("Ask the agent to filter the deadlines. Try these commands:")
st.info("`latest` (default) | `quiz` | `assignment` | `done`")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    
# Get user input
prompt = st.chat_input("What do you want to see?")

# Store the filter query in session state
if "filter" not in st.session_state:
    st.session_state.filter = "latest"

if prompt:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Set the filter
    st.session_state.filter = prompt.lower()
    # Add assistant response
    st.session_state.messages.append({"role": "assistant", "content": f"OK, filtering for: '{st.session_state.filter}'"})


# --- 3. Deadline Table (The "Monitor" UI) ---
st.header("🗓️ Deadline Monitor")
st.write(f"Showing results for: **{st.session_state.filter}**")

# Fetch and display the data
try:
    data = get_deadlines(st.session_state.filter)
    
    if data.empty:
        st.warning("No deadlines found matching your filter.")
    else:
        # Use st.data_editor to make the table interactive
        edited_df = st.data_editor(
            data,
            column_config={
                "id": None, # Hide the ID column
                "task_name": st.column_config.TextColumn("Task", width="large"),
                "course_name": st.column_config.TextColumn("Course"),
                "due_date": st.column_config.DateColumn("Due Date", format="YYYY-MM-DD"), # This config is now valid
                "status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["pending", "done"],
                    required=True,
                )
            },
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            key="deadline_editor"
        )
        
        # --- Bonus Feature: Handle Edits ---
        if "deadline_editor" in st.session_state:
            diff = st.session_state.deadline_editor.get("edited_rows")
            if diff:
                for row_index, changes in diff.items():
                    deadline_id = data.iloc[row_index]["id"]
                    if "status" in changes:
                        new_status = changes["status"]
                        update_status(deadline_id, new_status)
                        st.success(f"Updated Task ID {deadline_id} to '{new_status}'!")
                        st.rerun()

except Exception as e:
    st.error(f"Failed to load data from database: {e}")
    st.info("Have you run `main.py` at least once to create and populate the database?")