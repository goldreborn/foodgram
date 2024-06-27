from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework.serializers import SerializerMethodField, ValidationError

from .models import CustomUser, Subscription


class CustomUserSerializer(UserSerializer):
    """
    Сериализатор для модели User.

    Используется для преобразования данных модели User в формат JSON.
    """

    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        model = CustomUser
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'subscribed'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(user=user, author=obj.id).exists()


class SubscriptionSerializer(UserSerializer):
    """
    Сериализатор для вывода подписок пользователя
    """
    recipes = SerializerMethodField(read_only=True)
    recipes_count = SerializerMethodField(read_only=True)

    class Meta:
        model = CustomUser
        fields = ('__all__')

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def validate(self, data):
        request = self.context.get('request')
        if request.user == data['author']:
            raise ValidationError(
                'Нельзя подписаться на самого себя.'
            )
        return data


class UserSignUpSerializer(UserCreateSerializer):
    """
    Сериализатор для создания нового пользователя.

    Используется для преобразования данных модели User в формат JSON.
    """

    class Meta:
        """Мета-класс сериализатора который создает нового пользователя."""
        model = CustomUser
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'password',
        )
