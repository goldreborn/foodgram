"""
Модуль для работы с рецептами и связанными с ними данными.

В этом модуле определены ViewSet для тегов, пользователей,
рецептов, избранного, подписок и списка покупок.

Он предоставляет функциональность для создания, чтения,
обновления и удаления данных о рецептах,а также для управления
избранными рецептами, подписками на авторов и списками покупок.

Каждый ViewSet предоставляет набор методов для выполнения операций с данными.
"""
from django.http import HttpResponse
from rest_framework.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from djoser.views import UserViewSet as DjoserUserViewSet
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from django.db.transaction import atomic

from .filters import IngredientFilter
from . import serializers
from recipes import models
from users.models import Subscription

User = get_user_model()

PROTEIN_KCAL = 4
FAT_KCAL = 9
CARBOHYDRATE_KCAL = 4

class TagViewSet(ModelViewSet):
    """
    ViewSet для тегов рецептов.

    Этот класс предоставляет CRUD-операции для тегов рецептов.
    Он использует TagSerializer для сериализации и десериализации тегов.
    """
    queryset = models.Tag.objects.all()
    serializer_class = serializers.TagSerializer
    permission_classes = (AllowAny,)


class UserViewSet(DjoserUserViewSet):
    """
    ViewSet для пользователей.

    Этот класс предоставляет CRUD-операции для пользователей.
    Он использует UserSerializer для сериализации и десериализации юзеров.
    """
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer

    def get_serializer_class(self):
        """
        Получение serializer класса в зависимости от действия.

        return: serializer класс
        """
        if self.action == 'list' or self.action == 'retrieve':
            return serializers.UserSerializer
        elif self.action == 'create':
            return serializers.UserCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return serializers.UserSerializer
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        """
        Создание нового пользователя.

        request: запрос
        return: созданный пользователь
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        """
        Обновление информации о пользователе.

        request: запрос
        pk: идентификатор пользователя
        return: обновленный пользователь
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Удаление пользователя.

        request: запрос
        pk: идентификатор пользователя
        return: пустой ответ
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=HTTP_204_NO_CONTENT)


class IngredientViewSet(ReadOnlyModelViewSet):
    """
    ViewSet для ингредиентов.

    Получение информации о ингредиенте.
    """
    queryset = models.Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    permission_classes = (AllowAny, )
    filter_backends = (DjangoFilterBackend, )
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    """
    ViewSet для рецептов.

    Этот класс предоставляет CRUD-операции для рецептов.
    Он использует RecipeSerializer для сериализации и десериализации рецептов.
    """
    queryset = models.Recipe.objects.all().order_by('-pub_date')
    serializer_class = serializers.RecipeSerializer
    pagination_class = PageNumberPagination

    @action(methods=['post'], detail=True)
    @atomic
    def add_to_favorites(self, request, pk):
        """
        Добавление рецепта в избранное.

        request: запрос
        pk: идентификатор рецепта
        return: информация о добавлении рецепта в избранное
        """
        recipe = self.get_object()
        favorite, created = models.Favorites.objects.get_or_create(
            user=request.user, recipe=recipe
        )
        serializer = serializers.FavoritesSerializer(favorite)
        if created:
            return Response({
               'message': 'Рецепт добавлен в избранное',
               'data': serializer.data
            })
        return Response({
           'message': 'Рецепт уже находится в избранном',
           'data': serializer.data
        })

    @action(methods=['post'], detail=True)
    @atomic
    def add_to_shopping_list(self, request, pk):
        """
        Добавление рецепта в список покупок.

        request: запрос
        pk: идентификатор рецепта
        return: информация о добавлении рецепта в список покупок
        """
        recipe = self.get_object()
        shopping_list, created = models.ShoppingList.objects.get_or_create(
            user=request.user, recipe=recipe
        )
        serializer = serializers.ShoppingListSerializer(shopping_list)
        if created:
            return Response({
               'message': 'Рецепт добавлен в список покупок',
               'data': serializer.data
            })
        return Response({
           'message': 'Рецепт уже находится в списке покупок',
           'data': serializer.data
        })


class FavoritesViewSet(ModelViewSet):
    """
    ViewSet для избранного.

    Этот класс предоставляет CRUD-операции для избранного.
    Он использует FavoritesSerializer для сериализации
    и десериализации избранного.
    """
    queryset = models.Favorites.objects.all()
    serializer_class = serializers.FavoritesSerializer


class SubscriptionViewSet(ModelViewSet):
    """
    ViewSet для подписок.

    Этот класс предоставляет CRUD-операции для подписок.
    Он использует SubscriptionSerializer для сериализации
    и десериализации подписок.
    """
    queryset = Subscription.objects.all()
    serializer_class = serializers.SubscriptionSerializer

    @action(methods=['post'], detail=True)
    @atomic
    def subscribe(self, request, pk):
        """
        Подписка на автора.

        request: запрос
        pk: идентификатор автора
        return: информация о подписке на автора
        """
        author = User.objects.get(pk=pk)
        _, created = Subscription.objects.get_or_create(
            user=request.user, author=author
        )
        if created:
            return Response({
               'message': f'Вы подписались на {author}'
            })
        return Response({
           'message': f'Вы уже подписаны на {author}'
        })


class ShoppingListViewSet(ModelViewSet):
    """
    ViewSet для списка покупок.

    Этот класс предоставляет CRUD-операции для списка покупок.
    Он использует ShoppingListSerializer для сериализации
    и десериализации списка покупок.
    """
    queryset = models.ShoppingList.objects.all()
    serializer_class = serializers.ShoppingListSerializer

    @action(methods=['get'], detail=False)
    def download_shopping_list(self, request):
        """
        Скачивание списка покупок.

        request: запрос
        return: файл со списком покупок
        """
        shopping_list = models.ShoppingList.objects.filter(user=request.user)
        ingredients = {}
        for item in shopping_list:
            for ingredient in item.recipe.ingredients.all():
                name = ingredient.name
                quantity = item.recipe.recipeingredient_set.get(ingredient=ingredient).amount
                if name in ingredients:
                    ingredients[name] += quantity
                else:
                    ingredients[name] = quantity

        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="buy_list.txt"'
        for ingredient, quantity in ingredients.items():
            response.write(f'{ingredient} - {quantity}\n')
        return response
