from datetime import datetime

from django.db.models import Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from users.models import Profile, Subscription
from .serializers import (
    ShoppingCartSerializer,
    FavoriteSerializer,
    UserSubscriptionSerializer,
    AvatarSerializer,
    SubscriptionSerializer
)
from recipes.models import (
    Favourite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag
)
from .filters import IngredientFilter, RecipeFilter
from .pagination import PageLimitPagination
from .serializers import (
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    TagSerializer
)
from .permissions import IsAuthorAdminOrReadOnly


class ProfileViewSet(UserViewSet):
    pagination_class = PageLimitPagination

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, **kwargs):
        user = request.user
        author = get_object_or_404(Profile, id=self.kwargs.get('id'))

        serializer = SubscriptionSerializer(
            data={'author': author.id,
                  'user': user.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def del_subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(Profile, id=id)

        deleted_count, _ = Subscription.objects.filter(
            user=user,
            author=author
        ).delete()

        if deleted_count == 0:
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        queryset = Profile.objects.filter(followers__user=request.user)
        serializer = UserSubscriptionSerializer(
            self.paginate_queryset(queryset),
            many=True,
            context={'request': request}
        )

        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=['put'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated]
    )
    def avatar(self, request):
        user = request.user
        serializer = AvatarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.avatar = serializer.validated_data['avatar']
        user.save()
        avatar_url = request.build_absolute_uri(user.avatar.url)
        return Response(
            {'avatar': avatar_url},
            status=status.HTTP_200_OK
        )

    @avatar.mapping.delete
    def delete_avatar(self, request):
        user = request.user
        user.avatar = None
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


def redirect_to_recipe(request, recipe_hash):
    recipe = get_object_or_404(Recipe, short_link_hash=recipe_hash)
    relative_url = '/recipes/' + str(recipe.pk) + '/'
    full_url = request.build_absolute_uri(relative_url)
    return HttpResponseRedirect(full_url)


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    http_method_names = ['get']


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    http_method_names = ['get']


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorAdminOrReadOnly,)
    pagination_class = PageLimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        recipe_hash = recipe.short_link_hash
        short_link = request.build_absolute_uri(
            reverse(
                'short-link-redirect',
                args=[recipe_hash]
            )
        )

        return Response({'short-link': short_link})

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated])
    def favorite(self, request, pk):
        context = {'request': request}
        data = {
            'user': request.user.id,
            'recipe': pk
        }
        try:
            _ = Recipe.objects.get(id=pk)
        except Recipe.DoesNotExist:
            return Response({
                'errors': 'Рецепт не найден'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = FavoriteSerializer(data=data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        deleted_count, _ = Favourite.objects.filter(
            user=request.user,
            recipe=recipe
        ).delete()

        if deleted_count == 0:
            return Response({'errors': 'Рецепт не найден в вашем избранном'},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk):
        context = {'request': request}
        data = {
            'user': request.user.id,
            'recipe': pk
        }

        try:
            _ = Recipe.objects.get(id=pk)
        except Recipe.DoesNotExist:
            return Response({
                'errors': 'Рецепт не найден'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = ShoppingCartSerializer(data=data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        deleted_count, _ = ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe
        ).delete()

        if deleted_count == 0:
            return Response({'errors': 'Рецепт не найден в вашей корзине'},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = request.user
        if not user.shopping_cart.exists():
            return Response(status=HTTP_400_BAD_REQUEST)

        ingredients = IngredientInRecipe.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))

        today = datetime.today()
        shopping_list = (
            f'Список покупок для: {user.get_full_name()}\n\n'
            f'Дата: {today:%Y-%m-%d}\n\n'
        )
        shopping_list += '\n'.join([
            f'- {ingredient["ingredient__name"]} '
            f'({ingredient["ingredient__measurement_unit"]})'
            f' - {ingredient["amount"]}'
            for ingredient in ingredients
        ])
        shopping_list += f'\n\nFoodgram ({today:%Y})'

        filename = f'{user.username}_shopping_list.txt'
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response
