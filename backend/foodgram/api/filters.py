from django.utils.encoding import force_str

from django_filters import FilterSet, CharFilter

from recipes.models import Ingredient


class IngredientFilter(FilterSet):
    name = CharFilter(method='filter_name')

    class Meta:
        model = Ingredient
        fields = ('name',)

    def filter_name(self, queryset, _, value):
        value = force_str(value)
        return queryset.filter(name__icontains=value)
