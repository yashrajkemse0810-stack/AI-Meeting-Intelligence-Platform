
from db import db
from bson import ObjectId
from datetime import datetime, timezone


def create_meeting(data):
    now = datetime.now(timezone.utc)

    meeting = {
        "title": data.get("title", "Untitled Meeting"),
        "description": data.get("description", ""),
        "status": data.get("status", "processing"),
        "summary_status": "pending",
        "created_at": now,
        "updated_at": now,
    }

    optional_fields = [
        "file_name",
        "file_url",
        "file_type",
        "file_size",
        "owner_id",
        "duration_seconds",
    ]

    for field in optional_fields:
        if field in data:
            meeting[field] = data[field]

    result = db.meetings.insert_one(meeting)
    meeting["_id"] = str(result.inserted_id)
    return meeting



def get_all_meetings():
    meetings = list(db.meetings.find().sort("created_at", -1))

    for meeting in meetings:
        meeting["_id"] = str(meeting["_id"])

    return meetings


def get_meeting_by_id(meeting_id):
    if not ObjectId.is_valid(meeting_id):
        return None

    meeting = db.meetings.find_one({"_id": ObjectId(meeting_id)})

    if meeting:
        meeting["_id"] = str(meeting["_id"])

    return meeting


def update_meeting(meeting_id, data):
    if not ObjectId.is_valid(meeting_id):
        return None

    allowed_fields = {"title", "description", "status"}
    updates = {
        key: value
        for key, value in data.items()
        if key in allowed_fields
    }

    if not updates:
        return get_meeting_by_id(meeting_id)

    updates["updated_at"] = datetime.now(timezone.utc)

    db.meetings.update_one(
        {"_id": ObjectId(meeting_id)},
        {"$set": updates}
    )

    return get_meeting_by_id(meeting_id)


def delete_meeting(meeting_id):
    if not ObjectId.is_valid(meeting_id):
        return False

    result = db.meetings.delete_one(
        {"_id": ObjectId(meeting_id)}
    )

    return result.deleted_count == 1

def save_transcript(meeting_id, transcript):
    if not ObjectId.is_valid(meeting_id):
        return None

    result = db.meetings.update_one(
        {"_id": ObjectId(meeting_id)},
        {
            "$set": {
                "transcript": transcript,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    if result.matched_count == 0:
        return None

    return get_meeting_by_id(meeting_id)


def get_transcript(meeting_id):
    meeting = get_meeting_by_id(meeting_id)

    if meeting is None:
        return None

    return {
        "meeting_id": meeting_id,
        "title": meeting.get("title", ""),
        "transcript": meeting.get("transcript", "")
    }


def save_meeting_summary(meeting_id, summary):
    if not ObjectId.is_valid(meeting_id):
        return None

    result = db.meetings.update_one(
        {"_id": ObjectId(meeting_id)},
        {
            "$set": {
                "summary": summary,
                "summary_status": "completed",
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    if result.matched_count == 0:
        return None

    return get_meeting_by_id(meeting_id)

    
def get_meeting_summary(meeting_id):
    meeting = get_meeting_by_id(meeting_id)

    if meeting is None:
        return None

    return {
        "meeting_id": meeting_id,
        "title": meeting.get("title", ""),
        "summary": meeting.get("summary", "")
    }
    
def mark_summary_failed(meeting_id):
    if not ObjectId.is_valid(meeting_id):
        return None

    result = db.meetings.update_one(
        {"_id": ObjectId(meeting_id)},
        {
            "$set": {
                "summary_status": "failed",
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    if result.matched_count == 0:
        return None

    return get_meeting_by_id(meeting_id)


