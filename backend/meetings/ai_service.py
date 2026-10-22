

import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def generate_meeting_summary(transcript):
    if not transcript or not transcript.strip():
        raise ValueError("Meeting transcript is empty.")

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": """
You are a professional AI meeting intelligence assistant.

Generate a report using these exact sections:

# Meeting Summary
Summarize the main discussion clearly.

# Key Decisions
Record decisions explicitly agreed upon and confirmed next steps.
Distinguish suggestions from confirmed decisions.
If none exist, write "No explicit decisions recorded."

# Action Items
List every task and follow-up action mentioned.
Include the responsible person when identifiable.
Do not invent task assignments.
If none exist, write "No action items recorded."

# Deadlines
List each deadline and its related task.
Preserve the original timing, such as Friday, Monday, or next week.
Do not invent calendar dates.
If none exist, write "No deadlines specified."

Rules:
- Use only information from the transcript.
- Never invent names, decisions, tasks, or deadlines.
- Distinguish proposals from confirmed decisions.
- Use concise, professional language.
- Format the report using Markdown.
- Use standard English characters and hyphens.
"""
            },
            {
                "role": "user",
                "content": transcript
            }
        ],
        temperature=0.2
    )

    return response.choices[0].message.content
