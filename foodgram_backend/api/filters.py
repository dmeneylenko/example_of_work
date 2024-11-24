import django_filters
from django_filters.rest_framework import filters

from recipe.models import Ingredient, Recipe, Tag


class RecipeFilter(django_filters.FilterSet):
    is_favorited = filters.BooleanFilter(method='filter_by_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_by_is_in_shopping_cart'
    )
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    id = django_filters.CharFilter(field_name='id')

    def filter_by_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(
                shopping_cart__user=self.request.user
            )
        return queryset

    def filter_by_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(
                favorites__user=self.request.user
            )
        return queryset

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ['name']
