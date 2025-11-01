import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from main import run_agent

load_dotenv()

DB_FILE = "deadlines.db"

# --- Database Functions ---
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def get_deadlines(filter_query=""):
    conn = get_db_connection()
    query = "SELECT id, task_name, course_name, due_date, status FROM deadlines"
    
    if "latest" in filter_query:
        query += " WHERE status = 'pending' ORDER BY due_date ASC"
    elif "quiz" in filter_query:
        query += " WHERE status = 'pending' AND (task_name LIKE '%quiz%' OR course_name LIKE '%quiz%') ORDER BY due_date ASC"
    elif "assignment" in filter_query:
        query += " WHERE status = 'pending' AND (task_name LIKE '%assignment%' OR task_name LIKE '%p-set%') ORDER BY due_date ASC"
    elif "done" in filter_query:
        query += " WHERE status = 'done' ORDER BY due_date DESC"
    else:
        query += " WHERE status = 'pending' ORDER BY due_date ASC"
        
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

def delete_deadline(deadline_id):
    """Permanently deletes a task from the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM deadlines WHERE id = ?", (deadline_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error deleting from database: {e}")
        return False

# --- NEW FUNCTION ---
def get_tasks_to_delete(search_term: str):
    """Gets a list of pending tasks that match a search term."""
    conn = get_db_connection()
    # Use LIKE to find partial matches
    tasks = conn.execute(
        "SELECT id, task_name, course_name, due_date FROM deadlines WHERE status = 'pending' AND task_name LIKE ?",
        (f"%{search_term}%",)
    ).fetchall()
    conn.close()
    return tasks

# --- Streamlit App UI ---
st.set_page_config(page_title="Deadline Agent", layout="wide")
st.title("🎓 Email Deadline Agent")

# --- Initialize Session State ---
# This holds the app's "memory"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "filter" not in st.session_state:
    st.session_state.filter = "latest"
if "delete_mode" not in st.session_state:
    st.session_state.delete_mode = False # Are we in "view" or "delete" mode?
if "tasks_to_delete" not in st.session_state:
    st.session_state.tasks_to_delete = [] # List of tasks matching delete command

# --- 1. Dashboard ---
st.header("Dashboard")
try:
    conn = get_db_connection()
    pending_count = conn.execute("SELECT COUNT(*) FROM deadlines WHERE status = 'pending'").fetchone()[0]
    today = datetime.now().date()
    one_week_from_now = today + timedelta(days=7)
    due_this_week_count = conn.execute(
        "SELECT COUNT(*) FROM deadlines WHERE status = 'pending' AND due_date BETWEEN ? AND ?",
        (today.isoformat(), one_week_from_now.isoformat())
    ).fetchone()[0]
    next_deadline = conn.execute(
        "SELECT task_name, due_date FROM deadlines WHERE status = 'pending' ORDER BY due_date ASC LIMIT 1"
    ).fetchone()
    conn.close()

    col1, col2, col3 = st.columns(3)
    col1.metric(label="Total Pending Deadlines", value=pending_count)
    col2.metric(label="Deadlines Due This Week", value=due_this_week_count)
    if next_deadline:
        col3.metric(label="Next Up", value=next_deadline["task_name"], delta=f"Due: {next_deadline['due_date']}")
    else:
        col3.metric(label="Next Up", value="N/A")

except Exception as e:
    st.info("Database empty. Click 'Scan Emails Now' to get started.")

# --- 2. Scan Button ---
st.header("Scan for New Deadlines")
st.info("This will also automatically remove any 'pending' tasks that are past their due date.")
if st.button("Scan Emails Now"):
    with st.spinner("Connecting to email, cleaning up old tasks, and running AI agent..."):
        try:
            run_agent() 
            st.success("Scan complete! New deadlines (if any) are added.")
            st.session_state.delete_mode = False # Exit delete mode after a scan
            st.rerun()
        except Exception as e:
            st.error(f"An error occurred during the scan: {e}")

# --- 3. Chat Interface ---
st.header("💬 Chat Interface")
st.write("Ask the agent to filter or delete. Try these commands:")
st.info("`latest` | `quiz` | `assignment` | `delete [task name]`")

prompt = st.chat_input("What do you want to see?")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    prompt_lower = prompt.lower()

    # --- NEW: Intent Parsing Logic ---
    if prompt_lower.startswith("delete "):
        st.session_state.delete_mode = True # Enter delete mode
        search_term = prompt[len("delete "):].strip() # Get the task name
        
        if not search_term:
            st.session_state.messages.append({"role": "assistant", "content": "Please specify what you want to delete. (e.g., `delete Quiz 1`)"})
            st.session_state.delete_mode = False
        else:
            st.session_state.tasks_to_delete = get_tasks_to_delete(search_term)
            
            if not st.session_state.tasks_to_delete:
                st.session_state.messages.append({"role": "assistant", "content": f"Sorry, I couldn't find any pending tasks matching '{search_term}'."})
                st.session_state.delete_mode = False # Exit delete mode
            else:
                st.session_state.messages.append({"role": "assistant", "content": f"I found {len(st.session_state.tasks_to_delete)} task(s) matching '{search_term}'. Please confirm below."})
        
        st.rerun() # Rerun to show the new UI state

    else:
        # This is the old "filter" logic
        st.session_state.delete_mode = False # Ensure we are in view mode
        st.session_state.filter = prompt_lower
        st.session_state.messages.append({"role": "assistant", "content": f"OK, filtering for: '{st.session_state.filter}'"})
        st.rerun() # Rerun to apply the filter

# --- 4. Main Display (Conditional UI) ---
# This section now shows EITHER the delete UI OR the table UI,
# depending on the app's "mode".

if st.session_state.delete_mode:
    # --- DELETE CONFIRMATION UI ---
    st.header("Confirm Deletion")
    st.warning("Please select which task you'd like to permanently delete.")
    
    # Check if tasks are still available (in case of rerun)
    if not st.session_state.tasks_to_delete:
        st.info("No tasks to delete. Type a new command.")
    
    for task in st.session_state.tasks_to_delete:
        col1, col2 = st.columns([0.8, 0.2])
        task_display = f"**{task['task_name']}** ({task['course_name'] or 'N/A'}) - Due: {task['due_date']}"
        col1.markdown(task_display)
        
        # Use the task ID in the key to make it unique
        if col2.button(f"Delete This Task", type="primary", key=f"del_{task['id']}"):
            if delete_deadline(task['id']):
                st.success(f"Deleted '{task['task_name']}'!")
                # Exit delete mode and rerun to refresh the list
                st.session_state.delete_mode = False
                st.rerun()
            else:
                st.error("Failed to delete task.")
    
    if st.button("Cancel"):
        st.session_state.delete_mode = False
        st.rerun()

else:
    # --- REGULAR TABLE MONITOR UI ---
    st.header("🗓️ Deadline Monitor")
    st.write(f"Showing results for: **{st.session_state.filter}**")

    try:
        data = get_deadlines(st.session_state.filter)
        if data.empty:
            st.warning("No deadlines found. Click 'Scan Emails Now' to check for new ones.")
        else:
            edited_df = st.data_editor(
                data,
                column_config={
                    "id": None,
                    "task_name": st.column_config.TextColumn("Task", width="large"),
                    "course_name": st.column_config.TextColumn("Course"),
                    "due_date": st.column_config.DateColumn("Due Date", format="YYYY-MM-DD"),
                    "status": st.column_config.SelectboxColumn("Status", options=["pending", "done"], required=True)
                },
                use_container_width=True, hide_index=True, num_rows="dynamic", key="deadline_editor"
            )
            
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
        st.info("Database not found. Click 'Scan Emails Now' to initialize it.")