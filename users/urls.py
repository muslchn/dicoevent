from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # User management endpoints (these will be under /api/users/)
    path('', views.UserListCreateView.as_view(), name='user-list-create'),
    path('<uuid:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('me/', views.UserDetailView.as_view(), name='user-profile'),
    
    # Authentication endpoints
    path('register/', views.register_user, name='user-register'),
    path('login/', views.login_user, name='user-login'),
    path('token/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # Group/Organizer management endpoints
    path('groups/', views.GroupListCreateView.as_view(), name='group-list-create'),
    path('groups/<int:pk>/', views.GroupDetailView.as_view(), name='group-detail'),
    
    # User role management
    path('<uuid:pk>/role/', views.update_user_role, name='user-role-update'),
]