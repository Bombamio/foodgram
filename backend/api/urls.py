from django.urls import include, path
from rest_framework import routers

from api.views import (IngredientsViewSet, RecipeViewSet, TagViewSet,
                       UserViewSet)


router = routers.DefaultRouter()
router.register(r'recipes', RecipeViewSet)
router.register(r'tags', TagViewSet)
router.register(r'ingredients', IngredientsViewSet, basename='ingredient')
router.register(r'users', UserViewSet, basename='users')


urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
