from django_filters import (
    FilterSet, CharFilter, NumberFilter, BooleanFilter,
    ModelMultipleChoiceFilter
)

from recipes import models


class IngredientFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = models.Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    author = NumberFilter(field_name='author__id')
    tags = ModelMultipleChoiceFilter(
        queryset=models.Tag.objects.all(),
        field_name='tags__slug', to_field_name='slug'
    )
    is_in_shopping_cart = BooleanFilter(method='filter_is_in_shopping_cart')
    is_favorited = BooleanFilter(method='filter_is_favorited')

    class Meta:
        model = models.Recipe
        fields = ['is_in_shopping_cart', 'is_favorited']

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(carts__user=user)
        return queryset.exclude(carts__user=user)

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        return queryset.exclude(favorites__user=user)
