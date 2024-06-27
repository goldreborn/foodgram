from django.db.transaction import atomic
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from users.models import User, Subscription
from serializers import UserSerializer, SubscriptionSerializer


class UserViewSet(DjoserUserViewSet):
    """
    ViewSet для пользователей.

    Этот класс предоставляет CRUD-операции для пользователей.
    Он использует UserSerializer для сериализации и десериализации юзеров.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)


class SubscriptionViewSet(APIView):
    """
    ViewSet для подписок.

    Этот класс предоставляет CRUD-операции для подписок.
    Он использует SubscriptionSerializer для сериализации
    и десериализации подписок.
    """
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = (IsAuthenticated,)

    @atomic
    @action(
        methods=['post'], detail=True, permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk):
        """
        Подписка на автора.
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

    @atomic
    @action(
        methods=['post'], detail=True, permission_classes=[IsAuthenticated]
    )
    def unsubscribe(self, request, pk):
        """
        Отписка от автора.
        """
        author = User.objects.get(pk=pk)
        subscription = Subscription.objects.filter(
            user=request.user, author=author
        )
        subscription.delete()
        return Response({
            'message': f'Вы отписались от {author}'
        }, status=status.HTTP_204_NO_CONTENT)
