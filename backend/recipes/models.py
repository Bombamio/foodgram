from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.urls import reverse
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError

from . import constants


User = get_user_model()


class NameModel(models.Model):
    '''
    Абстрактная модель с полем `name`.
    '''

    name = models.CharField(
        'Название', max_length=constants.MAX_NAME_LENGTH, unique=True
    )

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class Tag(NameModel):
    '''
    Теги для рецептов (завтрак, обед, ужин).

    Поля: `name`, `slug`.
    '''

    slug = models.SlugField(
        'Слаг',
        unique=True,
        max_length=constants.MAX_SLUG_LENGTH,
        blank=True
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1

            # Используем self.__class__ чтобы работало для любых моделей
            while self.__class__.objects.filter(slug=slug).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = ('Тег')
        verbose_name_plural = ('Теги')

    def get_absolute_url(self):
        return reverse('tag_detail', kwargs={'slug': self.slug})


class Ingredients(models.Model):
    '''
    Ингридиенты к блюдам.

    Поля: `name`, `measurement_unit`.
    '''

    name = models.CharField(
        'Название', max_length=constants.MAX_NAME_LENGTH, unique=True
    )
    measurement_unit = models.CharField('Единица измерения')

    class Meta:
        verbose_name = ('Ингридиент')
        verbose_name_plural = ('Ингридиенты')
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient',
            ),
        ]

    def get_absolute_url(self):
        return reverse('ingredients_detail', kwargs={'pk': self.pk})

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class RecipeIngredients(models.Model):
    '''
    Промежуточная связь какой ингредиент в каком рецепте и сколько.

    Поля: `ingredients`, `recipe`, `amount`.
    '''

    ingredients = models.ForeignKey(
        Ingredients,
        verbose_name=('Ингридиент'),
        on_delete=models.CASCADE,
        related_name='ingredients_in_recipe',
    )
    recipe = models.ForeignKey(
        'Recipe',
        verbose_name=('Рецепт'),
        on_delete=models.CASCADE,
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[MinValueValidator(constants.MIN_AMOUNT_VALUE)]
    )

    class Meta:
        verbose_name = ('Ингридиент')
        verbose_name_plural = ('Ингридиенты')
        constraints = [
            models.UniqueConstraint(
                fields=('ingredients', 'recipe'),
                name='unique_ingredients_in_recipe'
            )
        ]

    def __str__(self):
        return f'{self.ingredients} - {self.amount}'


class Recipe(models.Model):
    '''
    Рецепты блюд.

    Поля: `name`, `author`, `image`, `text`, `ingredients`,
    `tags`, `cooking_time`, `is_favorited`, `is_in_shopping_cart`.
    '''

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name=('Автор'),
    )
    name = models.CharField('Название', max_length=constants.MAX_NAME_LENGTH)
    image = models.ImageField(
        upload_to='api/images/',
        null=True,
        default=None,
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
    cooking_time = models.PositiveIntegerField('Время приготовления (мин)')
    is_favorited = models.BooleanField(
        'Избранное',
        default=False,
    )
    is_in_shopping_cart = models.BooleanField(
        'В списке покупок',
        default=False,
    )

    class Meta:
        verbose_name = ('Рецепт')
        verbose_name_plural = ('Рецепты')
        ordering = ('-id',)

    def get_absolute_url(self):
        return reverse('recipe_detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.name


class Favorite(models.Model):
    '''
    Промежуточная связь пользователь добавил рецепт в избранное.

    Поля: `user`, `recipe`.
    '''

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name=('Пользователь'),
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name=('Рецепт'),
    )

    class Meta:
        verbose_name = ('Избранное')
        verbose_name_plural = ('Избраные')
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class ShoppingCart(models.Model):
    '''
    Промежуточная связь пользователь добавил рецепт в список покупок.

    Поля: `user`, `recipe`.
    '''

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shoppong_carts',
        verbose_name=('Пользователь'),
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shoppong_carts',
        verbose_name=('Рецепт'),
    )

    class Meta:
        verbose_name = ('Список покупок')
        verbose_name_plural = ('Списки покупок')
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shoppong_cart'
            )
        ]

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class Subscription(models.Model):
    '''
    Промежуточная связь подписка пользователя на автора.

    Поля: `user`, `author`.
    '''

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions_as_follower',
        verbose_name=('Пользователь'),
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions_as_author',
        verbose_name=('Автор'),
    )

    class Meta:
        verbose_name = ('Подписка')
        verbose_name_plural = ('Подписки')
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_subscription'
            )
        ]

    def clean(self):
        if self.user == self.author:
            raise ValidationError('Нельзя подписаться на самого себя')

    def __str__(self):
        return f'{self.user} - {self.author}'
