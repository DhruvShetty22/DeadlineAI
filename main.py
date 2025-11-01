import getpass
from datetime import date, timedelta
from typing import List
import dotenv
dotenv.load_dotenv()  

from imap_tools import MailBox, A

from agent import extractor_agent, Deadline  
from database_manager import create_table, save_deadlines, DB_FILE 


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
            
            # mailbox.fetch returns a generator. We reverse it to get newest first.
            # We'll limit processing to the newest 50 to be safe.
            for i, msg in enumerate(mailbox.fetch(criteria, reverse=True)):
                if i >= 50:
                    print("Processing limit (50) reached. Stopping email fetch.")
                    break
                    
                if msg.text: 
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
    
    # --- 2. Get Credentials ---
    user_login = input("Enter your userId(e.g., 'sdhruv23'): ")
    pwd = getpass.getpass("Enter your password: ")
    
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
            # Run the agent from agent.py
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
    save_deadlines(all_extracted_deadlines) # From database_manager.py
    
    print("\n--- ✅ Agent run complete! ---")

if __name__ == "__main__":
    run_agent()