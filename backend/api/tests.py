from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from recipes.models import Ingredients, Recipe, Tag

User = get_user_model()


class RecipeAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            email='auth_user@example.com',
            username='auth_user',
            password='auth_user_password',
            first_name='Auth',
            last_name='User'
        )

        self.author = User.objects.create_user(
            email='author@example.com',
            username='author',
            password='author_password',
            first_name='Author',
            last_name='User',
            is_staff=True
        )

        self.tag = Tag.objects.create(name='Test Tag', slug='test-tag')

        self.ingredient = Ingredients.objects.create(
            name='Test Ingredient',
            measurement_unit='g'
        )

        self.recipe = Recipe.objects.create(
            name='Test Recipe',
            author=self.author,
            text='Test recipe description.',
            cooking_time=10
        )

        self.recipe.tags.add(self.tag)
        self.recipe.ingredients.add(
            self.ingredient,
            through_defaults={'amount': 5}
        )

    def test_list_exists(self):
        """Проверка доступности списка задач."""
        response = self.client.get('/api/recipes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
