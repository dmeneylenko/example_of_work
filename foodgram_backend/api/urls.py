from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter

from api import views

router = DefaultRouter()
router.register('recipes', views.RecipeViewSet, basename='recipe')
router.register('tags', views.TagViewSet, basename='tag')
router.register('ingredients', views.IngredientViewSet, basename='ingredient')
router.register('users', views.WorkUserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path(
        'docs/',
        TemplateView.as_view(
            template_name='redoc.html',
            extra_context={'schema_url': 'openapi-schema'}),
        name='redoc'
    ),
    path('docs/openapi-schema.yml', views.OpenAPISchemaView.as_view(),
         name='openapi-schema')
]
