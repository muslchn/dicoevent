from rest_framework import permissions


class IsAdminOrSuperUser(permissions.BasePermission):
    """Allow access only to admin or superuser"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_admin() or request.user.is_superuser_role()
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """Allow access to owner or admin/superuser"""
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated and (
            request.user.is_admin() or request.user.is_superuser_role()
        ):
            return True
        return obj.user == request.user


class IsOrganizerOrAdmin(permissions.BasePermission):
    """Allow access to organizers, admins, and superusers"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_organizer() or 
            request.user.is_admin() or 
            request.user.is_superuser_role()
        )


class CanManageEvents(permissions.BasePermission):
    """Allow access to users who can manage events"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_permission_to_manage_events()


class CanManageTickets(permissions.BasePermission):
    """Allow access to users who can manage tickets"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_permission_to_manage_tickets()


class CanManageRegistrations(permissions.BasePermission):
    """Allow access to users who can manage registrations"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_permission_to_manage_registrations()


class CanManagePayments(permissions.BasePermission):
    """Allow access to users who can manage payments"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_permission_to_manage_payments()