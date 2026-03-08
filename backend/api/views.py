from django.contrib.auth import get_user_model
from django.db import models
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser import views
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import IngredientsFilter, RecipeFilter
from .pagination import RecipePagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AvatarSerializer,
    IngredientsSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    ShortRecipeSerializer,
    SubscriptionSerializer,
    TagSerializer,
)
from recipes.models import (
    Favorite,
    Ingredients,
    Recipe,
    RecipeIngredients,
    ShoppingCart,
    Tag,
)
from users.models import Subscription

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
        # Аннатируем подзагрузку флагов избранного и списка покупок.
        Recipe.objects.annotate(is_in_shopping_cart=models.Exists(
            ShoppingCart.objects.filter(
                user=user,
                recipe=models.OuterRef('pk')
            )
        )).annotate(is_favorited=models.Exists(
            Favorite.objects.filter(
                user=user,
                recipe=models.OuterRef('pk')
            )
        ))

        return queryset

    def build_shopping_list(self, ingredients):
        lines = [
            f"{item['ingredients__name']} - {item['total_amount']} "
            f"{item['ingredients__measurement_unit']}"
            for item in ingredients
        ]
        return 'Список покупок:\n\n' + '\n'.join(lines)

    def hendl_favorite_shopping_cart(self, request, model):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            _, created = model.objects.get_or_create(
                user=user,
                recipe=recipe
            )

            if not created:
                return Response(
                    {'errors': 'Рецепт уже добавлен.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = ShortRecipeSerializer(
                recipe,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, _ = model.objects.filter(user=user, recipe=recipe).delete()

        if deleted == 0:
            return Response(
                {'errors': 'Рецепт не найден.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    @action(url_path='get-link', methods=['get'], detail=True)
    def get_short_link(self, request, pk=None):
        recipe = self.get_object()
        return Response(
            {'short-link': request.build_absolute_uri(
                f'/recipes/{recipe.id}/'
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

        response = HttpResponse(
            self.build_shopping_list(ingredients), status=status.HTTP_200_OK,
            content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = \
            'attachment; filename="shopping_list.txt"'
        return response

    @action(url_path='favorite', methods=['post', 'delete'], detail=True,
            permission_classes=[permissions.IsAuthenticated])
    def manage_favorite(self, request, pk=None):
        return self.hendl_favorite_shopping_cart(request, Favorite)

    @action(
        url_path='shopping_cart', methods=['post', 'delete'],
        detail=True, permission_classes=[permissions.IsAuthenticated]
    )
    def manage_shopping_cart(self, request, pk=None):
        return self.hendl_favorite_shopping_cart(request, ShoppingCart)


class CustomUserViewSet(views.UserViewSet):

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
            serializer = AvatarSerializer(
                user,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        user.avatar.delete()
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

            subscription, created = Subscription.objects.get_or_create(
                user=user, author=author
            )

            if not created:
                return Response(
                    {'detail': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = SubscriptionSerializer(
                subscription,
                context={'request': request}
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        delete, _ = Subscription.objects.filter(
            user=user, author=author
        ).delete()

        if delete == 0:
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
