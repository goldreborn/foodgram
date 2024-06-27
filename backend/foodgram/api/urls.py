from django.urls import path, include

from rest_framework import routers

from api import views
from users.views import SubscriptionViewSet

app_name = 'api'

router_v1 = routers.DefaultRouter()
router_v1.register(
    r'recipes', views.RecipeViewSet, basename='recipes'
)
router_v1.register(r'tags', views.TagViewSet, basename='tags')
router_v1.register(
    r'ingredients', views.IngredientViewSet, basename='ingredients'
)
router_v1.register(r'favorites', views.FavoritesViewSet)
router_v1.register(
    r'shopping_list', views.ShoppingListViewSet
)

urlpatterns = [
    path(
        'users/subscriptions/',
        SubscriptionViewSet.as_view()
    ),
    path('', include(router_v1.urls)),
    path('', include('djoser.urls')),
    path("auth/", include("djoser.urls.authtoken")),
]
