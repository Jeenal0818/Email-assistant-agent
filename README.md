# Email Assistant Agent

An autonomous AI email agent that transforms unstructured emails into executable actions using LLM reasoning, IMAP/SMTP protocols, and Google Calendar APIs.

The system ingests emails, identifies user intent, extracts temporal information, schedules meetings, sends emails, manages inbox operations, and automates end-to-end email workflows.

---

## System Architecture

```text
                     Incoming Emails
                           │
                           ▼
                  IMAP Email Ingestion
                           │
                           ▼
                Email Cleaning & Parsing
                           │
                           ▼
                 LLM Reasoning Pipeline
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
 Intent Detection  Entity Extraction  Time Parsing
          │            │            │
          └────────────┴────────────┘
                       │
                       ▼
              Decision & Action Engine
          ┌────────────┼────────────┐
          ▼            ▼            ▼
 Google Calendar   Email Sender   Inbox Actions
```

---

## Features

- Autonomous email ingestion via IMAP
- LLM-powered intent and entity extraction
- Natural language date & time understanding
- Automatic Google Calendar event creation
- SMTP-based email composition and delivery
- Email search and deletion utilities
- Modular architecture for extending agent capabilities

---

## Tech Stack

- Python
- OpenAI API
- IMAP / SMTP
- Google Calendar API
- Google OAuth 2.0
- DateParser
- python-dotenv

---

## Project Structure

```text
Email-assistant-agent/

├── main.py
├── calendar_agent.py
├── email_tools.py
├── delete_mail.py
├── credentials.json
├── token.json
├── requirements.txt
└── README.md
```

---

## Workflow

### 1. Email Ingestion

- Connects securely to Gmail via IMAP
- Retrieves incoming emails
- Cleans and preprocesses email content

### 2. LLM Reasoning

The agent extracts:

- User intent
- Meeting participants
- Date & time
- Subject
- Actionable context

### 3. Action Execution

Based on extracted intent, the agent can:

- Create Google Calendar events
- Send emails
- Search inbox
- Delete emails

### 4. Calendar Automation

Meeting requests are automatically converted into structured Google Calendar events with validated timestamps.

---

## Installation

```bash
git clone https://github.com/Jeenal0818/Email-assistant-agent.git

cd Email-assistant-agent

pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file:

```env
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

IMAP_HOST=imap.gmail.com

OPENAI_API_KEY=your_openai_api_key
```

---

## Google Calendar Setup

1. Enable the Google Calendar API.
2. Create OAuth Desktop credentials.
3. Download `credentials.json`.
4. Place it in the project root.
5. Run the application.

```bash
python main.py
```

The first execution generates a `token.json` file for authentication.

---

## Example

**Input Email**

> Let's meet next Tuesday at 4 PM to discuss the quarterly roadmap.

**Agent Actions**

- Detects meeting intent
- Extracts date and time
- Creates a Google Calendar event
- Confirms successful scheduling

---

## Engineering Highlights

- Architected an autonomous email workflow that combines LLM reasoning with IMAP/SMTP and Google Calendar APIs to execute user actions from natural-language emails.
- Built a modular agent pipeline separating email ingestion, reasoning, and action execution, enabling scalable extension of new agent capabilities.
- Implemented structured temporal extraction and intent classification to convert unstructured emails into executable calendar and email operations.

---

## Future Improvements

- Multi-agent architecture for specialized email tasks
- Retrieval-Augmented Generation (RAG) for long email threads
- Memory layer for personalized scheduling preferences
- Function-calling support for dynamic tool selection
- Slack, Outlook, and Microsoft Teams integrations
- Calendar conflict detection and intelligent meeting rescheduling

---
