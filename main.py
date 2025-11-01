import os
from datetime import date, timedelta
from typing import List
from dotenv import load_dotenv  # <-- NEW IMPORT

# --- Import from the correct package ---
from imap_tools import MailBox, A

# --- Import from our other scripts ---
from agent import extractor_agent, Deadline  # The "Brain"
from database_manager import create_table, save_deadlines, DB_FILE # The "Memory"

# --- Load all variables from .env file ---
load_dotenv()

# --- Your IITK Email Server Settings ---
IMAP_SERVER = "qasid.iitk.ac.in"
IMAP_PORT = 993

def fetch_recent_emails(username, password, days=7) -> List[dict]:
    """
    Connects to the IMAP server and fetches unseen emails from the last 7 days.
    """
    fetched_emails = []
    print(f"Connecting to {IMAP_SERVER}...")
    
    try:
        with MailBox(IMAP_SERVER, port=IMAP_PORT).login(username, password) as mailbox:
            print("Login successful. Fetching emails...")
            
            criteria = A(date_gte=date.today() - timedelta(days=days), seen=False)
            
            for i, msg in enumerate(mailbox.fetch(criteria, reverse=True)):
                if i >= 50:
                    print("Processing limit (50) reached. Stopping email fetch.")
                    break
                    
                if msg.text: # msg.text is the plain-text body
                    fetched_emails.append({
                        "subject": msg.subject,
                        "body": msg.text
                    })

            print(f"Fetched {len(fetched_emails)} new unread emails from the last {days} days.")
            return fetched_emails

    except Exception as e:
        print(f"Error connecting or fetching email: {e}")
        return [] # Return an empty list on failure

def run_agent():
    """
    The main end-to-end function for the agent's backend.
    """
    print("--- 🚀 Starting Email Deadline Agent ---")
    
    # --- 1. Initialize Database ---
    print("Initializing database...")
    create_table() # From database_manager.py
    
    # --- 2. Get Credentials (from .env) ---
    # We now read from the environment variables
    user_login = os.environ.get("EMAIL_USER")
    pwd = os.environ.get("EMAIL_PASS")
    
    if not user_login or not pwd:
        print("Error: EMAIL_USER or EMAIL_PASS not set in .env file.")
        return
    
    print("Credentials loaded successfully.")
    
    # --- 3. Fetch Emails (Our "Tool") ---
    emails_to_process = fetch_recent_emails(user_login, pwd)
    
    if not emails_to_process:
        print("No new emails to process. Exiting.")
        return

    # --- 4. Process with AI Agent (The "Brain") ---
    print(f"\n--- 🧠 Processing {len(emails_to_process)} emails with AI ---")
    all_extracted_deadlines = []
    
    for i, email in enumerate(emails_to_process):
        print(f"Processing email {i+1}/{len(emails_to_process)}: {email['subject'][:50]}...")
        try:
            result = extractor_agent.invoke({
                "subject": email['subject'],
                "body": email['body']
            })
            
            if result.deadlines:
                print(f"  > Found {len(result.deadlines)} deadline(s).")
                all_extracted_deadlines.extend(result.deadlines)
            else:
                print("  > No deadlines found.")
                
        except Exception as e:
            print(f"  > Error processing email with AI: {e}")
    
    print("\n--- 💾 Saving results to database ---")
    save_deadlines(all_extracted_deadlines) 
    
    print("\n--- ✅ Agent run complete! ---")


if __name__ == "__main__":
    run_agent()