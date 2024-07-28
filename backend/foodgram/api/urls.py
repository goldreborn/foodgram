from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from users import views as user_views

app_name = 'api'

v1_router = DefaultRouter()

v1_router.register(r'tags', views.TagViewSet, basename='tags')
v1_router.register(
    r'ingredients', views.IngredientViewSet, basename='ingredients'
)
v1_router.register(r'recipes', views.RecipeViewSet, basename='recipes')
v1_router.register(r'users', user_views.UserViewSet, basename='users')

urlpatterns = [
    path('users/me/avatar/', user_views.UpdateAvatarView.as_view()),
    path('users/subscriptions/',
         user_views.UserSubscriptionsListViewSet.as_view({'get': 'list'})),
    path(
        'users/<int:user_id>/subscribe/',
        user_views.UserSubscribeView.as_view()
    ),
    path(
        'recipes/<int:pk>/get-link/',
        views.RecipeViewSet.as_view({'get': 'get_link'})
    ),
    path('', include(v1_router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]