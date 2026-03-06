import os

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Exists, OuterRef
from django.urls import reverse
from djoser import views
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import APIView, action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from .permissions import IsAuthorOrReadOnly
from .filters import IngredientsFilter, RecipeFilter
from .pagination import RecipePagination
from recipes.models import (
    Recipe,
    Tag,
    Ingredients,
    RecipeIngredients,
    Favorite,
    ShoppingCart,
    Subscription
)
from .serializers import (
    RecipeWriteSerializer,
    RecipeReadSerializer,
    SubscriptionSerializer,
    ShortRecipeSerializer,
    TagSerializer,
    IngredientsSerializer,
    TokenObtainSerializer,
    UserSerializer,
)

User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Ingredients.objects.all()
    serializer_class = IngredientsSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientsFilter


class RecipeViewSet(viewsets.ModelViewSet):

    queryset = Recipe.objects.select_related(
        'author'
    ).prefetch_related(
        'tags',
        'recipe_ingredients__ingredients',
    )
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (
        DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter
    )
    ordering = ('-cooking_time',)
    filterset_class = RecipeFilter
    search_fields = ('name',)
    pagination_class = RecipePagination

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        if user.is_authenticated:

            if self.request.query_params.get('is_in_shopping_cart') == '1':
                queryset = queryset.filter(shoppingcart__user=user)

            if self.request.query_params.get('is_favorited') == '1':
                queryset = queryset.filter(favorite__user=user)

        return queryset

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(url_path='get-link', methods=['get'], detail=True)
    def get_short_link(self, request, pk=None):
        recipe = self.get_object()
        return Response(
            {'short-link': request.build_absolute_uri(
                reverse('recipe-detail', kwargs={'pk': recipe.pk})
            )},
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False,
            permission_classes=[permissions.IsAuthenticated])
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredients.objects.filter(
            recipe__shoppingcart__user=request.user
        ).values(
            'ingredients__name',
            'ingredients__measurement_unit'
        ).annotate(total_amount=models.Sum('amount'))

        if not ingredients.exists():
            return Response(
                {'detail': 'Ваш список покупок пуст.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        lines = [
            f"{item['ingredients__name']} - {item['total_amount']} "
            f"{item['ingredients__measurement_unit']}"
            for item in ingredients
        ]
        shopping_list = 'Список покупок:\n\n' + '\n'.join(lines)

        response = HttpResponse(
            shopping_list, status=status.HTTP_200_OK,
            content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = \
            'attachment; filename="shopping_list.txt"'
        return response

    @action(url_path='favorite', methods=['post', 'delete'], detail=True,
            permission_classes=[permissions.IsAuthenticated])
    def manage_favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            favorite, created = Favorite.objects.get_or_create(
                user=user,
                recipe=recipe
            )

            if not created:
                return Response(
                    {'errors': 'Рецепт уже в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = ShortRecipeSerializer(
                recipe,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        favorite = Favorite.objects.filter(user=user, recipe=recipe)

        if not favorite.exists():
            return Response(
                {'errors': 'Рецепта нет в избранном.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        url_path='shopping_cart', methods=['post', 'delete'],
        detail=True, permission_classes=[permissions.IsAuthenticated]
    )
    def manage_shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            cart, created = ShoppingCart.objects.get_or_create(
                user=user,
                recipe=recipe
            )

            if not created:
                return Response(
                    {'errors': 'Рецепт уже в списке покупок.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = ShortRecipeSerializer(
                recipe,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        cart = ShoppingCart.objects.filter(user=user, recipe=recipe)

        if not cart.exists():
            return Response(
                {'errors': 'Рецепта нет в списке покупок.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(views.UserViewSet):

    queryset = User.objects.all()
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    pagination_class = RecipePagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)

    @action(
        methods=['get'], detail=False,
        permission_classes=[permissions.IsAuthenticated]
    )
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    @action(
        url_path='me/avatar', methods=['put', 'delete'], detail=False,
        permission_classes=[permissions.IsAuthenticated]
    )
    def manage_avatar(self, request, *args, **kwargs):
        user = request.user

        if request.method == 'PUT':
            avatar = request.data.get('avatar')

            if not avatar:
                return Response(
                    {'avatar': ['Аватар не указан.']},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user.avatar = avatar
            user.save()

            return Response(
                {'avatar': request.build_absolute_uri(user.avatar.url)},
                status=status.HTTP_200_OK
            )

        if request.method == 'DELETE':
            try:
                user.avatar = None
                user.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Exception:
                return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        url_path='subscribe', methods=['post', 'delete'], detail=True,
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscribe(self, request, *args, **kwargs):
        author = self.get_object()
        user = request.user

        if request.method == 'POST':
            if user == author:
                return Response(
                    {'detail': 'Нельзя подписаться на самого себя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if Subscription.objects.filter(
                    user=user, author=author).exists():
                return Response(
                    {'detail': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subscription = Subscription.objects.create(
                user=user,
                author=author
            )

            serializer = SubscriptionSerializer(
                subscription,
                context={'request': request}
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        subscription = Subscription.objects.filter(user=user, author=author)

        if not subscription.exists():
            return Response(
                {'detail': 'Вы не подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        url_path='subscriptions', methods=['get'], detail=False,
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscriptions(self, request):
        user = request.user
        subscriptions = user.subscriptions.select_related('author').all()
        page = self.paginate_queryset(subscriptions)

        if page is not None:
            serializer = SubscriptionSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionSerializer(
            subscriptions,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)


class TokenObtainView(APIView):
    """Получение JWT токена по коду подтверждения."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Обработка POST-запроса."""
        serializer = TokenObtainSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        token = AccessToken.for_user(user)

        return Response({'token': str(token)})
