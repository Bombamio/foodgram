import django_filters
from recipes.models import Recipe


class RecipeFilter(django_filters.FilterSet):
    '''Фильтр для рецептов.'''

    tags = django_filters.CharFilter(
        field_name='tags__slug',
        lookup_expr='in',
        method='filter_tags'
    )
    is_in_shopping_cart = django_filters.BooleanFilter(
        field_name='is_in_shopping_cart_by_user',
        method='filter_is_in_shopping_cart'
    )

    def filter_tags(self, queryset, name, value):
        tags = value.split(',')
        return queryset.filter(tags__slug__in=tags).distinct()

    class Meta:
        model = Recipe
        fields = ['author', 'tags']
