from rest_framework import permissions


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Anyone authenticated can read (list/retrieve). Only staff users can
    create/update/delete -- used for Category and Product management.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsOwnerOrStaff(permissions.BasePermission):
    """
    Used for Invoice management. Any authenticated user can create an
    invoice (create_by is set to the requester). Reading is open to any
    authenticated user. Updating/deleting an invoice is only allowed for
    the user who created it, or staff.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        # Creation is allowed for any authenticated user; object-level
        # checks below handle update/delete restrictions.
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff or obj.created_by_id == request.user.id
