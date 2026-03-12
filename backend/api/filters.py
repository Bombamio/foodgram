from django_filters import rest_framework as filters

from recipes.models import Recipe, Ingredients


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов."""

    tags = filters.AllValuesMultipleFilter(
        field_name='tags__slug'
    )
    is_in_shopping_cart = filters.BooleanFilter()
    is_favorited = filters.BooleanFilter()

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_in_shopping_cart', 'is_favorited']


class IngredientsFilter(filters.FilterSet):
    """Фильтр для ингредиентов."""

    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredients
        fields = ['name']
