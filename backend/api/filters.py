from django_filters import rest_framework as filters

from recipes.models import Recipe, Ingredients


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов."""

    tags = filters.AllValuesMultipleFilter(
        field_name='tags__slug'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited'
    )

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_in_shopping_cart', 'is_favorited']

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user

        if user.is_anonymous:
            return queryset.none() if value else queryset

        if value:
            return queryset.filter(shoppingcarts__user=user)
        return queryset.exclude(shoppingcarts__user=user)

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user

        if user.is_anonymous:
            return queryset.none() if value else queryset

        if value:
            return queryset.filter(favorite__user=user)
        return queryset.exclude(favorite__user=user)


class IngredientsFilter(filters.FilterSet):
    """Фильтр для ингредиентов."""

    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredients
        fields = ['name']
