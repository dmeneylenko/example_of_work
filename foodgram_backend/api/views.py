from django.contrib.auth.hashers import check_password
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.views.generic import TemplateView
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import Pagination
from api.permissions import AuthorOrReadOnly
from api.serializers import (CreateUserSerializer, FavoriteSerializer,
                             IngredientSerializer, LookSubscriptionsSerializer,
                             RecipeGetSerializer, RecipePostSerializer,
                             SetPasswordSerializer, ShoppingCartSerializer,
                             SubscriptionsSerializer, TagSerializer,
                             UserSerializer)
from api.utils import (create_model_instance, delete_model_instance,
                       download_shopping_list)
from recipe.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import User


class WorkUserViewSet(UserViewSet):
    """Вьюсет модели юзеров."""

    queryset = User.objects.all()
    pagination_class = Pagination
    permission_classes = (AuthorOrReadOnly, )

    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserSerializer
        return CreateUserSerializer

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, **kwargs):
        """Работа с подпиской."""
        user = request.user
        author = get_object_or_404(User, id=self.kwargs.get('id'))
        if request.method == 'POST':
            serializer = SubscriptionsSerializer(
                data={'user': request.user.id, 'author': author.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        subscription = user.subscriptions.filter(author=author)
        if subscription.exists():
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False,
            methods=['get'],
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Отображение подписки."""
        user = request.user
        subscribers = User.objects.filter(subscribers__user=user)
        pages = self.paginate_queryset(subscribers)
        serializer = LookSubscriptionsSerializer(
            pages,
            many=True,
            context={'request': request,
                     'limit': request.query_params.get('recipes_limit')})
        return self.get_paginated_response(serializer.data)

    @action(detail=False,
            methods=['post'],
            permission_classes=[IsAuthenticated])
    def set_password(self, request):
        """Обновление пароля."""
        serializer = SetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        current_password = serializer.validated_data.get('current_password')
        new_password = serializer.validated_data.get('new_password')

        user = request.user
        if not check_password(current_password, user.password):
            return Response(
                {'error': 'current_password не верный'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.set_password(new_password)
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Данные авторизованного юзера."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет рецептов."""

    filter_backends = DjangoFilterBackend,
    filterset_class = RecipeFilter
    pagination_class = Pagination
    queryset = Recipe.objects.all()
    http_method_names = ['get', 'post', 'patch', 'create', 'delete']
    permission_classes = (AuthorOrReadOnly, IsAuthenticatedOrReadOnly)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeGetSerializer
        return RecipePostSerializer

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk):
        """Работа с корзиной."""
        if not Recipe.objects.filter(id=pk).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            return create_model_instance(
                request, recipe, ShoppingCartSerializer)

        error_message = 'У вас нет этого рецепта в списке покупок'
        return delete_model_instance(request, ShoppingCart,
                                     recipe, error_message)

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk):
        """Работа с избранным."""
        if not Recipe.objects.filter(id=pk).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            return create_model_instance(
                request, recipe, FavoriteSerializer)

        error_message = 'У вас нет этого рецепта в избранном'
        return delete_model_instance(request, Favorite,
                                     recipe, error_message)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """Выгрузка списка покупок."""
        user = request.user
        user_sc = user.shopping_cart.all()
        if not user_sc.exists():
            return Response(
                'В вашей корзине пока ничего нет',
                status=status.HTTP_400_BAD_REQUEST
            )
        ingredients = Ingredient.objects.filter(
            recipes__shopping_cart__user=user).values(
            'name',
            'measurement_unit'
        ).annotate(amount=Sum('ingredients__amount'))
        shopping_list = ['Список покупок:\n']
        for ingredient in ingredients:
            name = ingredient["name"]
            unit = ingredient["measurement_unit"]
            amount = ingredient["amount"]
            shopping_list.append(f'\n{name} - {amount}, {unit}')
            shopping_list_print = download_shopping_list(shopping_list)
        return shopping_list_print


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет тэгов."""

    permission_classes = AllowAny,
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет ингредиентов."""

    permission_classes = AllowAny,
    filter_backends = DjangoFilterBackend,
    filterset_class = IngredientFilter
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class OpenAPISchemaView(TemplateView):
    template_name = 'openapi-schema.yml'
    content_type = 'text/yaml'

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        response['Content-Disposition'] = (
            'attachment;'
            'filename="openapi-schema.yml"')
        return response
