from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Registration
from .serializers import (
    RegistrationSerializer, 
    RegistrationCreateSerializer, 
    RegistrationUpdateSerializer,
    RegistrationStatusUpdateSerializer
)
from users.permissions import CanManageRegistrations
from events.models import Event


class RegistrationListCreateView(generics.ListCreateAPIView):
    """List all registrations or create a new registration"""
    queryset = Registration.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_status', 'event', 'user']
    search_fields = ['attendee_name', 'attendee_email', 'event__title']
    ordering_fields = ['registered_at', 'updated_at']
    ordering = ['-registered_at']
    
    def list(self, request, *args, **kwargs):
        """Override to return array directly instead of paginated response"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def get_queryset(self):
        queryset = Registration.objects.all()
        
        # Regular users can only see their own registrations
        if not (self.request.user.is_admin() or self.request.user.is_superuser_role()):
            queryset = queryset.filter(user=self.request.user)
            
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RegistrationCreateSerializer
        return RegistrationSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        # Set the user to the current user
        serializer.save(user=self.request.user)


class RegistrationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a registration"""
    queryset = Registration.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return RegistrationUpdateSerializer
        return RegistrationSerializer
    
    def get_queryset(self):
        queryset = Registration.objects.all()
        
        # Regular users can only access their own registrations
        if not (self.request.user.is_admin() or self.request.user.is_superuser_role()):
            queryset = queryset.filter(user=self.request.user)
            
        return queryset
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        elif self.request.method in ['PUT', 'PATCH']:
            # Users can update their own registrations, admins can update all
            if not (self.request.user.is_admin() or self.request.user.is_superuser_role()):
                return [IsAuthenticated()]
            return [CanManageRegistrations()]
        else:  # DELETE
            return [CanManageRegistrations()]


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_registrations(request):
    """Get current user's registrations"""
    registrations = Registration.objects.filter(user=request.user).order_by('-registered_at')
    serializer = RegistrationSerializer(registrations, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def event_registrations(request, event_pk):
    """Get all registrations for a specific event"""
    event = get_object_or_404(Event, pk=event_pk)
    
    # Check if user has permission to view event registrations
    if not (request.user.is_admin() or request.user.is_superuser_role() or event.organizer == request.user):
        return Response(
            {'error': 'You do not have permission to view registrations for this event'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    registrations = Registration.objects.filter(event=event).order_by('-registered_at')
    serializer = RegistrationSerializer(registrations, many=True)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([CanManageRegistrations])
def update_registration_status(request, pk):
    """Update registration status"""
    registration = get_object_or_404(Registration, pk=pk)
    
    serializer = RegistrationStatusUpdateSerializer(
        registration, 
        data=request.data, 
        partial=True
    )
    
    if serializer.is_valid():
        old_status = registration.status
        new_status = serializer.validated_data.get('status')
        
        # Business logic for status transitions
        if old_status == 'pending' and new_status == 'confirmed':
            # Check if event still has capacity
            if registration.event.is_full():
                return Response(
                    {'error': 'Cannot confirm registration - event is full'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif old_status == 'confirmed' and new_status == 'attended':
            # Mark as attended
            pass
        elif new_status == 'cancelled':
            # Allow cancellation
            pass
        else:
            return Response(
                {'error': f'Invalid status transition from {old_status} to {new_status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save()
        return Response({
            'message': 'Registration status updated successfully',
            'registration': RegistrationSerializer(registration).data
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_registration(request, pk):
    """Cancel a registration"""
    registration = get_object_or_404(Registration, pk=pk)
    
    # Check if user owns this registration or has admin rights
    if not (registration.user == request.user or 
            request.user.is_admin() or 
            request.user.is_superuser_role()):
        return Response(
            {'error': 'You do not have permission to cancel this registration'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if registration.cancel_registration():
        return Response({
            'message': 'Registration cancelled successfully',
            'registration': RegistrationSerializer(registration).data
        })
    else:
        return Response(
            {'error': 'Cannot cancel registration in current status'},
            status=status.HTTP_400_BAD_REQUEST
        )