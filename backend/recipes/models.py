from django.db import models


class Tag(models.Model):
    """Recipe tag, e.g. breakfast or dinner."""

    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ('name',)

    def __str__(self) -> str:
        return self.name


class Ingredient(models.Model):
    """Ingredient with its measurement unit."""

    name = models.CharField(max_length=200)
    measurement_unit = models.CharField(max_length=200)

    class Meta:
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient',
            ),
        ]

    def __str__(self) -> str:
        return self.name


class Recipe(models.Model):
    """Recipe created by an author."""

    author = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='recipes',
    )
    name = models.CharField(max_length=256)
    image = models.ImageField(
        upload_to='recipes/',
        blank=True,
        null=True,
    )
    text = models.TextField()
    cooking_time = models.PositiveSmallIntegerField()
    created = models.DateTimeField(auto_now_add=True)
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
    )

    class Meta:
        ordering = ('-created',)

    def __str__(self) -> str:
        return self.name


class RecipeIngredient(models.Model):
    """Ingredient with amount inside a recipe."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
    )
    amount = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.ingredient} in {self.recipe}'


class Favorite(models.Model):
    """Recipe added to a user's favorites."""

    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='favorites',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.user} likes {self.recipe}'


class ShoppingCart(models.Model):
    """Recipe added to a user's shopping cart."""

    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='shopping_cart',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_cart',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.user} buys {self.recipe}'


class ShortLink(models.Model):
    """Stable short code for a recipe link."""

    recipe = models.OneToOneField(
        Recipe,
        on_delete=models.CASCADE,
        related_name='short_link',
    )
    short_id = models.CharField(max_length=20, unique=True)

    def __str__(self) -> str:
        return self.short_id
