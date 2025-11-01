import os
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

# Import for Google Gemini
from langchain_google_genai import ChatGoogleGenerativeAI

# --- 1. Define Your Desired Output Structure (using Pydantic) ---
class Deadline(BaseModel):
    task_name: str = Field(..., description="The name of the assignment, quiz, or project")
    due_date: date = Field(..., description="The date the task is due, in YYYY-MM-DD format")
    course_name: Optional[str] = Field(None, description="The course code or name (e.g., 'CS410', 'MTH101')")

class DeadlinesFound(BaseModel):
    deadlines: List[Deadline]


# --- 2. Initialize the "Brain" (the LLM) ---
try:
    # We use the full, stable model name we found from list_models()
    llm = ChatGoogleGenerativeAI(model="models/gemini-pro-latest", temperature=0)
    print("Successfully initialized Google Gemini (models/gemini-pro-latest).")
except Exception as e:
    print(f"Error initializing Gemini: {e}")
    print("Please make sure you have set your GOOGLE_API_KEY environment variable.")
    exit()

# --- 3. Create the Agent Chain ---
# We tell the LLM that it is a "tool" that can extract deadline data.
structured_llm = llm.with_structured_output(DeadlinesFound)

# This is the prompt that "reasons" about the email text.
prompt = ChatPromptTemplate.from_messages([
    ("system", f"""
     You are an expert AI assistant tasked with extracting deadline information from university emails.
     Your goal is to find any assignments, quizzes, projects, or exams.
     - Today's date is: {date.today()}. Use this as a reference for relative dates.
     - 'Next Friday' means the upcoming Friday, not the one after.
     - 'EOD' means 'end of day', but you should just extract the date.
     - Be careful to distinguish between *announcement* dates and *due* dates.
     - If no deadlines are found, return an empty list of deadlines.
     - The 'due_date' MUST be in YYYY-MM-DD format.
     - 'task_name' should be specific (e.g., "Homework 3", "Mid-term Exam").
     - 'course_name' can be extracted from the subject or email body.
    """),
    ("human", "Here is the email content:\n\nSubject: {subject}\n\nBody: {body}")
])

# Chain the prompt and the structured LLM together
extractor_agent = prompt | structured_llm


# --- 4. Test the Agent ---
if __name__ == "__main__":
    
    # --- This is our MOCK email data ---
    test_emails = [
        {
            "subject": "[CS410-TA] Reminder: Assignment 3 is due!",
            "body": f"""
            Hi all,
            This is a reminder that Assignment 3 (Graphs) is due this Friday, Nov 7. 
            (Today's date is {date.today()})
            Please submit your code to the portal before 11:59 PM.
            
            Also, Quiz 2 will be held next week on Nov 13.
            
            See you in class,
            TA
            """
        },
        {
            "subject": "Fwd: Weekly Newsletter",
            "body": "Hi, check out this newsletter. It has some cool articles. The robotics club meeting is on Friday."
        },
        {
            "subject": "[PHY101] Lecture 10 Slides and P-Set 4",
            "body": "Professor here. P-Set 4 has been released and is due on 2025-11-10."
        }
    ]

    print(f"--- Processing {len(test_emails)} emails (using today's date: {date.today()}) ---")

    all_extracted_deadlines = []

    for i, email in enumerate(test_emails):
        print(f"\n--- Email 1 ---")
        print(f"Subject: {email['subject']}")
        
        try:
            result = extractor_agent.invoke({
                "subject": email['subject'],
                "body": email['body']
            })
            
            if result.deadlines:
                print(f"Found {len(result.deadlines)} deadline(s):")
                for deadline in result.deadlines:
                    print(f"  - {deadline.task_name} ({deadline.course_name}) due on {deadline.due_date}")
                    all_extracted_deadlines.append(deadline)
            else:
                print("No deadlines found in this email.")

        except Exception as e:
            print(f"Error processing email: {e}")
            
    print("\n\n--- All Deadlines Extracted ---")
    print(all_extracted_deadlines)