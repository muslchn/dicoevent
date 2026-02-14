from rest_framework import serializers
from .models import Event
from users.serializers import UserSerializer


class EventSerializer(serializers.ModelSerializer):
    """Serializer for Event model"""
    organizer_detail = UserSerializer(source='organizer', read_only=True)
    available_spots = serializers.SerializerMethodField()
    is_full = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'organizer', 'organizer_detail',
            'venue', 'address', 'city', 'country', 'start_date', 'end_date',
            'capacity', 'price', 'status', 'image', 'available_spots', 
            'is_full', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'organizer_detail', 'available_spots', 'is_full', 'created_at', 'updated_at']
    
    def get_available_spots(self, obj):
        return obj.available_spots()
    
    def get_is_full(self, obj):
        return obj.is_full()
    
    def validate(self, attrs):
        # Validate that end_date is after start_date
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        if start_date and end_date and end_date <= start_date:
            raise serializers.ValidationError("End date must be after start date")
        
        # Validate capacity
        capacity = attrs.get('capacity')
        if capacity and capacity <= 0:
            raise serializers.ValidationError("Capacity must be greater than 0")
            
        return attrs


class EventCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating events - excludes organizer as it's set automatically"""
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'venue', 'address', 'city', 
            'country', 'start_date', 'end_date', 'capacity', 'price', 
            'status', 'image', 'available_spots', 'is_full', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'available_spots', 'is_full', 'created_at', 'updated_at']
    
    def get_available_spots(self, obj):
        return obj.available_spots()
    
    def get_is_full(self, obj):
        return obj.is_full()
    
    def validate(self, attrs):
        # Validate that end_date is after start_date
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        if start_date and end_date and end_date <= start_date:
            raise serializers.ValidationError("End date must be after start date")
        
        # Validate capacity
        capacity = attrs.get('capacity')
        if capacity and capacity <= 0:
            raise serializers.ValidationError("Capacity must be greater than 0")
            
        return attrs


class EventUpdateSerializer(EventSerializer):
    """Serializer for updating events"""
    
    class Meta(EventSerializer.Meta):
        read_only_fields = ['id', 'organizer', 'available_spots', 'is_full', 'created_at', 'updated_at']