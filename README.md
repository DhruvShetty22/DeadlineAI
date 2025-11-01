
This project is a submission for the Software Engineer intern application.

Name: Dhruv Shetty

University: IIT Kanpur

Department: Biological Sciences and Bioengineering

1. Project Concept

This project is an AI agent designed to solve a common and stressful problem for university students: managing deadlines. Students receive a high volume of emails with critical information about assignments, quizzes, internships, and workshops. Manually finding, tracking, and centralizing these deadlines is tedious and prone to error.

This agent automates the entire process. It connects to the user's university email (IITK), reads new emails, uses an AI to reason about the content, extracts all relevant deadlines, and executes by saving them to a local, persistent database. The user can then view and manage all their deadlines in one simple, interactive desktop application.


<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/1f4b26d6-846e-4bec-8397-1cd98c631b66" />
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/c42bd08c-8698-45f0-8a64-5d15d19194d9" />




2. Features

This prototype fulfills all core and optional requirements from the assignment.

Backend Agent (main.py)

IMAP Email Connection: Connects securely to the university's IMAP server (qasid.iitk.ac.in) to fetch new emails.

AI-Powered Reasoning: Uses Google's Gemini LLM (via LangChain) to read and understand the full text of each email.

Broad Deadline Extraction: The agent's prompt is designed to find all types of deadlines, not just academic ones (e.g., "Assignment 3", "Internship Application", "Workshop Registration").

Structured Output: Uses Pydantic to force the LLM's unstructured output into a clean, reliable Deadline data object.

Persistent Memory: Saves all extracted deadlines to a local SQLite database (deadlines.db).

Automatic Cleanup: Automatically deletes 'pending' tasks from the database if their due date has already passed, keeping the list relevant.

Streamlit UI (app.py)

Dashboard: A high-level dashboard showing "Total Pending Deadlines," "Deadlines Due This Week," and the "Next Upcoming" task.

Manual Scan: A "Scan Emails Now" button that manually triggers the entire backend agent, providing a "refresh" functionality.

Interactive Monitor: A full, editable table of all deadlines. Users can click the "status" column to change a task from pending to done.

Chat-based Filtering: A chat UI that allows users to filter the table with natural language commands (e.g., latest, quiz, assignment).

Chat-based Deletion: Allows the user to type delete [task name] to initiate a safe deletion, which then presents a confirmation UI to prevent mistakes.

3. Technology Stack & Rationale

Component

Technology

Rationale (Reasoning)

Backend

Python 3.10+

The standard for AI development with the best libraries (LangChain, Streamlit).

Frontend UI

Streamlit

A Python-only framework for building data-centric web apps, perfect for rapid prototyping.

AI Agent

LangChain

The core agentic framework, used to chain the prompt, LLM, and structured output parser.

LLM

Google Gemini (models/gemini-pro-latest)

A powerful, free-to-use LLM capable of the reasoning and extraction required.

Data Schema

Pydantic

Guarantees reliable, structured data from the LLM, preventing errors.

Database

SQLite (SQL)

A serverless, single-file database. Perfect for a local desktop app (no setup required).

Email Tool

imap-tools

A high-level Python library to simplify the IMAP connection to the mail server.

Credentials

python-dotenv

The standard for securely managing API keys and passwords in a .env file, which is kept local.

4. How to Run This Project

Prerequisites

Python 3.10+

A Google Gemini API Key (from Google AI Studio)

A compatible email account (project is configured for qasid.iitk.ac.in)

Installation & Setup

Clone the repository:

git clone [your-repo-url]
cd [your-repo-name]


Create and activate a Python virtual environment:

# For Windows
py -m venv venv
.\venv\Scripts\activate


(If you get a PowerShell error, run Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process first)

Install all required packages:

pip install -r requirements.txt


Create your credentials file:

Create a new file in the main folder named .env

Copy and paste the text below, filling in your own credentials:

# .env file
GOOGLE_API_KEY="Your-Google-API-Key-Here"
EMAIL_USER="your-email@iitk.ac.in"
EMAIL_PASS="Your-Email-Password-Here"


Running the Application

Launch the Streamlit App:

Make sure you are in your activated (venv) terminal.

Run the following command:

streamlit run app.py


Your browser will automatically open, and the app is ready to use.

5. How to Use the App

When the app first loads, the database will be empty.

Click the "Scan Emails Now" button. The app will securely log in to your email, find all unread emails, and populate the Dashboard and Deadline Monitor.

Use the Chat Interface to filter your tasks (e.g., assignment).

To mark a task as complete, click on the pending status in the table and change it to done.

To delete a task, type delete [task name] into the chat and confirm your choice.

6. Project Deliverables

As required by the assignment, all deliverables are in this repository:

Source Code: All .py and .bat files.

System Design Document: Design.md

Interaction Logs: https://gemini.google.com/share/d672a0035083
