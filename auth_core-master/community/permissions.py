from rest_framework.permissions import BasePermission

class IsBoardMember(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and hasattr(request.user, "profile") and request.user.profile.role in {"board", "admin"})
