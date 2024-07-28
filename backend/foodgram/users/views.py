import base64
from djoser.views import UserViewSet as DjoserUserViewSet
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet

from .models import User, Subscription
from api.permissions import IsAuthenticatedUser
from api import serializers


class UpdateAvatarView(APIView):
    permission_classes = (IsAuthenticatedUser,)

    def get(self, request):
        user = request.user
        if user.avatar:
            return Response({
                'avatar': user.avatar.url
            }, status=status.HTTP_200_OK)
        return Response({
            'error': 'Аватар не найден'
        }, status=status.HTTP_404_NOT_FOUND)

    def put(self, request):
        user = request.user
        avatar_data = request.data.get('avatar')
        if avatar_data:
            try:
                header, image_data = avatar_data.split(';base64,')
                image_format = header.split('/')[-1]
                data = ContentFile(base64.b64decode(image_data))
                file_name = f'image.{image_format}'
                user.avatar.save(file_name, data, save=True)
                user.save()
                return Response({
                    'avatar': user.avatar.url
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    'error': f'Invalid avatar data {e}'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                'error': 'Avatar field is required.'
            }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        user = request.user
        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(DjoserUserViewSet):

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return serializers.UserSerializer
        return serializers.UserCreateSerializer

    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve']:
            self.permission_classes = [AllowAny]
        else:
            self.permission_classes = [IsAuthenticatedUser]
        return super().get_permissions()

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def get_user_list(self, request):
        users = User.objects.all()
        page = self.paginate_queryset(users)
        if page is not None:
            serializer = serializers.UserSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = serializers.UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def get_profile(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        serializer = serializers.UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
            detail=False, methods=['get'],
            permission_classes=[IsAuthenticatedUser]
        )
    def users_me(self, request):
        user = request.user
        serializer = serializers.UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            user_data = serializers.UserSerializer(
                serializer.instance, context={'request': request}
            ).data
            return Response(
                user_data, status=status.HTTP_201_CREATED, headers=headers
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def register(self, request, *args, **kwargs):
        self.action = 'create'
        return self.create(request, *args, **kwargs)


class UserSubscribeView(APIView):
    """Создание/удаление подписки на пользователя."""
    permission_classes = (IsAuthenticatedUser,)

    def post(self, request, user_id):
        author = get_object_or_404(User, id=user_id)
        subscription, created = Subscription.objects.get_or_create(
            user=request.user, author=author
        )
        if not created:
            return Response({
                'error': 'Already subscribed'
            }, status=status.HTTP_400_BAD_REQUEST)
        serializer = serializers.UserSubscribeSerializer(
            subscription, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, user_id):
        author = get_object_or_404(User, id=user_id)
        subscription = Subscription.objects.filter(
            user=request.user, author=author
        )
        if subscription.exists():
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({
            'errors': 'Not subscribed'
        }, status=status.HTTP_400_BAD_REQUEST)


class UserSubscriptionsListViewSet(ListModelMixin, GenericViewSet):
    """Получение списка всех подписок на пользователей."""
    serializer_class = serializers.UserSubscriptionsListSerializer
    permission_classes = (IsAuthenticatedUser,)

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
