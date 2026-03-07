from django.contrib import admin

from .models import Tag, Ingredients, Recipe


class RecipeIngredientInline(admin.TabularInline):
    model = Recipe.ingredients.through
    extra = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug',)
    list_display_links = ('name',)
    search_fields = ('name', 'slug',)


@admin.register(Ingredients)
class IngredientsAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    list_display_links = ('name',)
    search_fields = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (RecipeIngredientInline,)
    list_display = (
        'name', 'author', 'favorite_count',
    )
    list_display_links = ('name',)
    search_fields = ('name', 'author__username',)
    filter_horizontal = ('tags',)
    list_filter = ('author__username', 'tags__name',)

    def favorite_count(self, obj):
        return obj.favorite.count()
