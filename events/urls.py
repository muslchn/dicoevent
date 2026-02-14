from django.urls import path
from . import views

urlpatterns = [
    path('events/', views.EventListCreateView.as_view(), name='event-list-create'),
    path('events/<uuid:pk>/', views.EventDetailView.as_view(), name='event-detail'),
    path('events/upcoming/', views.upcoming_events, name='upcoming-events'),
    path('events/my-events/', views.my_events, name='my-events'),
    path('events/<uuid:pk>/publish/', views.publish_event, name='publish-event'),
    path('events/<uuid:pk>/cancel/', views.cancel_event, name='cancel-event'),
]