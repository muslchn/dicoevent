from rest_framework import serializers
from .models import TicketType, Ticket
from events.serializers import EventSerializer


class TicketTypeSerializer(serializers.ModelSerializer):
    """Serializer for TicketType model"""
    event_detail = EventSerializer(source='event', read_only=True)
    available_quantity = serializers.SerializerMethodField()
    is_sold_out = serializers.SerializerMethodField()
    
    class Meta:
        model = TicketType
        fields = [
            'id', 'event', 'event_detail', 'name', 'description', 'price',
            'quantity', 'sold', 'is_active', 'available_quantity', 
            'is_sold_out', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'event_detail', 'sold', 'available_quantity', 
            'is_sold_out', 'created_at', 'updated_at'
        ]
    
    def get_available_quantity(self, obj):
        return obj.available_quantity()
    
    def get_is_sold_out(self, obj):
        return obj.is_sold_out()
    
    def validate(self, attrs):
        price = attrs.get('price')
        quantity = attrs.get('quantity')
        
        if price and price < 0:
            raise serializers.ValidationError("Price cannot be negative")
        
        if quantity and quantity <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
            
        return attrs


class TicketTypeCreateSerializer(TicketTypeSerializer):
    """Serializer for creating ticket types"""
    
    class Meta(TicketTypeSerializer.Meta):
        read_only_fields = ['id', 'sold', 'available_quantity', 'is_sold_out', 'created_at', 'updated_at']


class TicketTypeUpdateSerializer(TicketTypeSerializer):
    """Serializer for updating ticket types"""
    
    class Meta(TicketTypeSerializer.Meta):
        read_only_fields = ['id', 'event', 'sold', 'available_quantity', 'is_sold_out', 'created_at', 'updated_at']


class TicketSerializer(serializers.ModelSerializer):
    """Serializer for individual Ticket model"""
    ticket_type_detail = TicketTypeSerializer(source='ticket_type', read_only=True)
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'ticket_type', 'ticket_type_detail', 'code', 
            'issued_at', 'is_used', 'used_at'
        ]
        read_only_fields = ['id', 'ticket_type_detail', 'code', 'issued_at', 'used_at']