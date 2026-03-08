from django_filters import rest_framework as filters

from recipes.models import Recipe, Ingredients


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов."""

    tags = filters.AllValuesMultipleFilter(
        field_name='tags__slug'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        field_name='is_in_shopping_cart',
        method='filter_is_in_shopping_cart'
    )
    is_favorited = filters.BooleanFilter(
        field_name='is_favorited',
        method='filter_is_favorited'
    )

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_in_shopping_cart', 'is_favorited']

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user

        if user.is_anonymous:
            return queryset

        if value:
            return queryset.filter(is_in_shopping_cart__user=user)
        return queryset.exclude(is_in_shopping_cart__user=user)

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user

        if user.is_anonymous:
            return queryset

        if value:
            return queryset.filter(is_favorited__user=user)
        return queryset.exclude(is_favorited__user=user)


class IngredientsFilter(filters.FilterSet):
    """Фильтр для ингредиентов."""

    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredients
        fields = ['name']
