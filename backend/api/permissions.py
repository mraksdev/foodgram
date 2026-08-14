from rest_framework.permissions import BasePermission, SAFE_METHODS

ACTIONS_OPEN_TO_ANY_AUTHENTICATED = (
    'favorite',
    'remove_from_favorite',
    'shopping_cart',
    'remove_from_shopping_cart',
)


class IsAuthorOrReadOnly(BasePermission):
    """Allow read to anyone and write only to the recipe author."""

    def has_object_permission(self, request, view, obj) -> bool:
        """Return whether the user may access the recipe."""
        if request.method in SAFE_METHODS:
            return True
        if view.action in ACTIONS_OPEN_TO_ANY_AUTHENTICATED:
            return True
        return obj.author == request.user
