from django.db import models


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
    amount = models.PositiveSmallIntegerField('количество')

    class Meta:
        verbose_name = 'ингредиент рецепта'
        verbose_name_plural = 'ингредиенты рецепта'
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
        verbose_name='пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='рецепт',
    )

    class Meta:
        verbose_name = 'избранное'
        verbose_name_plural = 'избранное'
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
        verbose_name='пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_cart',
        verbose_name='рецепт',
    )

    class Meta:
        verbose_name = 'список покупок'
        verbose_name_plural = 'список покупок'
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
        verbose_name='рецепт',
    )
    short_id = models.CharField('короткий код', max_length=20, unique=True)

    class Meta:
        verbose_name = 'короткая ссылка'
        verbose_name_plural = 'короткие ссылки'

    def __str__(self) -> str:
        return self.short_id
