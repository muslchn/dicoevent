from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from .models import User
from .serializers import (
    UserRegistrationSerializer, 
    UserLoginSerializer, 
    UserSerializer, 
    UserUpdateSerializer,
    UserRoleUpdateSerializer
)
from .permissions import IsAdminOrSuperUser


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """Register a new user"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """Login user and return JWT tokens"""
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListView(generics.ListAPIView):
    """List all users (admin/superuser only)"""
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrSuperUser]


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete user details"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            # Users can view their own profile or admins can view all
            requested_user_id = self.kwargs.get('pk')
            current_user_id = str(self.request.user.id)
            
            # Ensure both are strings for proper comparison
            if str(requested_user_id) == current_user_id:
                return [IsAuthenticated()]
            return [IsAdminOrSuperUser()]
        elif self.request.method in ['PUT', 'PATCH']:
            # Users can update their own profile
            requested_user_id = self.kwargs.get('pk')
            current_user_id = str(self.request.user.id)
            
            if str(requested_user_id) == current_user_id:
                return [IsAuthenticated()]
            return [IsAdminOrSuperUser()]
        else:  # DELETE
            return [IsAdminOrSuperUser()]


@api_view(['PATCH'])
@permission_classes([IsAdminOrSuperUser])
def update_user_role(request, pk):
    """Update user role (admin/superuser only)"""
    user = get_object_or_404(User, pk=pk)
    serializer = UserRoleUpdateSerializer(user, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return Response({
            'message': 'User role updated successfully',
            'user': UserSerializer(user).data
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)