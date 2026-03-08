from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from .fields import Base64ImageField
from recipes.models import (
    Ingredients,
    Recipe,
    RecipeIngredients,
    Tag,
)
from users.models import Subscription


User = get_user_model()


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для загрузки аватара."""

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class UserSerializer(DjoserUserSerializer):
    """Сериализатор, для списка пользователей с проверкой подписки."""

    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            *DjoserUserSerializer.Meta.fields,
            'is_subscribed', 'avatar',
        )
        read_only_fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and Subscription.objects.filter(
                user=request.user,
                author=obj
            ).exists()
        )


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredients
        fields = '__all__'


class RecipeIngredientsSerializer(serializers.ModelSerializer):

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredients.objects.all(),
        source='ingredients',
    )
    name = serializers.ReadOnlyField(source='ingredients.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredients.measurement_unit'
    )

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для списка рецептов."""

    author = UserSerializer()
    ingredients = RecipeIngredientsSerializer(
        source='recipe_ingredients',
        many=True,
    )
    tags = TagSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'author', 'image', 'text',
            'ingredients', 'tags', 'cooking_time',
            'is_favorited', 'is_in_shopping_cart',
        )
        read_only_fields = fields


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления рецептов."""

    ingredients = RecipeIngredientsSerializer(
        many=True,
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'text',
            'ingredients', 'tags', 'cooking_time',
        )

    def validate(self, data):
        ingredients = data.get('ingredients')
        tags = data.get('tags')

        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Должен быть указан хотя бы один ингредиент.'}
            )
        ingredient_ids = [item['ingredients'].pk for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты должны быть уникальными.'}
            )

        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Должен быть указан хотя бы один тег.'}
            )
        tag_ids = [item.id for item in tags]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError(
                {'tags': 'Теги должны быть уникальными.'}
            )

        return data

    def recipe_ingredients_create(self, recipe, ingredients_data):
        RecipeIngredients.objects.bulk_create([
            RecipeIngredients(
                recipe=recipe,
                ingredients=ingredient['ingredients'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients_data
        ])

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data,
        )
        recipe.tags.set(tags_data)

        self.recipe_ingredients_create(recipe, ingredients_data)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)

        instance = super().update(instance, validated_data)

        if tags_data is not None:
            instance.tags.set(tags_data)

        instance.recipe_ingredients.clear()
        self.recipe_ingredients_create(instance, ingredients_data)

        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance,
            context=self.context
        ).data


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого отображения рецепта."""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class SubscriptionSerializer(UserSerializer):
    """Сериализатор для отображения подписок."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='recipes.count')

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_subscribed', 'avatar', 'recipes', 'recipes_count',
        )

    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.author.avatar and hasattr(obj.avatar, 'url') and request:
            return obj.author.avatar.url
        return None

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.author.recipes.all()

        if request:
            recipes_limit = request.query_params.get('recipes_limit')
            if recipes_limit:
                try:
                    limit = int(recipes_limit)
                    recipes = recipes[:limit]
                except (ValueError, TypeError):
                    pass

        context = {'request': request} if request else {}
        return ShortRecipeSerializer(
            recipes,
            many=True,
            context=context
        ).data
