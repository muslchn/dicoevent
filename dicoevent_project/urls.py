"""dicoevent_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from users import views as user_views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/events/', include('events.urls')),
    path('api/tickets/', include('tickets.urls')),
    path('api/registrations/', include('registrations.urls')),
    path('api/payments/', include('payments.urls')),
    # Direct authentication endpoints for tests
    path('api/register/', user_views.register_user),
    path('api/login/', user_views.login_user),
    # JWT token endpoints - both paths for compatibility
    path('api/token/', TokenRefreshView.as_view(), name='token_obtain_pair'),  # For Postman tests
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Direct group management endpoints
    path('api/groups/', user_views.GroupListCreateView.as_view()),
    path('api/groups/<int:pk>/', user_views.GroupDetailView.as_view()),
    # User-group assignment endpoint
    path('api/assign-roles/', user_views.assign_user_to_group, name='assign-roles'),
]