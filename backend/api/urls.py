from django.urls import include, path
from rest_framework import routers

from api.views import (
    CustomUserViewSet,
    IngredientsViewSet,
    RecipeViewSet,
    TagViewSet,
)


router = routers.DefaultRouter()
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientsViewSet, basename='ingredient')
router.register('users', CustomUserViewSet, basename='users')


urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
