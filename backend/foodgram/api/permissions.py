from rest_framework import permissions


class AnonymousOnly(permissions.BasePermission):
    message = 'Доступ запрещен'

    def has_permission(self, request, view):
        return not request.user.is_authenticated


class RecipePermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )
