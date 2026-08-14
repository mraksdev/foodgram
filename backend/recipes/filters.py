from django_filters import rest_framework as filters

from recipes.models import Recipe


class RecipeFilter(filters.FilterSet):
    """Filter recipes by tags, author and user lists."""

    tags = filters.CharFilter(
        method='filter_tags',
        distinct=True,
    )
    author = filters.NumberFilter(field_name='author__id')
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited',
        distinct=True,
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart',
        distinct=True,
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def filter_tags(self, queryset, name, value):
        """Filter recipes by the tag slug."""
        return queryset.filter(tags__slug=value)

    def filter_is_favorited(self, queryset, name, value):
        """Filter recipes by the current user's favorites."""
        user = self.request.user
        if user.is_anonymous:
            return queryset.none()
        if value:
            return queryset.filter(favorited_by__user=user)
        return queryset.exclude(favorited_by__user=user)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Filter recipes by the current user's shopping cart."""
        user = self.request.user
        if user.is_anonymous:
            return queryset.none()
        if value:
            return queryset.filter(in_shopping_cart__user=user)
        return queryset.exclude(in_shopping_cart__user=user)
