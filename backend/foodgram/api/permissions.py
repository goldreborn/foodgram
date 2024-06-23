from rest_framework.permissions import BasePermission


class IsAuthenticatedUser(BasePermission):
    """
    Доступ авторизованному пользователю
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsOwnerOrReadOnly(BasePermission):
    """
    Доступ владельца к своему контенту или только чтение
    """
    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True

        return obj.owner == request.user
