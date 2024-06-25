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
from django.contrib.auth import get_user_model
from django.db.transaction import atomic

from rest_framework.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from djoser.views import UserViewSet as DjoserUserViewSet
from django_filters.rest_framework import DjangoFilterBackend

from recipes.models import Tag, Recipe, Ingredient, Favorites, ShoppingList
from users.models import Subscription

from .permissions import IsAuthenticatedUser, IsOwnerOrReadOnly
from .filters import IngredientFilter
from . import serializers


User = get_user_model()


class TagViewSet(ModelViewSet):
    """
    ViewSet для тегов рецептов.

    Этот класс предоставляет CRUD-операции для тегов рецептов.
    Он использует TagSerializer для сериализации и десериализации тегов.
    """
    queryset = Tag.objects.all()
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
        if self.action in ('list', 'retrieve', 'update', 'partial_update'):
            return serializers.UserSerializer
        elif self.action == 'create':
            return serializers.UserCreateSerializer
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
        return Response(
            serializer.data, status=HTTP_201_CREATED,
            headers=self.get_success_headers(serializer.data)
        )

    def update(self, request, *args, **kwargs):
        """
        Обновление информации о пользователе.

        request: запрос
        pk: идентификатор пользователя
        return: обновленный пользователь
        """
        serializer = self.get_serializer(
            self.get_object(), data=request.data,
            partial=kwargs.pop('partial', False)
        )
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
        self.perform_destroy(self.get_object())
        return Response(status=HTTP_204_NO_CONTENT)


class IngredientViewSet(ReadOnlyModelViewSet):
    """
    ViewSet для ингредиентов.

    Получение информации о ингредиенте.
    """
    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    """
    ViewSet для рецептов.

    Этот класс предоставляет CRUD-операции для рецептов.
    Он использует RecipeSerializer для сериализации и десериализации рецептов.
    """
    queryset = Recipe.objects.all().order_by('-pub_date')
    serializer_class = serializers.RecipeSerializer
    pagination_class = PageNumberPagination
    permission_classes = (IsOwnerOrReadOnly,)

    @atomic
    @action(
        methods=['post'], detail=True, permission_classes=[IsAuthenticatedUser]
    )
    def add_to_favorites(self, request, pk):
        """
        Добавление рецепта в избранное.

        request: запрос
        pk: идентификатор рецепта
        return: информация о добавлении рецепта в избранное
        """
        favorite, created = Favorites.objects.get_or_create(
            user=request.user, recipe=self.get_object()
        )
        serializer = serializers.FavoritesSerializer(favorite)
        if created:
            return Response({
                'message': 'Рецепт добавлен в избранное',
                'data': serializer.data
            })
        else:
            return Response({
                'message': 'Рецепт уже находится в избранном',
                'data': serializer.data
            })

    @atomic
    @action(
        methods=['post'], detail=True, permission_classes=[IsAuthenticatedUser]
    )
    def remove_from_favorites(self, request, pk):
        """
        Удаление рецепта из избранного.

        request: запрос
        pk: идентификатор рецепта
        return: информация об удалении рецепта из избранного
        """
        favorite = Favorites.objects.filter(
            user=request.user, recipe=self.get_object()
        )
        favorite.delete()
        return Response({
            'message': 'Рецепт удален из избранного'
        }, status=HTTP_204_NO_CONTENT)

    @atomic
    @action(
        methods=['post'], detail=True, permission_classes=[IsAuthenticatedUser]
    )
    def add_to_shopping_list(self, request, pk):
        """
        Добавление рецепта в список покупок.

        request: запрос
        pk: идентификатор рецепта
        return: информация о добавлении рецепта в список покупок
        """
        shopping_list, created = ShoppingList.objects.get_or_create(
            user=request.user, recipe=self.get_object()
        )
        serializer = serializers.ShoppingListSerializer(shopping_list)
        if created:
            return Response({
                'message': 'Рецепт добавлен в список покупок',
                'data': serializer.data
            })
        else:
            return Response({
                'message': 'Рецепт уже находится в списке покупок',
                'data': serializer.data
            })

    @atomic
    @action(
        methods=['post'], detail=True, permission_classes=[IsAuthenticatedUser]
    )
    def remove_from_shopping_list(self, request, pk):
        """
        Удаление рецепта из списка покупок.

        request: запрос
        pk: идентификатор рецепта
        return: информация об удалении рецепта из списка покупок
        """
        shopping_list = ShoppingList.objects.filter(
            user=request.user, recipe=self.get_object()
        )
        shopping_list.delete()
        return Response({
            'message': 'Рецепт удален из списка покупок'
        }, status=HTTP_204_NO_CONTENT)

    def create(self, request):
        tags = request.data.get('tags')
        ingredients = request.data.get('ingredients')
        image = request.FILES.get('image')

        recipe = Recipe(
            name=request.data.get('name'),
            author=request.user,
            text=request.data.get('text'),
            cooking_time=request.data.get('cooking_time')
        )
        recipe.save()

        for tag in tags:
            tag_obj, _ = Tag.objects.get_or_create(name=tag)
            recipe.tags.add(tag_obj)

        for ingredient in ingredients:
            ingredient_obj, _ = Ingredient.objects.get_or_create(
                name=ingredient
            )
            recipe.ingredients.add(ingredient_obj)

        if image:
            recipe.image = image
            recipe.save()

        serializer = serializers.RecipeSerializer(recipe)
        return Response(serializer.data)


