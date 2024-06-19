import django_filters
from recipes.models import Ingredient

class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Ingredient
        fields = ('name',)