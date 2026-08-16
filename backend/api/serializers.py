from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from api.fields import Base64ImageField
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Subscription

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    """Serializer for a tag."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class TagField(serializers.PrimaryKeyRelatedField):
    """Tag field that renders full tag objects on read."""

    def to_representation(self, tag):
        """Return the serialized tag object."""
        return TagSerializer(tag, context=self.context).data


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for an ingredient."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Serializer for an ingredient inside a recipe."""

    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all(),
    )
    name = serializers.CharField(read_only=True)
    measurement_unit = serializers.CharField(read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def to_representation(self, instance):
        """Expose the ingredient data on the recipe ingredient."""
        return {
            'id': instance.ingredient.id,
            'name': instance.ingredient.name,
            'measurement_unit': instance.ingredient.measurement_unit,
            'amount': instance.amount,
        }


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Short recipe serializer."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class AvatarSerializer(serializers.Serializer):
    """Serializer for setting a user avatar."""

    avatar = Base64ImageField()


class UserFieldsMixin(serializers.Serializer):
    """Mixin with is_subscribed and avatar fields for users."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj) -> bool:
        """Return whether the current user subscribes to this user."""
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        return user.subscriptions.filter(author_id=obj.id).exists()

    def get_avatar(self, obj):
        """Return the avatar URL or None."""
        if not obj.avatar:
            return None
        return obj.avatar.url


class UserSerializer(UserFieldsMixin, DjoserUserSerializer):
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


class UserWithRecipesSerializer(UserFieldsMixin, serializers.ModelSerializer):
    """User serializer with recipes and their count."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True)

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

    def get_recipes(self, obj):
        """Return user recipes limited by the recipes_limit parameter."""
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


class RecipeSerializer(serializers.ModelSerializer):
    """Full recipe serializer for read and write."""

    author = UserSerializer(read_only=True)
    tags = TagField(
        queryset=Tag.objects.all(),
        many=True,
        allow_empty=False,
    )
    ingredients = IngredientInRecipeSerializer(
        many=True,
        source='recipe_ingredients',
        allow_empty=False,
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=1)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj) -> bool:
        """Return whether the recipe is in the user's favorites."""
        annotated = getattr(obj, 'is_favorited', None)
        if annotated is not None:
            return annotated
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.favorite.filter(user=request.user).exists()

    def get_is_in_shopping_cart(self, obj) -> bool:
        """Return whether the recipe is in the user's cart."""
        annotated = getattr(obj, 'is_in_shopping_cart', None)
        if annotated is not None:
            return annotated
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.shoppingcart.filter(user=request.user).exists()

    def validate_tags(self, value):
        """Reject duplicate tags."""
        slugs = [tag.slug for tag in value]
        if len(slugs) != len(set(slugs)):
            raise serializers.ValidationError('Теги не могут повторяться.')
        return value

    def validate_ingredients(self, value):
        """Reject duplicate ingredients."""
        ingredient_ids = [
            item['ingredient'].id for item in value
        ]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не могут повторяться.'
            )
        return value

    def create(self, validated_data):
        """Create a recipe with ingredients and tags."""
        ingredients = validated_data.pop('recipe_ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self._save_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        """Update a recipe with ingredients and tags."""
        ingredients = validated_data.pop('recipe_ingredients', None)
        tags = validated_data.pop('tags', None)
        recipe = super().update(instance, validated_data)
        if ingredients is not None:
            recipe.recipe_ingredients.all().delete()
            self._save_ingredients(recipe, ingredients)
        if tags is not None:
            recipe.tags.set(tags)
        return recipe

    def _save_ingredients(self, recipe, ingredients) -> None:
        """Create recipe ingredient rows."""
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount'],
            )
            for item in ingredients
        )


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer to subscribe the current user to an author."""

    class Meta:
        model = Subscription
        fields = ('author',)

    def validate_author(self, author):
        """Reject self-subscription and duplicate subscriptions."""
        user = self.context['request'].user
        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.'
            )
        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError('Вы уже подписаны.')
        return author

    def create(self, validated_data):
        """Create a subscription for the current user."""
        user = self.context['request'].user
        return Subscription.objects.create(
            user=user,
            author=validated_data['author'],
        )


class FavoriteSerializer(serializers.ModelSerializer):
    """Serializer to add a recipe to the user's favorites."""

    class Meta:
        model = Favorite
        fields = ('recipe',)

    def validate_recipe(self, recipe):
        """Reject a recipe already in the user's favorites."""
        user = self.context['request'].user
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError('Рецепт уже в избранном.')
        return recipe

    def create(self, validated_data):
        """Create a favorite entry for the current user."""
        user = self.context['request'].user
        return Favorite.objects.create(
            user=user,
            recipe=validated_data['recipe'],
        )


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Serializer to add a recipe to the user's shopping cart."""

    class Meta:
        model = ShoppingCart
        fields = ('recipe',)

    def validate_recipe(self, recipe):
        """Reject a recipe already in the user's shopping cart."""
        user = self.context['request'].user
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                'Рецепт уже в списке покупок.'
            )
        return recipe

    def create(self, validated_data):
        """Create a shopping cart entry for the current user."""
        user = self.context['request'].user
        return ShoppingCart.objects.create(
            user=user,
            recipe=validated_data['recipe'],
        )
