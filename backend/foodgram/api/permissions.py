"""
Модуль для определения пользовательских разрешений.

Этот модуль предоставляет пользовательские разрешения,
используемые в представлениях.
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    """Разрешение, позволяющее редактировать объект только его владельцу."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user if obj.author is not None else False


class IsAuthenticatedUser(BasePermission):
    """Разрешение, позволяющее доступ только авторизованным пользователям."""

    def has_permission(self, request, view):
        return request.user is not None and request.user.is_authenticated
