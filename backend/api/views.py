import uuid

from django.contrib.auth import get_user_model
from django.db.models import (
    BooleanField,
    Count,
    Exists,
    OuterRef,
    Prefetch,
    Sum,
    Value,
)
from django.http import HttpResponse
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from api.filters import RecipeFilter
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    AvatarSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeMinifiedSerializer,
    RecipeSerializer,
    ShoppingCartSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UserWithRecipesSerializer,
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShortLink,
    ShoppingCart,
    Tag,
)

User = get_user_model()


class RelationActionsMixin:
    """Mixin with reusable add/remove logic for user relations."""

    def _add_relation(self, obj, serializer_class, field):
        """Validate and create a relation, return the target serialized."""
        serializer = serializer_class(
            data={field: obj.id},
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            self.get_serializer(obj).data,
            status=status.HTTP_201_CREATED,
        )

    def _remove_relation(self, obj, related_name, field, message):
        """Delete a relation, raising 404 when it does not exist."""
        deleted, _ = getattr(self.request.user, related_name).filter(
            **{field + '_id': obj.id},
        ).delete()
        if not deleted:
            raise NotFound(message)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UnpaginatedReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset without pagination."""

    pagination_class = None


class TagViewSet(UnpaginatedReadOnlyViewSet):
    """Read-only viewset for tags."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(UnpaginatedReadOnlyViewSet):
    """Read-only viewset for ingredients."""

    serializer_class = IngredientSerializer

    def get_queryset(self):
        """Filter ingredients by name prefix."""
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class RecipeViewSet(RelationActionsMixin, viewsets.ModelViewSet):
    """Recipe CRUD with favorites, cart and short links."""

    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        """Return a minified serializer for the relation actions."""
        if self.action in ('favorite', 'shopping_cart'):
            return RecipeMinifiedSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        """Return recipes annotated with user list flags."""
        user = self.request.user
        queryset = (
            Recipe.objects.select_related('author')
            .prefetch_related(
                'tags',
                'recipe_ingredients__ingredient',
            )
            .order_by('-created')
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

    @action(detail=True, methods=('post',))
    def favorite(self, request, pk=None):
        """Add a recipe to the user's favorites."""
        recipe = self.get_object()
        return self._add_relation(recipe, FavoriteSerializer, 'recipe')

    @favorite.mapping.delete
    def remove_from_favorite(self, request, pk=None):
        """Remove a recipe from the user's favorites."""
        recipe = self.get_object()
        return self._remove_relation(
            recipe,
            'favorite',
            'recipe',
            'Рецепт не в избранном.',
        )

    @action(detail=True, methods=('post',))
    def shopping_cart(self, request, pk=None):
        """Add a recipe to the user's shopping cart."""
        recipe = self.get_object()
        return self._add_relation(recipe, ShoppingCartSerializer, 'recipe')

    @shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        """Remove a recipe from the user's shopping cart."""
        recipe = self.get_object()
        return self._remove_relation(
            recipe,
            'shoppingcart',
            'recipe',
            'Рецепта нет в списке покупок.',
        )

    @action(detail=True, url_path='get-link')
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
                    reverse('short-link', args=(short_link.short_id,))
                )
            },
        )

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        """Return the shopping cart as a text file."""
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__shoppingcart__user=request.user,
            )
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total=Sum('amount'))
            .order_by('ingredient__name')
        )
        lines = [
            ingredient_data['ingredient__name']
            + ' ('
            + ingredient_data['ingredient__measurement_unit']
            + ') — '
            + str(ingredient_data['total'])
            for ingredient_data in ingredients
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


class UserViewSet(RelationActionsMixin, DjoserUserViewSet):
    """User viewset extended with subscriptions and avatar."""

    def get_permissions(self):
        """Allow anonymous users to view profiles."""
        if self.action == 'retrieve':
            return [AllowAny()]
        return super().get_permissions()

    def get_serializer_class(self):
        """Return the user-with-recipes serializer for subscriptions."""
        if self.action in ('subscribe', 'subscriptions'):
            return UserWithRecipesSerializer
        return super().get_serializer_class()

    @action(detail=True, methods=('post',))
    def subscribe(self, request, id=None):
        """Subscribe the current user to another user."""
        author = self.get_object()
        author.recipes_count = author.recipes.count()
        return self._add_relation(author, SubscriptionSerializer, 'author')

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        """Unsubscribe the current user from another user."""
        author = self.get_object()
        return self._remove_relation(
            author,
            'subscriptions',
            'author',
            'Вы не подписаны на этого пользователя.',
        )

    @action(detail=False)
    def subscriptions(self, request):
        """Return users the current user is subscribed to."""
        recipes_prefetch = Prefetch('recipes', to_attr='prefetched_recipes')
        authors = (
            User.objects.filter(followers__user=request.user)
            .annotate(recipes_count=Count('recipes'))
            .prefetch_related(recipes_prefetch)
            .order_by('-id')
            .distinct()
        )
        page = self.paginate_queryset(authors)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=('put',),
        url_path='me/avatar',
    )
    def me_avatar(self, request):
        """Set the avatar of the current user."""
        serializer = AvatarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.avatar = serializer.validated_data['avatar']
        request.user.save()
        return Response({'avatar': request.user.avatar.url})

    @me_avatar.mapping.delete
    def delete_avatar(self, request):
        """Delete the avatar of the current user."""
        if request.user.avatar:
            request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)
