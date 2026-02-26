import base64

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from . import constants
from recipes.models import (
    Favorite,
    Ingredients,
    Recipe,
    RecipeIngredients,
    ShoppingCart,
    Subscription,
    Tag,
)


User = get_user_model()


class Base64ImageField(serializers.ImageField):

    def to_internal_value(self, data):

        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class UserSerializer(DjoserUserSerializer):
    '''Сериализатор, для списка пользователей с проверкой подписки.'''

    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        read_only_fields = (
            *DjoserUserSerializer.Meta.fields,
            'is_subscribed', 'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user,
                author=obj
            ).exists()
        return False


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredients
        fields = '__all__'


class RecipeIngredientsReadSerializer(serializers.ModelSerializer):

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientsWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredients.objects.all(),
        source='ingredients'
    )
    amount = serializers.IntegerField(
        min_value=constants.INGREDIENT_MIN_AMOUNT
    )

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    '''Сериализатор для списка рецептов.'''

    author = UserSerializer()
    ingredients = RecipeIngredientsReadSerializer(
        source='ingredients_in_recipe',
        many=True,
    )
    tags = TagSerializer(many=True)
    image = Base64ImageField(required=False, allow_null=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        read_only_fields = (
            'id', 'name', 'author', 'image', 'text',
            'ingredients', 'tags', 'cooking_time',
            'is_favorited', 'is_in_shopping_cart',
        )

    def check_user_status(self, obj, model_class):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return model_class.objects.filter(
                user=request.user,
                author=obj
            ).exists()
        return False

    def get_is_favorited(self, obj):
        return self.check_user_status(obj, Favorite)

    def get_is_in_shopping_cart(self, obj):
        return self.check_user_status(obj, ShoppingCart)


class RecipeWriteSerializer(serializers.ModelSerializer):
    '''Сериализатор для добавления рецептов.'''

    ingredients = RecipeIngredientsWriteSerializer(
        many=True,
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    image = Base64ImageField(required=False, allow_null=True)
    cooking_time = serializers.IntegerField(
        min_value=constants.INGREDIENT_MIN_AMOUNT
    )

    class Meta:
        model = Recipe
        fields = (
            'name', 'image', 'text',
            'ingredients', 'tags', 'cooking_time',
        )

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Должен быть указан хотя бы один ингредиент.'
            )
        ingredient_ids = [item['ingredients'].id for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты должны быть уникальными.'
            )
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Должен быть указан хотя бы один тег.'
            )
        tag_ids = [item.id for item in value]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError(
                'Теги должны быть уникальными.'
            )
        return value

    def validate_cooking_time(self, value):
        if value < constants.INGREDIENT_MIN_AMOUNT:
            raise serializers.ValidationError(
                'Время приготовления должно быть больше нуля.'
            )
        return value

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)

        for ingredient in ingredients_data:
            RecipeIngredients.objects.create(
                recipe=recipe,
                ingredient=ingredient['ingredients'],
                amount=ingredient['amount']
            )

        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if tags_data is not None:
            instance.tags.set(tags_data)

        if ingredients_data is not None:
            instance.ingredients_in_recipe.all().delete()
            recipe_ingredients = [
                RecipeIngredients(
                    recipe=instance,
                    ingredient=ingredient['ingredients'],
                    amount=ingredient['amount']
                )
                for ingredient in ingredients_data
            ]
            RecipeIngredients.objects.bulk_create(recipe_ingredients)

        instance.save()
        return instance


class ShortRecipeSerializer(serializers.ModelSerializer):
    '''Сериализатор для краткого отображения рецепта.'''

    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    '''Сериализатор для отображения подписок.'''

    recipes = ShortRecipeSerializer(many=True)
    recipes_count = serializers.IntegerField(source='recipes.count')

    class Meta:
        model = User
        read_only_fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_subscribed', 'avatar', 'recipes', 'recipes_count',
        )


class TokenObtainSerializer(serializers.Serializer):
    '''Сериализатор для получения JWT токена.'''

    username = serializers.CharField(required=True)
    confirmation_code = serializers.CharField(required=True)

    def validate(self, data):
        username = data.get('username')
        confirmation_code = data.get('confirmation_code')

        user = get_object_or_404(User, username=username)

        if not default_token_generator.check_token(
            user, confirmation_code
        ):
            raise serializers.ValidationError(
                'Неверный код подтверждения'
            )

        data['user'] = user
        return data
