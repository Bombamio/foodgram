from django.apps import apps
from django.db import models
from django.db.models import Exists, OuterRef, Value, BooleanField


class RecipeQuerySet(models.QuerySet):
    """Кастомный QuerySet для модели Recipe."""

    def with_user_annotations(self, user):
        """Добавляет аннотации is_favorited и is_in_shopping_cart."""

        Favorite = apps.get_model('recipes', 'Favorite')
        ShoppingCart = apps.get_model('recipes', 'ShoppingCart')

        if user and user.is_authenticated:
            return self.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user=user,
                        recipe=OuterRef('pk')
                    )
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=user,
                        recipe=OuterRef('pk')
                    )
                )
            )

        return self.annotate(
            is_favorited=Value(False, output_field=BooleanField()),
            is_in_shopping_cart=Value(False, output_field=BooleanField())
        )
