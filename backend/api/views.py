import uuid

from django.db.models import BooleanField, Exists, OuterRef, Sum, Value
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from api.permissions import IsAuthorOrReadOnly
from recipes.filters import RecipeFilter
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    ShortLink,
    ShoppingCart,
    Tag,
)
from recipes.serializers import (
    IngredientSerializer,
    RecipeMinifiedSerializer,
    RecipeSerializer,
    TagSerializer,
)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for tags."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for ingredients."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None

    def get_queryset(self):
        """Filter ingredients by name prefix."""
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    """Recipe CRUD with favorites, cart and short links."""

    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        """Return recipes annotated with user list flags."""
        user = self.request.user
        queryset = Recipe.objects.select_related(
            'author',
        ).prefetch_related(
            'tags',
            'recipe_ingredients__ingredient',
        )
        if user.is_authenticated:
            return queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user=user,
                        recipe=OuterRef('pk'),
                    )
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=user,
                        recipe=OuterRef('pk'),
                    )
                ),
            )
        return queryset.annotate(
            is_favorited=Value(False, output_field=BooleanField()),
            is_in_shopping_cart=Value(False, output_field=BooleanField()),
        )

    def perform_create(self, serializer):
        """Set the current user as the recipe author."""
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'])
    def favorite(self, request, pk=None):
        """Add a recipe to the user's favorites."""
        recipe = self.get_object()
        _, created = Favorite.objects.get_or_create(
            user=request.user,
            recipe=recipe,
        )
        if not created:
            return Response(
                {'detail': 'Рецепт уже в избранном.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            RecipeMinifiedSerializer(recipe).data,
            status=status.HTTP_201_CREATED,
        )

    @favorite.mapping.delete
    def remove_from_favorite(self, request, pk=None):
        """Remove a recipe from the user's favorites."""
        recipe = self.get_object()
        deleted, _ = Favorite.objects.filter(
            user=request.user,
            recipe=recipe,
        ).delete()
        if not deleted:
            return Response(
                {'detail': 'Рецепт не в избранном.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def shopping_cart(self, request, pk=None):
        """Add a recipe to the user's shopping cart."""
        recipe = self.get_object()
        _, created = ShoppingCart.objects.get_or_create(
            user=request.user,
            recipe=recipe,
        )
        if not created:
            return Response(
                {'detail': 'Рецепт уже в списке покупок.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            RecipeMinifiedSerializer(recipe).data,
            status=status.HTTP_201_CREATED,
        )

    @shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        """Remove a recipe from the user's shopping cart."""
        recipe = self.get_object()
        deleted, _ = ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe,
        ).delete()
        if not deleted:
            return Response(
                {'detail': 'Рецепта нет в списке покупок.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        """Return a stable short link to the recipe."""
        recipe = self.get_object()
        short_link, _ = ShortLink.objects.get_or_create(
            recipe=recipe,
            defaults={'short_id': self._generate_short_id()},
        )
        return Response(
            {
                'short-link': request.build_absolute_uri(
                    f'/s/{short_link.short_id}/'
                )
            },
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        """Return the shopping cart as a text file."""
        recipes = Recipe.objects.filter(
            in_shopping_cart__user=request.user,
        )
        ingredients = (
            Ingredient.objects.filter(
                recipe_ingredients__recipe__in=recipes,
            )
            .values('name', 'measurement_unit')
            .annotate(total=Sum('recipe_ingredients__amount'))
            .order_by('name')
        )
        lines = [
            f'{item["name"]} ({item["measurement_unit"]}) — {item["total"]}'
            for item in ingredients
        ]
        response = HttpResponse(
            '\n'.join(lines),
            content_type='text/plain',
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    def _generate_short_id(self) -> str:
        """Generate a unique short id."""
        while True:
            short_id = uuid.uuid4().hex[:8]
            if not ShortLink.objects.filter(short_id=short_id).exists():
                return short_id


def short_link_redirect(request, short_id):
    """Redirect a short link to the recipe page."""
    try:
        short_link = ShortLink.objects.get(short_id=short_id)
    except ShortLink.DoesNotExist:
        raise Http404
    return redirect(f'/recipes/{short_link.recipe_id}/')
