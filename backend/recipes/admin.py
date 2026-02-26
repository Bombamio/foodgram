from django.contrib import admin

from .models import Tag, Ingredients, Recipe


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug",)
    list_display_links = ("name",)
    search_fields = ("name", "slug",)


@admin.register(Ingredients)
class IngredientsAdmin(admin.ModelAdmin):
    list_display = ("name", "measurement_unit",)
    list_display_links = ("name",)
    search_fields = ("name",)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        "name", "author", "cooking_time",
    )
    list_display_links = ("name",)
