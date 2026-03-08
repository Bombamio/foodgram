from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse

from . import constants


User = get_user_model()


class Tag(models.Model):
    """
    Теги для рецептов (завтрак, обед, ужин).

    Поля: `name`, `slug`.
    """
    name = models.CharField(
        'Название', max_length=constants.TAG_NAME_MAX_LENGTH, unique=True
    )
    slug = models.SlugField(
        'Слаг',
        unique=True,
        max_length=constants.TAG_SLUG_MAX_LENGTH,
    )

    class Meta:
        ordering = ('name',)
        verbose_name = ('Тег')
        verbose_name_plural = ('Теги')

    def __str__(self):
        return self.name


class Ingredients(models.Model):
    """
    Ингредиенты к блюдам.

    Поля: `name`, `measurement_unit`.
    """

    name = models.CharField(
        'Название', max_length=constants.INGREDIENT_NAME_MAX_LENGTH
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=constants.INGREDIENT_MEASUREMENT_UNIT_MAX_LENGTH
    )

    class Meta:
        verbose_name = ('Ингредиент')
        verbose_name_plural = ('Ингредиенты')
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient',
            ),
        ]

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class RecipeIngredients(models.Model):
    """
    Промежуточная связь какой ингредиент в каком рецепте и сколько.

    Поля: `ingredients`, `recipe`, `amount`.
    """

    ingredients = models.ForeignKey(
        Ingredients,
        verbose_name=('Ингредиент'),
        on_delete=models.CASCADE,
        related_name='ingredients_in_recipe',
    )
    recipe = models.ForeignKey(
        'Recipe',
        verbose_name=('Рецепт'),
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[
            MinValueValidator(constants.INGREDIENT_MIN_AMOUNT_VALUE),
            MaxValueValidator(constants.INGREDIENT_MAX_AMOUNT_VALUE)
        ]
    )

    class Meta:
        verbose_name = ('Ингредиент')
        verbose_name_plural = ('Ингредиенты')
        constraints = [
            models.UniqueConstraint(
                fields=('ingredients', 'recipe'),
                name='unique_ingredients_in_recipe'
            )
        ]

    def __str__(self):
        return f'{self.ingredients} - {self.amount}'


class Recipe(models.Model):
    """
    Рецепты блюд.

    Поля: `name`, `author`, `image`, `text`, `ingredients`,
    `tags`, `cooking_time`, `is_favorited`, `is_in_shopping_cart`.
    """

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name=('Автор'),
    )
    name = models.CharField(
        'Название', max_length=constants.RECIPE_NAME_MAX_LENGTH
    )
    image = models.ImageField(
        upload_to='api/images/',
        null=True,
        blank=True,
    )
    text = models.TextField('Описание')
    ingredients = models.ManyToManyField(
        Ingredients,
        through=RecipeIngredients,
        verbose_name='Ингридиенты',
        related_name='recipes',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name=('Теги'),
        related_name='recipes',
    )
    cooking_time = models.PositiveIntegerField(
        'Время приготовления (мин)',
        validators=[
            MinValueValidator(constants.RECIPE_COOKING_TIME_MIN_VALUE),
            MaxValueValidator(constants.RECIPE_COOKING_TIME_MAX_VALUE)
        ]
    )

    class Meta:
        verbose_name = ('Рецепт')
        verbose_name_plural = ('Рецепты')
        ordering = ('name', 'author')

    def get_absolute_url(self):
        return reverse('recipe-detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.name


class UserRecipeRelationBase(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)s',
        verbose_name=('Пользователь'),
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='%(class)s',
        verbose_name=('Рецепт'),
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_%(class)s'
            )
        ]

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class Favorite(UserRecipeRelationBase):
    """
    Промежуточная связь пользователь добавил рецепт в избранное.

    Поля: `user`, `recipe`.
    """
    class Meta(UserRecipeRelationBase.Meta):
        verbose_name = ('Избранное')
        verbose_name_plural = ('Избранные')


class ShoppingCart(UserRecipeRelationBase):
    """
    Промежуточная связь пользователь добавил рецепт в список покупок.

    Поля: `user`, `recipe`.
    """
    class Meta(UserRecipeRelationBase.Meta):
        verbose_name = ('Список покупок')
        verbose_name_plural = ('Списки покупок')
