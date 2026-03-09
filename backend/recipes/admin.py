from django.contrib import admin
from django.db.models import Count

from .models import Favorite, ShoppingCart, Tag, Ingredients, Recipe


class CountMixin:
    count_field = None
    count_relation = None

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if self.count_field and self.count_relation:
            return queryset.annotate(
                **{self.count_field: Count(self.count_relation)}
            )
        return queryset


class RecipeIngredientInline(admin.TabularInline):
    model = Recipe.ingredients.through
    extra = 1
    min_num = 1
    verbose_min = True


@admin.register(Tag)
class TagAdmin(CountMixin, admin.ModelAdmin):
    list_display = ('name', 'slug', 'tag_count')
    list_display_links = ('name',)
    search_fields = ('name', 'slug',)

    count_field = 'tag_count'
    count_relation = 'recipes'

    @admin.display(description='Используется в рецептах')
    def tag_count(self, obj):
        return getattr(obj, self.count_field, 0)


@admin.register(Ingredients)
class IngredientsAdmin(CountMixin, admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'ingredients_count')
    list_display_links = ('name',)
    search_fields = ('name',)

    count_field = 'ingredients_count'
    count_relation = 'ingredients_in_recipe'

    @admin.display(description='Используется в рецептах')
    def ingredients_count(self, obj):
        return getattr(obj, self.count_field, 0)


@admin.register(Recipe)
class RecipeAdmin(CountMixin, admin.ModelAdmin):
    inlines = (RecipeIngredientInline,)
    list_display = (
        'name', 'author', 'favorite_count',
    )
    list_display_links = ('name',)
    search_fields = ('name', 'author__username',)
    filter_horizontal = ('tags',)
    list_filter = ('author__username', 'tags__name',)

    count_field = 'favorite_count'
    count_relation = 'favorite'

    @admin.display(description='В избранном')
    def favorite_count(self, obj):
        return getattr(obj, self.count_field, 0)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_display_links = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_display_links = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
