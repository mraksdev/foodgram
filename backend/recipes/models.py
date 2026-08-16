from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

MAX_RECIPE_INGREDIENT_AMOUNT = 32000


class Tag(models.Model):
    """Recipe tag, e.g. breakfast or dinner."""

    name = models.CharField('название', max_length=200, unique=True)
    slug = models.SlugField('слаг', max_length=200, unique=True)

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'теги'
        ordering = ('name',)

    def __str__(self) -> str:
        return self.name


class Ingredient(models.Model):
    """Ingredient with its measurement unit."""

    name = models.CharField('название', max_length=200)
    measurement_unit = models.CharField(
        'единица измерения',
        max_length=200,
    )

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'ингредиенты'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
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
        verbose_name='автор',
    )
    name = models.CharField('название', max_length=256)
    image = models.ImageField('изображение', upload_to='recipes/')
    text = models.TextField('описание')
    cooking_time = models.PositiveSmallIntegerField('время приготовления')
    created = models.DateTimeField('дата создания', auto_now_add=True)
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='теги',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='ингредиенты',
    )

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'рецепты'
        ordering = ('-created',)

    def __str__(self) -> str:
        return self.name


class RecipeIngredient(models.Model):
    """Ingredient with amount inside a recipe."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        'количество',
        validators=[
            MinValueValidator(1),
            MaxValueValidator(MAX_RECIPE_INGREDIENT_AMOUNT),
        ],
    )

    class Meta:
        verbose_name = 'ингредиент рецепта'
        verbose_name_plural = 'ингредиенты рецепта'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient',
            ),
        ]

    def __str__(self) -> str:
        return str(self.ingredient) + ' in ' + str(self.recipe)


class UserRecipeRelation(models.Model):
    """Abstract base for a user-recipe relation."""

    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        verbose_name='пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='рецепт',
    )

    class Meta:
        abstract = True
        default_related_name = '%(class)s'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_%(class)s',
            ),
        ]

    def __str__(self) -> str:
        return str(self.user) + ' -> ' + str(self.recipe)


class Favorite(UserRecipeRelation):
    """Recipe added to a user's favorites."""

    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'избранное'
        verbose_name_plural = 'избранное'


class ShoppingCart(UserRecipeRelation):
    """Recipe added to a user's shopping cart."""

    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'список покупок'
        verbose_name_plural = 'список покупок'


class ShortLink(models.Model):
    """Stable short code for a recipe link."""

    recipe = models.OneToOneField(
        Recipe,
        on_delete=models.CASCADE,
        related_name='short_link',
        verbose_name='рецепт',
    )
    short_id = models.CharField('короткий код', max_length=20, unique=True)

    class Meta:
        verbose_name = 'короткая ссылка'
        verbose_name_plural = 'короткие ссылки'

    def __str__(self) -> str:
        return self.short_id
