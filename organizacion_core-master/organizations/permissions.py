from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsBoardOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        role = request.auth.get("role") if request.auth else None
        return role in {"board", "admin"}
