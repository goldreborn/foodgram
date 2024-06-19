from django.urls import path, include
from rest_framework import routers

from api import views

app_name = 'api'

router_v1 = routers.DefaultRouter()
router_v1.register(r'recipes', views.RecipeViewSet)
router_v1.register(r'tags', views.TagViewSet)
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
        views.SubscriptionViewSet.as_view({'get': 'list'})
    ),
    path('', include(router_v1.urls)),
    path('', include('djoser.urls')),
    path("auth/", include("djoser.urls.authtoken")),
]
