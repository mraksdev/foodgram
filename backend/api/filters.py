from django_filters import rest_framework as filters

from recipes.models import Recipe


class RecipeFilter(filters.FilterSet):
    """Filter recipes by tags, author and user lists."""

    tags = filters.CharFilter(
        method='filter_tags',
        distinct=True,
    )
    is_favorited = filters.BooleanFilter(field_name='is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        field_name='is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def filter_tags(self, queryset, name, slug):
        """Filter recipes by the tag slug."""
        slugs = self.request.GET.getlist(name) or [slug]
        return queryset.filter(tags__slug__in=slugs).distinct()
