
from django.urls import path
from . import views

urlpatterns = [
    path("", views.meetings_list, name="meetings-list"),
    path("dashboard/", views.dashboard_summary, name="dashboard-summary"),
    path("upload/", views.upload_meeting, name="upload-meeting"),
    path(
        "<str:meeting_id>/transcript/",
        views.meeting_transcript,
        name="meeting-transcript",
    ),
    path(
        "<str:meeting_id>/summarize/",
        views.summarize_meeting,
        name="summarize-meeting",
    ),
    path(
        "<str:meeting_id>/summary/",
        views.meeting_summary,
        name="meeting-summary",
    ),
    path("<str:meeting_id>/", views.meeting_detail, name="meeting-detail"),
]
