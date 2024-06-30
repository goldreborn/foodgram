import base64
from djoser.views import UserViewSet as DjoserUserViewSet
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from .models import User, Subscription
from api import serializers


class UpdateAvatarView(APIView):
    def get(self, request):
        user = request.user
        if user.avatar:
            return Response({
                'avatar': user.avatar.url
            }, status=status.HTTP_200_OK)
        return Response({
            'error': 'Avatar not found'
        }, status=status.HTTP_404_NOT_FOUND)

    def put(self, request):
        user = request.user
        avatar_data = request.data.get('avatar')
        if avatar_data:
            header, image_data = avatar_data.split(';base64,')
            image_format = header.split('/')[-1]
            data = ContentFile(base64.b64decode(image_data))
            file_name = f'image.{image_format}'
            user.avatar.save(file_name, data, save=True)
            user.save()
            return Response({
                'avatar': user.avatar.url
            }, status=status.HTTP_200_OK)
        return Response({
            'error': 'Avatar data is required'
        }, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer
    permission_classes = (IsAuthenticated,)


class UserSubscribeView(APIView):
    """Создание/удаление подписки на пользователя."""
    def post(self, request, user_id):
        author = get_object_or_404(User, id=user_id)
        serializer = serializers.UserSubscribeSerializer(
            data={'user': request.user.id, 'author': author.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, user_id):
        author = get_object_or_404(User, id=user_id)
        if not Subscription.objects.filter(user=request.user,
                                           author=author).exists():
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Subscription.objects.get(user=request.user.id,
                                 author=user_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class UserSubscriptionsListViewSet(
    ListModelMixin, GenericViewSet
):
    """Получение списка всех подписок на пользователей."""
    serializer_class = serializers.UserSubscribeRepresentSerializer

    def get_queryset(self):
        return User.objects.filter(following__user=self.request.user)
