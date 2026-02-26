from django.contrib.auth import get_user_model
from django.db import models
from django.http import HttpResponse

from djoser import views
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from api.permissions import IsAuthorOrReadOnly
from backend.api.pagination import RecipePagination
from recipes.models import Recipe, Tag
from recipes.models import Favorite, ShoppingCart

from .serializers import (
    RecipeWriteSerializer,
    RecipeReadSerializer,
    SubscriptionSerializer,
    TokenObtainSerializer,
    UserSerializer,
    TagSerializer,
    IngredientsSerializer,
)


User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Recipe.objects.all()
    serializer_class = IngredientsSerializer
    permission_classes = (permissions.AllowAny)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)


class RecipeViewSet(viewsets.ModelViewSet):

    queryset = Recipe.objects.all()
    permission_classes = (permissions.AllowAny, IsAuthorOrReadOnly,)
    filter_backends = (
        DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter
    )
    ordering = ('-cooking_time',)
    # Настроить фильтрацию.
    filterset_fields = ('author', 'tags')
    search_fields = ('name',)

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        if user.is_authenticated:
            queryset = queryset.annotate(
                # Проверяем, добавлен ли рецепт в избранное текущим
                # пользователем.
                # Exists проверяет наличие хотя бы одной записи в подзапросе.
                is_favorited=models.Exists(
                    Favorite.objects.filter(
                        user=user,
                        # OuterRef позволяет ссылаться на поля текущей модели
                        # (Recipe) в подзапросе.
                        recipe=models.OuterRef('pk')
                    )
                )
                # Проверяем, добавлен ли рецепт в список покупок текущим
                # пользователем.
            ).annotate(
                is_in_shopping_cart=models.Exists(
                    ShoppingCart.objects.filter(
                        user=user,
                        recipe=models.OuterRef('pk')
                    )
                )
            )
        if self.action in ('list', 'retrieve'):
            return queryset.prefetch_related('tags').select_related('author')
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
        short_link = request.build_absolute_uri(recipe.get_absolute_url())
        return Response(
            {'short_link': short_link}, status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=True,
            permission_classes=[permissions.IsAuthenticated])
    def download_shopping_cart(self, request):
        recipe = self.get_object()
        shopping_cart = recipe.shopping_cart.filter(user=request.user)
        if not shopping_cart.exists():
            return Response(
                {'detail': 'Рецепт не добавлен в список покупок.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        ingredients = recipe.ingredients.all()
        shopping_list = f'Список покупок для рецепта: {recipe.name}\n\n'
        for ingredient in ingredients:
            shopping_list += (
                f'- {ingredient.name} ({ingredient.amount} '
                f'{ingredient.measurement_unit})\n'
            )
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(url_path='favorite', methods=['post', 'delete'], detail=True,
            permission_classes=[permissions.IsAuthenticated])
    def manage_favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'detail': 'Рецепт уже в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=user, recipe=recipe)
            return Response(
                {'detail': 'Рецепт добавлен в избранное.'},
                status=status.HTTP_201_CREATED
            )

        favorite = Favorite.objects.filter(user=user, recipe=recipe)
        if not favorite.exists():
            return Response(
                {'detail': 'Рецепт не найден в избранном.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        favorite.delete()
        return Response(
            {'detail': 'Рецепт удалён из избранного.'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(url_path='shopping_cart', methods=['post', 'delete'], detail=True,
            permission_classes=[permissions.IsAuthenticated])
    def manage_shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'detail': 'Рецепт уже в списке покупок.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            return Response(
                {'detail': 'Рецепт добавлен в список покупок.'},
                status=status.HTTP_201_CREATED
            )

        shopping_cart = ShoppingCart.objects.filter(user=user, recipe=recipe)
        if not shopping_cart.exists():
            return Response(
                {'detail': 'Рецепт не найден в списке покупок.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        shopping_cart.delete()
        return Response(
            {'detail': 'Рецепт удалён из списка покупок.'},
            status=status.HTTP_204_NO_CONTENT
        )


class UserViewSet(views.UserViewSet):

    queryset = User.objects.all()
    permission_classes = (permissions.IsAuthenticatedOrReadOnly)
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
            serializer = UserSerializer(
                user, data=request.data, partial=True
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        url_path='subscribe', methods=['post', 'delete'], detail=True,
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        author = self.get_object()
        user = request.user

        if request.method == 'POST':
            if user == author:
                return Response(
                    {'detail': 'Нельзя подписаться на самого себя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if user.subscriptions.filter(author=author).exists():
                return Response(
                    {'detail': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.subscriptions.create(author=author)
            serializer = SubscriptionSerializer(author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        subscription = user.subscriptions.filter(author=author)
        if not subscription.exists():
            return Response(
                {'detail': 'Вы не подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription.delete()
        return Response(
            {'detail': 'Вы отписались от этого пользователя.'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        url_path='subscriptions', methods=['get'], detail=False,
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscriptions(self, request):
        user = request.user
        subscriptions = user.subscriptions.select_related('author')
        paginaror = RecipePagination()
        page = paginaror.paginate_queryset(
            subscriptions, request, view=self
        )
        serializer = SubscriptionSerializer(
            page, many=True, context={'request': request}
        )
        return paginaror.get_paginated_response(serializer.data)


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
