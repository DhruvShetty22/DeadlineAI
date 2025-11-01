import os
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

from langchain_google_genai import ChatGoogleGenerativeAI

# Load .env if present
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise SystemExit("Please set GOOGLE_API_KEY in environment or in a .env file.")

# Pydantic models for structured output
class Deadline(BaseModel):
    task_name: str = Field(..., description="The name of the assignment, task, application, or event")
    due_date: date = Field(..., description="The date the task is due, in YYYY-MM-DD format")
    course_name: Optional[str] = Field(None, description="The course or organization (e.g., 'CS410', 'Robotics Club')")

class DeadlinesFound(BaseModel):
    deadlines: List[Deadline]

# Initialize the LLM (Google Gemini via langchain_google_genai)
try:
    llm = ChatGoogleGenerativeAI(model="models/gemini-pro-latest", temperature=0)
except Exception as e:
    raise SystemExit(f"Error initializing Google Gemini: {e}")

# Structured LLM wrapper
structured_llm = llm.with_structured_output(DeadlinesFound)

# Prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", f"""
     You are an expert AI assistant. Your task is to extract any and all deadlines from emails.
     Find any task, event, or application with a specific due date.
     Include academic tasks, applications, registrations, submissions, etc.
     Use today's date {date.today()} as reference for relative dates.
     If no deadlines are found, return an empty list of deadlines.
     The 'due_date' MUST be in YYYY-MM-DD format.
     'task_name' should be specific (e.g., "Homework 3", "Internship Application").
     'course_name' can be the course (CS410) or organization (Robotics Club).
    """),
    ("human", "Here is the email content:\n\nSubject: {subject}\n\nBody: {body}")
])

# Combined agent
extractor_agent = prompt | structured_llm

def extract_deadlines(subject: str, body: str) -> List[dict]:
    """
    Invoke the extractor agent on one email and return a list of deadlines as dicts.
    Returns an empty list when no deadlines found.
    Raises exceptions for unexpected invocation errors.
    """
    result = extractor_agent.invoke({"subject": subject, "body": body})
    # result is expected to be a DeadlinesFound pydantic model or similar
    deadlines = getattr(result, "deadlines", None)
    if not deadlines:
        return []
    # Convert Pydantic models to plain dicts (dates become ISO strings)
    out = []
    for d in deadlines:
        if isinstance(d, Deadline):
            out.append({
                "task_name": d.task_name,
                "due_date": d.due_date.isoformat(),
                "course_name": d.course_name
            })
        else:
            # If the library returned plain dict-like objects
            try:
                out.append({
                    "task_name": d.get("task_name"),
                    "due_date": (d.get("due_date").isoformat() if hasattr(d.get("due_date"), "isoformat") else d.get("due_date")),
                    "course_name": d.get("course_name")
                })
            except Exception:
                out.append(d)
    return out

if __name__ == "__main__":
    print("Module loaded. Use extract_deadlines(subject, body) to parse emails.")

import os
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

from langchain_google_genai import ChatGoogleGenerativeAI

# Load .env if present
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise SystemExit("Please set GOOGLE_API_KEY in environment or in a .env file.")

# Pydantic models for structured output
class Deadline(BaseModel):
    task_name: str = Field(..., description="The name of the assignment, task, application, or event")
    due_date: date = Field(..., description="The date the task is due, in YYYY-MM-DD format")
    course_name: Optional[str] = Field(None, description="The course or organization (e.g., 'CS410', 'Robotics Club')")

class DeadlinesFound(BaseModel):
    deadlines: List[Deadline]

# Initialize the LLM (Google Gemini via langchain_google_genai)
try:
    llm = ChatGoogleGenerativeAI(model="models/gemini-pro-latest", temperature=0)
except Exception as e:
    raise SystemExit(f"Error initializing Google Gemini: {e}")

# Structured LLM wrapper
structured_llm = llm.with_structured_output(DeadlinesFound)

# Prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", f"""
     You are an expert AI assistant. Your task is to extract any and all deadlines from emails.
     Find any task, event, or application with a specific due date.
     Include academic tasks, applications, registrations, submissions, etc.
     Use today's date {date.today()} as reference for relative dates.
     If no deadlines are found, return an empty list of deadlines.
     The 'due_date' MUST be in YYYY-MM-DD format.
     'task_name' should be specific (e.g., "Homework 3", "Internship Application").
     'course_name' can be the course (CS410) or organization (Robotics Club).
    """),
    ("human", "Here is the email content:\n\nSubject: {subject}\n\nBody: {body}")
])

# Combined agent
extractor_agent = prompt | structured_llm

def extract_deadlines(subject: str, body: str) -> List[dict]:
    """
    Invoke the extractor agent on one email and return a list of deadlines as dicts.
    Returns an empty list when no deadlines found.
    Raises exceptions for unexpected invocation errors.
    """
    result = extractor_agent.invoke({"subject": subject, "body": body})
    # result is expected to be a DeadlinesFound pydantic model or similar
    deadlines = getattr(result, "deadlines", None)
    if not deadlines:
        return []
    # Convert Pydantic models to plain dicts (dates become ISO strings)
    out = []
    for d in deadlines:
        if isinstance(d, Deadline):
            out.append({
                "task_name": d.task_name,
                "due_date": d.due_date.isoformat(),
                "course_name": d.course_name
            })
        else:
            # If the library returned plain dict-like objects
            try:
                out.append({
                    "task_name": d.get("task_name"),
                    "due_date": (d.get("due_date").isoformat() if hasattr(d.get("due_date"), "isoformat") else d.get("due_date")),
                    "course_name": d.get("course_name")
                })
            except Exception:
                out.append(d)
    return out

if __name__ == "__main__":
    print("Module loaded. Use extract_deadlines(subject, body) to parse emails.")