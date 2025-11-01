import os
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

# Import for Google Gemini
from langchain_google_genai import ChatGoogleGenerativeAI

# --- 1. Define Your Desired Output Structure (using Pydantic) ---
# This structure is general, so it's still perfect.
class Deadline(BaseModel):
    task_name: str = Field(..., description="The name of the assignment, task, application, or event")
    due_date: date = Field(..., description="The date the task is due, in YYYY-MM-DD format")
    course_name: Optional[str] = Field(None, description="The course or organization (e.g., 'CS410', 'Robotics Club')")

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
structured_llm = llm.with_structured_output(DeadlinesFound)

# --- THIS IS THE UPDATED SECTION ---
# This prompt is now much broader and looks for all kinds of deadlines.
prompt = ChatPromptTemplate.from_messages([
    ("system", f"""
     You are an expert AI assistant. Your task is to extract **any and all deadlines** from emails.
     Your goal is to find any task, event, or application with a specific due date.
     This includes, but is not limited to:
     - Academic tasks (assignments, quizzes, projects, exams)
     - Applications (internships, jobs, programs, scholarships)
     - Registrations (workshops, events, courses, conferences)
     - Submissions (proposals, forms, reports)
     
     - Today's date is: {date.today()}. Use this as a reference for relative dates.
     - If no deadlines are found, return an empty list of deadlines.
     - The 'due_date' MUST be in YYYY-MM-DD format.
     - 'task_name' should be specific (e.g., "Homework 3", "Internship Application", "Workshop Registration").
     - 'course_name' can be the course (CS410) or organization (Robotics Club, ACM).
    """),
    ("human", "Here is the email content:\n\nSubject: {subject}\n\nBody: {body}")
])
# -----------------------------------

# Chain the prompt and the structured LLM together
extractor_agent = prompt | structured_llm


# --- 4. Test the Agent ---
if __name__ == "__main__":
    
    # --- Updated MOCK email data ---
    test_emails = [
        {
            "subject": "[PHY101] Lecture 10 Slides and P-Set 4",
            "body": "Professor here. P-Set 4 has been released and is due on 2025-11-10."
        },
        {
            "subject": "Fwd: Summer Internship Opportunity @ Google",
            "body": """
            Hi students,
            The application portal for the Google Summer Internship is now open!
            Please submit your applications by November 20th, 2025.
            """
        },
        {
            "subject": "Robotics Club: AI Workshop",
            "body": "Don't forget to register for our upcoming AI workshop. Registrations close this Friday."
        }
    ]

    print(f"--- Processing {len(test_emails)} emails (using today's date: {date.today()}) ---")

    all_extracted_deadlines = []

    for i, email in enumerate(test_emails):
        print(f"\n--- Email {i+1} ---")
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