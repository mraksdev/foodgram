from django.contrib.auth import get_user_model
from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer,
)
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from api.fields import Base64ImageField

User = get_user_model()


class AvatarSerializer(serializers.Serializer):
    """Serializer for setting a user avatar."""

    avatar = Base64ImageField(required=True)


class UserFieldsMixin(serializers.Serializer):
    """Mixin with is_subscribed and avatar fields for users."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj) -> bool:
        """Return whether the current user subscribes to this user."""
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user is None or user.is_anonymous:
            return False
        return user.subscriptions.filter(author=obj).exists()

    def get_avatar(self, obj):
        """Return the avatar URL or None."""
        if not obj.avatar:
            return None
        return obj.avatar.url


class CustomUserSerializer(UserFieldsMixin, DjoserUserSerializer):
    """User serializer with subscription and avatar fields."""

    class Meta(DjoserUserSerializer.Meta):
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'avatar',
        )


class CustomUserCreateSerializer(DjoserUserCreateSerializer):
    """Registration serializer."""

    class Meta(DjoserUserCreateSerializer.Meta):
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'password',
        )


class UserWithRecipesSerializer(UserFieldsMixin, serializers.ModelSerializer):
    """User serializer with recipes and their count."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'avatar',
            'recipes_count',
            'recipes',
        )

    def get_recipes_count(self, obj) -> int:
        """Return the number of recipes of the user."""
        annotated = getattr(obj, 'recipes_count', None)
        if annotated is not None:
            return annotated
        return obj.recipes.count()

    def get_recipes(self, obj):
        """Return user recipes limited by the recipes_limit parameter."""
        from recipes.serializers import RecipeMinifiedSerializer

        recipes = getattr(
            obj,
            'prefetched_recipes',
            obj.recipes.all(),
        )
        request = self.context.get('request')
        recipes_limit = None
        if request is not None:
            recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit is not None:
            try:
                recipes = recipes[: int(recipes_limit)]
            except ValueError:
                pass
        return RecipeMinifiedSerializer(
            recipes,
            many=True,
            context=self.context,
        ).data
