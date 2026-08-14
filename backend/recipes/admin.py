from django.contrib import admin
from django.db.models import Count

from .models import Ingredient, Recipe, RecipeIngredient, ShortLink, Tag


class RecipeIngredientInline(admin.TabularInline):
    """Inline editor for ingredients of a recipe."""

    model = RecipeIngredient
    extra = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin panel for tags."""

    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Admin panel for ingredients."""

    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Admin panel for recipes."""

    list_display = ('id', 'name', 'author', 'favorite_count')
    search_fields = ('name', 'author__email', 'author__username')
    list_filter = ('tags',)
    inlines = (RecipeIngredientInline,)

    def get_queryset(self, request):
        """Annotate recipes with the number of favorites."""
        return super().get_queryset(request).annotate(
            favorite_count=Count('favorited_by'),
        )

    @admin.display(description='избранное')
    def favorite_count(self, obj):
        """Return the number of favorites for a recipe."""
        return obj.favorite_count


@admin.register(ShortLink)
class ShortLinkAdmin(admin.ModelAdmin):
    """Admin panel for short links."""

    list_display = ('id', 'recipe', 'short_id')
