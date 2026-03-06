import django_filters
from recipes.models import Recipe, Ingredients


class RecipeFilter(django_filters.FilterSet):
    '''Фильтр для рецептов.'''

    tags = django_filters.AllValuesMultipleFilter(
        field_name='tags__slug'
    )
    is_in_shopping_cart = django_filters.BooleanFilter(
        field_name='is_in_shopping_cart_by_user',
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ['author', 'tags']


class IngredientsFilter(django_filters.FilterSet):
    '''Фильтр для ингредиентов.'''

    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredients
        fields = ['name']
