from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Event
from .serializers import EventSerializer, EventCreateSerializer, EventUpdateSerializer
from users.permissions import CanManageEvents, IsOrganizerOrAdmin


class EventListCreateView(generics.ListCreateAPIView):
    """List all events or create a new event"""
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'city', 'country', 'organizer']
    search_fields = ['title', 'description', 'venue', 'city']
    ordering_fields = ['start_date', 'end_date', 'created_at', 'price']
    ordering = ['-created_at']
    
    def list(self, request, *args, **kwargs):
        """Override to return array directly instead of paginated response"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EventCreateSerializer
        return EventSerializer
    
    def perform_create(self, serializer):
        # Set the organizer to the current user
        serializer.save(organizer=self.request.user)
        
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event = self.perform_create(serializer)
        
        # Return response with ID field
        return Response(
            {
                "id": str(event.id),
                "title": event.title,
                "description": event.description,
                "organizer": str(event.organizer.id),
                "venue": event.venue,
                "address": event.address,
                "city": event.city,
                "country": event.country,
                "start_date": event.start_date.isoformat(),
                "end_date": event.end_date.isoformat(),
                "capacity": event.capacity,
                "price": str(event.price),
                "status": event.status,
                "created_at": event.created_at.isoformat(),
                "updated_at": event.updated_at.isoformat(),
            },
            status=status.HTTP_201_CREATED,
        )


class EventDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete an event"""
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return EventUpdateSerializer
        return EventSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            # Anyone authenticated can view events
            return [IsAuthenticated()]
        else:
            # Only organizers of the event, admins, or superusers can modify
            return [CanManageEvents()]
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Return response matching test expectations
        return Response(
            {
                "id": str(instance.id),
                "title": instance.title,
                "description": instance.description,
                "organizer": str(instance.organizer.id),
                "venue": instance.venue,
                "address": instance.address,
                "city": instance.city,
                "country": instance.country,
                "start_date": instance.start_date.isoformat(),
                "end_date": instance.end_date.isoformat(),
                "capacity": instance.capacity,
                "price": str(instance.price),
                "status": instance.status,
                "created_at": instance.created_at.isoformat(),
                "updated_at": instance.updated_at.isoformat(),
            }
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def upcoming_events(request):
    """Get upcoming events"""
    from django.utils import timezone
    upcoming = Event.objects.filter(
        start_date__gte=timezone.now(),
        status='published'
    ).order_by('start_date')
    
    serializer = EventSerializer(upcoming, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_events(request):
    """Get events organized by the current user"""
    my_events = Event.objects.filter(organizer=request.user).order_by('-created_at')
    serializer = EventSerializer(my_events, many=True)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsOrganizerOrAdmin])
def publish_event(request, pk):
    """Publish an event"""
    event = get_object_or_404(Event, pk=pk)
    
    # Check if user has permission to modify this event
    if not (request.user.is_admin() or request.user.is_superuser_role() or event.organizer == request.user):
        return Response(
            {'error': 'You do not have permission to modify this event'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if event.status == 'draft':
        event.status = 'published'
        event.save()
        return Response({
            'message': 'Event published successfully',
            'event': EventSerializer(event).data
        })
    else:
        return Response({
            'error': 'Event is not in draft status'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
@permission_classes([IsOrganizerOrAdmin])
def cancel_event(request, pk):
    """Cancel an event"""
    event = get_object_or_404(Event, pk=pk)
    
    # Check if user has permission to modify this event
    if not (request.user.is_admin() or request.user.is_superuser_role() or event.organizer == request.user):
        return Response(
            {'error': 'You do not have permission to modify this event'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if event.status in ['published', 'draft']:
        event.status = 'cancelled'
        event.save()
        return Response({
            'message': 'Event cancelled successfully',
            'event': EventSerializer(event).data
        })
    else:
        return Response({
            'error': 'Event cannot be cancelled in its current status'
        }, status=status.HTTP_400_BAD_REQUEST)