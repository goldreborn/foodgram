"""Модуль с кастомными правами доступа для REST API."""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """Класс прав доступа для администратора или только для чтения."""

    def has_permission(self, request, view):
        """
        Метод проверки прав доступа для запроса.

        Args:
            request: запрос
            view: представление

        Returns:
            bool: True если запрос разрешен, False иначе
        """
        if request.method in ['GET']:
            return True
        elif request.method in ['POST', 'PUT', 'DELETE']:
            return request.user.is_staff
        return False


class IsAdminAuthorOrReadOnly(BasePermission):
    """Класс прав доступа для автора либо администратора."""

    def has_permission(self, request, view):
        """
        Метод проверки прав доступа для запроса.

        Args:
            request: запрос
            view: представление

        Returns:
            bool: True если запрос разрешен, False иначе
        """
        return (request.method in SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        """
        Метод проверки прав доступа для объекта.

        Args:
            request: запрос
            view: представление
            obj: объект

        Returns:
            bool: True если запрос разрешен, False иначе
        """
        return (request.method in SAFE_METHODS
                or request.user.is_superuser
                or request.user.is_staff
                or obj.author == request.user)
