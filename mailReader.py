import imaplib
import email
from email.header import decode_header
import getpass
import datetime 

IMAP_SERVER = "qasid.iitk.ac.in"
IMAP_PORT = 993
# ----------------------------------------

def get_email_body(msg):
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain" and part.get("Content-Disposition") is None:
                try:
                    charset = part.get_content_charset()
                    if charset is None:
                        charset = 'utf-8'
                    return part.get_payload(decode=True).decode(charset, 'ignore')
                except Exception as e:
                    print(f"Error decoding part: {e}")
                    return None
    else:
        try:
            charset = msg.get_content_charset()
            if charset is None:
                charset = 'utf-8'
            return msg.get_payload(decode=True).decode(charset, 'ignore')
        except Exception as e:
            print(f"Error decoding single part: {e}")
            return None

def fetch_unread_emails(username, password, days_to_search=7, max_emails=15):
    
    print(f"Connecting to {IMAP_SERVER}...")
    mail = None
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(username, password)
        print("Login successful.")
        
        mail.select("inbox")
        
        date_since = (datetime.date.today() - datetime.timedelta(days=days_to_search))
        date_str = date_since.strftime("%d-%b-%Y")
        
        search_query = f'(UNSEEN SINCE "{date_str}")'
        print(f"Searching for unread emails since {date_str}...")

        status, messages = mail.search(None, search_query)
        
        if status != "OK":
            print("No messages found!")
            return []

        email_ids = messages[0].split()
        
        # --- NEW: Reverse and Limit ---
        email_ids.reverse() # Reverse to get newest first
        total_found = len(email_ids)
        print(f"Found {total_found} new unread emails.")
        
        # Get the list of IDs we will actually fetch
        email_ids_to_fetch = email_ids[:max_emails]
        if total_found > max_emails:
            print(f"Processing the newest {max_emails} emails...")
        # ------------------------------
        
        fetched_emails = []

        for e_id in email_ids_to_fetch: # Loop over the limited list
            status, msg_data = mail.fetch(e_id, "(RFC822)")
            
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        try:
                            subject = subject.decode(encoding if encoding else 'utf-8', 'ignore')
                        except:
                            subject = subject.decode('utf-8', 'ignore')

                    body = get_email_body(msg)
                    
                    if body:
                        fetched_emails.append({
                            "subject": subject,
                            "body": body.strip()
                        })
                        
        return fetched_emails

    except imaplib.IMAP4.error as e:
        print(f"IMAP Error: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []
    finally:
        if mail:
            mail.close()
            mail.logout()
            print("Connection closed.")

# --- Main execution ---
if __name__ == "__main__":
    user = input("Enter your IITK username (e.g., 'your_username'): ")
    pwd = getpass.getpass("Enter your password: ")
    
    full_username = f"{user}" 
    
    # We call the function, which now has the max_emails=15 logic inside it
    unread_emails = fetch_unread_emails(full_username, pwd, days_to_search=7, max_emails=15)
    
    if unread_emails:
        print(f"\n--- Showing Top {len(unread_emails)} Unread Emails (Last 7 Days) ---")
        for i, mail in enumerate(unread_emails):
            print(f"\n--- Email {i+1} ---")
            print(f"Subject: {mail['subject']}") # <-- The subject is printed here
            print("--- Body (Snippet) ---")
            print(mail['body'][:500] + "...")
    else:
        print("\nNo new unread emails found in the last 7 days.")