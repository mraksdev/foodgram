from rest_framework import serializers

from api.fields import Base64ImageField
from recipes.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Tag,
)
from users.serializers import CustomUserSerializer


class TagSerializer(serializers.ModelSerializer):
    """Serializer for a tag."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class TagField(serializers.PrimaryKeyRelatedField):
    """Tag field that renders full tag objects on read."""

    def to_representation(self, value):
        """Return the serialized tag object."""
        return TagSerializer(value, context=self.context).data


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
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def to_representation(self, instance):
        """Expose the ingredient data on the recipe ingredient."""
        instance.id = instance.ingredient.id
        instance.name = instance.ingredient.name
        instance.measurement_unit = instance.ingredient.measurement_unit
        return super().to_representation(instance)


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Short recipe serializer."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeSerializer(serializers.ModelSerializer):
    """Full recipe serializer for read and write."""

    author = CustomUserSerializer(read_only=True)
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
        if not request or request.user.is_anonymous:
            return False
        return obj.favorited_by.filter(user=request.user).exists()

    def get_is_in_shopping_cart(self, obj) -> bool:
        """Return whether the recipe is in the user's cart."""
        annotated = getattr(obj, 'is_in_shopping_cart', None)
        if annotated is not None:
            return annotated
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.in_shopping_cart.filter(user=request.user).exists()

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
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if ingredients is not None:
            instance.recipe_ingredients.all().delete()
            self._save_ingredients(instance, ingredients)
        if tags is not None:
            instance.tags.set(tags)
        return instance

    def _save_ingredients(self, recipe, ingredients) -> None:
        """Create recipe ingredient rows."""
        RecipeIngredient.objects.bulk_create(
            [
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=item['ingredient'],
                    amount=item['amount'],
                )
                for item in ingredients
            ]
        )
