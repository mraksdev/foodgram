from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import escape

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShortLink,
    ShoppingCart,
    Tag,
)


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


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Admin panel for recipe ingredients."""

    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
    autocomplete_fields = ('recipe', 'ingredient')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Admin panel for recipes."""

    list_display = ('id', 'name', 'author_link', 'favorite_count')
    search_fields = ('name', 'author__email', 'author__username')
    list_filter = ('tags',)
    inlines = (RecipeIngredientInline,)

    def get_queryset(self, request):
        """Annotate recipes with the number of favorites."""
        return super().get_queryset(request).select_related('author').annotate(
            favorite_count=Count('favorite'),
        )

    @admin.display(description='избранное')
    def favorite_count(self, recipe):
        """Return the number of favorites for a recipe."""
        return recipe.favorite_count

    @admin.display(description='автор')
    def author_link(self, recipe):
        """Return the author name as a link to the user."""
        return (
            '<a href="'
            + reverse('admin:users_user_change', args=(recipe.author.id,))
            + '">'
            + escape(recipe.author.username)
            + '</a>'
        )


@admin.register(ShortLink)
class ShortLinkAdmin(admin.ModelAdmin):
    """Admin panel for short links."""

    list_display = ('id', 'recipe', 'short_id')


class UserRecipeRelationAdmin(admin.ModelAdmin):
    """Base admin for favorite and shopping cart entries."""

    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__email', 'user__username', 'recipe__name')


@admin.register(Favorite)
class FavoriteAdmin(UserRecipeRelationAdmin):
    """Admin panel for favorites."""


@admin.register(ShoppingCart)
class ShoppingCartAdmin(UserRecipeRelationAdmin):
    """Admin panel for shopping cart entries."""
