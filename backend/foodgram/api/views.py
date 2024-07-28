from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum
from rest_framework.response import Response
from rest_framework.viewsets import (
    ModelViewSet, ReadOnlyModelViewSet, GenericViewSet
)
from rest_framework.decorators import action
from rest_framework import mixins, status
from rest_framework.permissions import AllowAny, IsAuthenticated

from pagination import PageLimitPagination
from recipes import models
from .permissions import IsOwnerOrReadOnly
from .filters import IngredientFilter, RecipeFilter
from . import serializers


class TagViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet
):
    """Функция для модели тегов."""
    queryset = models.Tag.objects.all()
    serializer_class = serializers.TagSerializer
    permission_classes = (AllowAny, )
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    """
    ViewSet для ингредиентов.

    Получение информации об ингредиентах.
    """
    queryset = models.Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    queryset = models.Recipe.objects.all()
    permission_classes = (IsOwnerOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = PageLimitPagination
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return serializers.RecipeCreateSerializer
        return serializers.RecipeSerializer

    @action(detail=True, methods=['get'])
    def get_link(self, request, pk=None):
        try:
            origin = request.build_absolute_uri('/api/recipes/')
            recipe = self.get_object()
            serializer = serializers.RecipeSerializer(recipe)
            link = f'{origin}{serializer.data["id"]}/'
            return Response({'short-link': link}, status=status.HTTP_200_OK)
        except models.Recipe.DoesNotExist:
            return Response({
                'error': 'Recipe not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception:
            return Response({
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({
                'detail': 'Authentication credentials were not provided.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        serializer = serializers.RecipeCreateSerializer(
            data=request.data, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = serializers.RecipeCreateSerializer(
            instance, data=request.data, partial=partial,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()

        if request.method == 'POST':
            if not request.user.is_authenticated:
                return Response({
                    'detail': 'Authentication credentials were not provided.'
                }, status=status.HTTP_401_UNAUTHORIZED)

            if models.Favorite.objects.filter(
                user=request.user, recipe=recipe
            ).exists():
                return Response({
                    'detail': 'Recipe is already in favorites.'
                }, status=status.HTTP_400_BAD_REQUEST)

            favorite = models.Favorite.objects.create(
                user=request.user, recipe=recipe
            )
            serializer = serializers.FavoriteSerializer(
                recipe, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            favorite = models.Favorite.objects.filter(
                user=request.user, recipe=recipe
            )
            if favorite.exists():
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({
                'detail': 'Recipe not found in favorites.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        if request.method == 'POST':
            if models.ShoppingCart.objects.filter(
                user=request.user, recipe=recipe
            ).exists():
                return Response({
                    'detail': 'Recipe already in shopping cart.'
                }, status=status.HTTP_400_BAD_REQUEST)
            shopping_cart = models.ShoppingCart.objects.create(
                user=request.user, recipe=recipe
            )
            serializer = serializers.ShoppingCartSerializer(
                shopping_cart, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            shopping_cart = models.ShoppingCart.objects.filter(
                user=request.user, recipe=recipe
            )
            if shopping_cart.exists():
                shopping_cart.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({
                'detail': 'Recipe not found in shopping cart.'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """Отправка файла со списком покупок."""
        ingredients = models.RecipeIngredient.objects.filter(
            recipe__carts__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(ingredient_amount=Sum('amount'))
        shopping_list = ['Список покупок:\n']
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            unit = ingredient['ingredient__measurement_unit']
            amount = ingredient['ingredient_amount']
            shopping_list.append(f'\n{name} - {amount}, {unit}')
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="buy_cart.txt"'
        return response
