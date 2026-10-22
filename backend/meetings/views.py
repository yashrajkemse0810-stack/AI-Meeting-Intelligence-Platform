import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage

from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes

from .ai_service import generate_meeting_summary

from .db_operations import (
    create_meeting,
    get_all_meetings,
    get_meeting_by_id,
    update_meeting,
    delete_meeting,
    save_transcript,
    get_transcript,
    save_meeting_summary,
    get_meeting_summary,
    mark_summary_failed,
)

from db import db




@api_view(["GET", "POST"])
def meetings_list(request):
    if request.method == "GET":
        return Response(get_all_meetings())

    title = request.data.get("title")
    if not title:
        return Response(
            {"error": "Meeting title is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    meeting = create_meeting(request.data)
    return Response(meeting, status=status.HTTP_201_CREATED)



@api_view(["GET", "PUT", "PATCH", "DELETE"])
def meeting_detail(request, meeting_id):
    meeting = get_meeting_by_id(meeting_id)

    if request.method == "GET":
        if meeting is None:
            return Response(
                {"error": "Meeting not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(meeting)

    if request.method in ["PUT", "PATCH"]:
        if meeting is None:
            return Response(
                {"error": "Meeting not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        updated = update_meeting(meeting_id, request.data)

        if updated is None:
            return Response(
                {"error": "Meeting not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(updated)

    deleted = delete_meeting(meeting_id)

    if not deleted:
        return Response(
            {"error": "Meeting not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(status=status.HTTP_204_NO_CONTENT)




@api_view(["GET"])
def dashboard_summary(request):
    total_meetings = db.meetings.count_documents({})
    processing_meetings = db.meetings.count_documents(
        {"status": "processing"}
    )
    completed_meetings = db.meetings.count_documents(
        {"status": "completed"}
    )
    failed_meetings = db.meetings.count_documents(
        {"status": "failed"}
    )

    recent_meetings = list(
        db.meetings.find(
            {},
            {
                "title": 1,
                "status": 1,
                "created_at": 1,
            }
        ).sort("created_at", -1).limit(5)
    )

    for meeting in recent_meetings:
        meeting["_id"] = str(meeting["_id"])
        if "created_at" in meeting:
            meeting["created_at"] = meeting["created_at"].isoformat()

    return Response({
        "total_meetings": total_meetings,
        "processing_meetings": processing_meetings,
        "completed_meetings": completed_meetings,
        "failed_meetings": failed_meetings,
        "recent_meetings": recent_meetings,
    })

    
@api_view(["GET", "POST"])
def meeting_transcript(request, meeting_id):
    if request.method == "POST":
        transcript = request.data.get("transcript")

        if not isinstance(transcript, str) or not transcript.strip():
            return Response(
                {"error": "Transcript text is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        meeting = save_transcript(meeting_id, transcript)

        if meeting is None:
            return Response(
                {"error": "Meeting not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            get_transcript(meeting_id),
            status=status.HTTP_200_OK,
        )

    result = get_transcript(meeting_id)

    if result is None:
        return Response(
            {"error": "Meeting not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(result)

@api_view(["POST"])
def summarize_meeting(request, meeting_id):
    meeting = get_meeting_by_id(meeting_id)

    if meeting is None:
        return Response(
            {"error": "Meeting not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    transcript = meeting.get("transcript", "")

    if not transcript or not transcript.strip():
        return Response(
            {"error": "No transcript found for this meeting"},
            status=status.HTTP_400_BAD_REQUEST
        )

    
    try:
        summary = generate_meeting_summary(transcript)
        updated_meeting = save_meeting_summary(meeting_id, summary)

        if updated_meeting is None:
            return Response(
                {"error": "Could not save meeting summary"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {
                "meeting_id": meeting_id,
                "title": updated_meeting.get("title", ""),
                "summary": summary,
                "message": "AI meeting summary generated successfully"
            },
            status=status.HTTP_200_OK
        )

    
    except Exception as e:
        print("AI SUMMARY ERROR:", repr(e))
        mark_summary_failed(meeting_id)
        return Response(
            {
                "error": "AI summary generation failed. Please try again later.",
                "summary_status": "failed"
            },
            status=status.HTTP_502_BAD_GATEWAY
        )

        
@api_view(["GET"])
def meeting_summary(request, meeting_id):
    result = get_meeting_summary(meeting_id)

    if result is None:
        return Response(
            {"error": "Meeting not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    if not result["summary"]:
        return Response(
            {"error": "Summary has not been generated yet"},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response(result, status=status.HTTP_200_OK)
    
@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def upload_meeting(request):
    uploaded_file = request.FILES.get("file")
    title = request.data.get("title", "").strip()

    if not uploaded_file:
        return Response(
            {"error": "Please upload a file using the 'file' field."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not title:
        return Response(
            {"error": "Title is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    allowed_extensions = {".mp3", ".wav", ".m4a", ".mp4", ".webm"}
    extension = os.path.splitext(uploaded_file.name)[1].lower()

    if extension not in allowed_extensions:
        return Response(
            {"error": "Unsupported file type."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if uploaded_file.size > 100 * 1024 * 1024:
        return Response(
            {"error": "File size must not exceed 100 MB."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    upload_dir = os.path.join(settings.MEDIA_ROOT, "meeting_uploads")
    os.makedirs(upload_dir, exist_ok=True)

    storage = FileSystemStorage(location=upload_dir)
    saved_name = storage.save(uploaded_file.name, uploaded_file)

    meeting_data = {
        "title": title,
        "description": "",
        "file_name": uploaded_file.name,
        "file_url": f"{settings.MEDIA_URL}meeting_uploads/{saved_name}",
        "file_type": extension.lstrip("."),
        "file_size": uploaded_file.size,
        "status": "processing",
    }

    meeting = create_meeting(meeting_data)

    return Response(
        {
            "message": "Meeting uploaded successfully.",
            "meeting": meeting,
        },
        status=status.HTTP_201_CREATED,
    )






