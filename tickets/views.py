from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import TicketType, Ticket
from .serializers import (
    TicketTypeSerializer, 
    TicketTypeCreateSerializer, 
    TicketTypeUpdateSerializer,
    TicketSerializer
)
from users.permissions import CanManageTickets
from events.models import Event
import random
import string


class TicketTypeListCreateView(generics.ListCreateAPIView):
    """List all ticket types or create a new ticket type"""
    queryset = TicketType.objects.all()
    serializer_class = TicketTypeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['event', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']
    ordering = ['-created_at']
    
    def list(self, request, *args, **kwargs):
        """Override to return array directly instead of paginated response"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TicketTypeCreateSerializer
        return TicketTypeSerializer


class TicketTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a ticket type"""
    queryset = TicketType.objects.all()
    serializer_class = TicketTypeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return TicketTypeUpdateSerializer
        return TicketTypeSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        else:
            return [CanManageTickets()]


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def event_ticket_types(request, event_pk):
    """Get all ticket types for a specific event"""
    ticket_types = TicketType.objects.filter(event_id=event_pk, is_active=True)
    serializer = TicketTypeSerializer(ticket_types, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([CanManageTickets])
def generate_tickets(request, ticket_type_pk):
    """Generate individual tickets for a ticket type"""
    ticket_type = get_object_or_404(TicketType, pk=ticket_type_pk)
    
    # Verify user has permission to manage this ticket type's event
    event = ticket_type.event
    if not (request.user.is_admin() or request.user.is_superuser_role() or event.organizer == request.user):
        return Response(
            {'error': 'You do not have permission to generate tickets for this event'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    count = request.data.get('count', 1)
    
    if not isinstance(count, int) or count <= 0:
        return Response(
            {'error': 'Count must be a positive integer'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if there are enough available slots
    available_slots = ticket_type.available_quantity()
    if count > available_slots:
        return Response(
            {'error': f'Cannot generate {count} tickets. Only {available_slots} slots available.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Generate tickets
    generated_tickets = []
    for _ in range(count):
        # Generate unique ticket code
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not Ticket.objects.filter(code=code).exists():
                break
        
        ticket = Ticket.objects.create(
            ticket_type=ticket_type,
            code=code
        )
        generated_tickets.append(ticket)
        ticket_type.sold += 1
        ticket_type.save()
    
    serializer = TicketSerializer(generated_tickets, many=True)
    return Response({
        'message': f'Successfully generated {len(generated_tickets)} tickets',
        'tickets': serializer.data
    }, status=status.HTTP_201_CREATED)


class TicketListView(generics.ListAPIView):
    """List all individual tickets"""
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['ticket_type', 'is_used']
    ordering_fields = ['issued_at', 'used_at']
    ordering = ['-issued_at']
    
    def list(self, request, *args, **kwargs):
        """Override to return array directly instead of paginated response"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def validate_ticket(request, ticket_code):
    """Validate a ticket by code"""
    try:
        ticket = Ticket.objects.get(code=ticket_code)
    except Ticket.DoesNotExist:
        return Response(
            {'valid': False, 'message': 'Ticket not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if ticket.is_used:
        return Response({
            'valid': False,
            'message': 'Ticket already used',
            'ticket': TicketSerializer(ticket).data
        })
    
    return Response({
        'valid': True,
        'message': 'Ticket is valid',
        'ticket': TicketSerializer(ticket).data
    })


@api_view(['POST'])
@permission_classes([CanManageTickets])
def use_ticket(request, ticket_code):
    """Mark a ticket as used"""
    try:
        ticket = Ticket.objects.get(code=ticket_code)
    except Ticket.DoesNotExist:
        return Response(
            {'error': 'Ticket not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if ticket.is_used:
        return Response(
            {'error': 'Ticket already used'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    ticket.mark_as_used()
    
    return Response({
        'message': 'Ticket marked as used successfully',
        'ticket': TicketSerializer(ticket).data
    })