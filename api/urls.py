from django.urls import path, include

urlpatterns = [
    path('users/', include('users.urls')),
    path('events/', include('events.urls')),
    path('tickets/', include('tickets.urls')),
    path('registrations/', include('registrations.urls')),
    path('payments/', include('payments.urls')),
]