from rest_framework import permissions  # type: ignore[import]


class IsAdminOrSuperUser(permissions.BasePermission):
    """Allow access only to admin or superuser"""

    def has_permission(self, request, view):
        # Check if user is authenticated and has admin or superuser role
        is_authenticated = request.user.is_authenticated
        is_admin_role = hasattr(request.user, "is_admin") and request.user.is_admin()
        is_superuser_role = (
            hasattr(request.user, "is_superuser_role")
            and request.user.is_superuser_role()
        )
        is_builtin_superuser = getattr(request.user, "is_superuser", False)

        return is_authenticated and (
            is_admin_role or is_superuser_role or is_builtin_superuser
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
            request.user.is_organizer()
            or request.user.is_admin()
            or request.user.is_superuser_role()
        )


class CanManageEvents(permissions.BasePermission):
    """Allow access to users who can manage events or organizers owning them"""

    def has_permission(self, request, view):
        # basic check: must at least be authenticated
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # admins and superusers always allowed
        if request.user.is_admin() or request.user.is_superuser_role():
            return True
        # organizer may manage their own event
        if hasattr(obj, "organizer") and obj.organizer == request.user:
            return True
        return False


class CanManageTickets(permissions.BasePermission):
    """Allow access to users who can manage tickets"""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.has_permission_to_manage_tickets()
        )


class CanManageRegistrations(permissions.BasePermission):
    """Allow access to users who can manage registrations"""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.has_permission_to_manage_registrations()
        )


class CanManagePayments(permissions.BasePermission):
    """Allow access to users who can manage payments"""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.has_permission_to_manage_payments()
        )
