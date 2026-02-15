from rest_framework import serializers
from .models import Group

class GroupSerializer(serializers.ModelSerializer):
    """Serializer for Group model"""
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']