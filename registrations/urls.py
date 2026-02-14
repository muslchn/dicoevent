from django.urls import path
from . import views

urlpatterns = [
    path('registrations/', views.RegistrationListCreateView.as_view(), name='registration-list-create'),
    path('registrations/<uuid:pk>/', views.RegistrationDetailView.as_view(), name='registration-detail'),
    path('registrations/my/', views.my_registrations, name='my-registrations'),
    path('events/<uuid:event_pk>/registrations/', views.event_registrations, name='event-registrations'),
    path('registrations/<uuid:pk>/status/', views.update_registration_status, name='update-registration-status'),
    path('registrations/<uuid:pk>/cancel/', views.cancel_registration, name='cancel-registration'),
]