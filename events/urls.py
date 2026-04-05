from django.urls import path
from . import views

urlpatterns = [
    path("", views.EventListCreateView.as_view(), name="event-list-create"),
    path("upload/", views.upload_event_poster, name="event-poster-upload"),
    path("<uuid:pk>/", views.EventDetailView.as_view(), name="event-detail"),
    path("<uuid:pk>/poster/", views.get_event_poster, name="event-poster-detail"),
    path("upcoming/", views.upcoming_events, name="upcoming-events"),
    path("my-events/", views.my_events, name="my-events"),
    path("<uuid:pk>/publish/", views.publish_event, name="publish-event"),
    path("<uuid:pk>/cancel/", views.cancel_event, name="cancel-event"),
]
