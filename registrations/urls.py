from django.urls import path
from . import views

urlpatterns = [
    path('', views.RegistrationListCreateView.as_view(), name='registration-list-create'),
    path('<uuid:pk>/', views.RegistrationDetailView.as_view(), name='registration-detail'),
    path('my/', views.my_registrations, name='my-registrations'),
    path('events/<uuid:event_pk>/registrations/', views.event_registrations, name='event-registrations'),
    path('<uuid:pk>/status/', views.update_registration_status, name='update-registration-status'),
    path('<uuid:pk>/cancel/', views.cancel_registration, name='cancel-registration'),
]