class FavoritesViewSet(ModelViewSet):
    """
    ViewSet для избранного.

    Этот класс предоставляет CRUD-операции для избранного.
    Он использует FavoritesSerializer для сериализации
    и десериализации избранного.
    """
    queryset = Favorites.objects.all()
    serializer_class = serializers.FavoritesSerializer
    permission_classes = (IsAuthenticatedUser,)


class SubscriptionViewSet(ModelViewSet):
    """
    ViewSet для подписок.

    Этот класс предоставляет CRUD-операции для подписок.
    Он использует SubscriptionSerializer для сериализации
    и десериализации подписок.
    """
    queryset = Subscription.objects.all()
    serializer_class = serializers.SubscriptionSerializer
    permission_classes = (IsAuthenticatedUser,)

    @atomic
    @action(
        methods=['post'], detail=True, permission_classes=[IsAuthenticatedUser]
    )
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
        else:
            return Response({
                'message': f'Вы уже подписаны на {author}'
            })

    @atomic
    @action(
        methods=['post'], detail=True, permission_classes=[IsAuthenticatedUser]
    )
    def unsubscribe(self, request, pk):
        """
        Отписка от автора.

        request: запрос
        pk: идентификатор автора
        return: информация об отписке от автора
        """
        author = User.objects.get(pk=pk)
        subscription = Subscription.objects.filter(
            user=request.user, author=author
        )
        subscription.delete()
        return Response({
            'message': f'Вы отписались от {author}'
        }, status=HTTP_204_NO_CONTENT)


class ShoppingListViewSet(ModelViewSet):
    """
    ViewSet для списка покупок.

    Этот класс предоставляет CRUD-операции для списка покупок.
    Он использует ShoppingListSerializer для сериализации
    и десериализации списка покупок.
    """
    queryset = ShoppingList.objects.all()
    serializer_class = serializers.ShoppingListSerializer
    permission_classes = (IsAuthenticatedUser,)

    @action(methods=['get'], detail=False)
    def download_shopping_list(self, request):
        """
        Скачивание списка покупок.

        request: запрос
        return: файл со списком покупок
        """
        ingredients = {}
        for item in ShoppingList.objects.filter(user=request.user):
            for ingredient in item.recipe.ingredients.all():
                quantity = item.recipe.recipeingredient_set.get(
                    ingredient=ingredient
                ).amount
                if ingredient.name in ingredients:
                    ingredients[ingredient.name] += quantity
                else:
                    ingredients[ingredient.name] = quantity

        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        for ingredient, quantity in ingredients.items():
            response.write(f'{ingredient} - {quantity}\n')
        return response
