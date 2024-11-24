import re

import django.contrib.auth.password_validation as validators
from django.core import exceptions
from django.db import transaction
from drf_base64.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.serializers import (ModelSerializer,
                                        PrimaryKeyRelatedField,
                                        SerializerMethodField)
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator

from api.utils import create_objects_bulk
from recipe.constants import (MAX_AMOUNT, MAX_COOKING_TIME,
                              MAX_LENGTH_USERNAME, MIN_AMOUNT,
                              MIN_COOKING_TIME)
from recipe.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                           ShoppingCart, Tag, TagRecipe)
from users.models import Subscriptions, User


class UserSerializer(ModelSerializer):
    """Сериализатор модель юзеров."""

    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return (
            user.is_authenticated and user.subscriptions.filter(
                author=obj).exists()
        )


class CreateUserSerializer(ModelSerializer):
    """Сериализатор Создание юзера."""

    username = serializers.CharField(
        max_length=MAX_LENGTH_USERNAME,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name',
                  'last_name', 'password', 'id')

    def validate_username(self, value):
        if not re.match(r'^[\ \w.@+-]+$', value):
            raise serializers.ValidationError(
                'Username должен содержать только буквы, цифры и символы .@+-'
            )
        if value == "me":
            raise serializers.ValidationError(
                {"error": "Вы не можете использовать 'me'!"}
            )
        return value

    def validate(self, data):
        user = User(**data)
        password = data.get('password')
        try:
            validators.validate_password(password=password, user=user)
        except exceptions.ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return super(CreateUserSerializer, self).validate(data)

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class SetPasswordSerializer(serializers.Serializer):
    """Сериализатор Обновление пароля."""

    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class IngredientSerializer(ModelSerializer):
    """Сериализатор Ингредиенты."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = ('id', 'name', 'measurement_unit')


class TagSerializer(ModelSerializer):
    """Сериализатор Тэги."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug', 'color')
        read_only_fields = ('id', 'name', 'slug', 'color')


class RecipeIngredientSerializer(ModelSerializer):
    """Сериализатор Промежуточная модель рецепт - ингредиент."""

    id = serializers.IntegerField(
        source='ingredient.id')
    name = serializers.CharField(
        source='ingredient.name',
        read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True)
    amount = serializers.IntegerField(
        min_value=MIN_AMOUNT,
        max_value=MAX_AMOUNT,
        error_messages={'required': 'Количество вне диапазона'}
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount', 'name', 'measurement_unit')
        read_only_fields = ('name', 'measurement_unit')

    def validate(self, data):
        ingredient_ids = data['ingredient']['id']
        if not Ingredient.objects.filter(id=ingredient_ids).exists():
            raise serializers.ValidationError(
                'Добавьте существующий ингредиент.'
            )
        if data['amount'] in (None, 0):
            raise serializers.ValidationError(
                'Количество ингредиента обязательно для заполнения. '
                'Минимальное значение 1.'
            )
        return data


class RecipeSimpleSerializer(ModelSerializer):
    """Короткий Сериализатор рецепта для отображения."""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image',
                  'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class RecipeGetSerializer(ModelSerializer):
    """Сериализатор Отображение рецепта."""

    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    author = UserSerializer(read_only=True)
    image = Base64ImageField()
    ingredients = RecipeIngredientSerializer(
        source='recipe_set',
        many=True
    )
    tags = TagSerializer(many=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'name', 'image', 'text', 'cooking_time',
                  'is_in_shopping_cart', 'is_favorited')

    def get_is_favorited(self, object):
        user = self.context['request'].user
        return (
            (user is not None and user.is_authenticated) and (
                user.favorites.filter(recipe=object).exists()
            )
        )

    def get_is_in_shopping_cart(self, object):
        user = self.context['request'].user
        return (
            (user is not None and user.is_authenticated) and (
                user.shopping_cart.filter(recipe=object).exists()
            )
        )


class RecipePostSerializer(ModelSerializer):
    """Сериализатор Создание рецепта."""

    author = UserSerializer(read_only=True)
    image = Base64ImageField()
    ingredients = RecipeIngredientSerializer(
        source='recipe_set',
        many=True
    )
    tags = PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        error_messages={
            'required': 'Добавлять можно только уже существующие теги.'
        }
    )
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME,
        max_value=MAX_COOKING_TIME
    )

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'name', 'image', 'text', 'cooking_time')

    def to_representation(self, instance):
        request = self.context.get('request')
        serializer = RecipeGetSerializer(
            instance,
            context={'request': request}
        )
        return serializer.data

    def validate(self, data):
        """Проверка тегов - ингредиентов."""
        tags = data['tags']
        if not tags:
            raise serializers.ValidationError(
                'Нужен хотя бы один тег.'
            )
        tags_ids = [
            tag for tag in data['tags']
        ]
        if len(tags_ids) != len(set(tags_ids)):
            raise serializers.ValidationError(
                'Теги не должны повторяться.'
            )

        ingredients = data['recipe_set']
        if not ingredients:
            raise serializers.ValidationError(
                'Выберите хотя бы 1 ингредиент из списка.'
            )
        ingredient_ids = [
            ingredient['ingredient']['id'] for ingredient in data['recipe_set']
        ]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.'
            )
        return data

    def create(self, validated_data):
        """Создание рецепта."""
        validated_data['author'] = self.context['request'].user
        ingredients = validated_data.pop('recipe_set')
        tags = set(validated_data.pop('tags'))
        recipe = Recipe.objects.create(**validated_data)
        create_objects_bulk(
            TagRecipe, recipe,
            objects=tags)
        create_objects_bulk(
            RecipeIngredient,
            recipe, objects=ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Обновление рецепта."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe_set')
        instance.tags.clear()
        instance.ingredients.clear()
        create_objects_bulk(
            TagRecipe,
            instance,
            objects=tags)
        create_objects_bulk(
            RecipeIngredient,
            instance,
            objects=ingredients)
        return super().update(instance, validated_data)


class LookSubscriptionsSerializer(UserSerializer):
    """Сериализатор отображения подписки."""

    recipes = serializers.SerializerMethodField()
    recipes_count = SerializerMethodField()

    class Meta:
        model = User
        fields = UserSerializer.Meta.fields + (
            'recipes', 'recipes_count'
        )
        read_only_fields = ('email', 'id', 'username',
                            'first_name', 'last_name',)

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = None
        if request:
            recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            if not recipes_limit.isdigit():
                raise serializers.ValidationError(
                    'recipes_limit не может быть преобразовано в int'
                )
            recipes = obj.recipes.all()[:int(recipes_limit)]
        return RecipeSimpleSerializer(recipes, many=True,
                                      context={'request': request}).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubscriptionsSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с подпиской."""

    class Meta:
        model = Subscriptions
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Subscriptions.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны на этого пользователя'
            )
        ]

    def validate(self, data):
        request = self.context.get('request')
        if request.user == data['author']:
            raise serializers.ValidationError(
                'Нельзя подписываться на самого себя!'
            )
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        return LookSubscriptionsSerializer(
            instance.author, context={'request': request}
        ).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с избранным."""

    class Meta:
        model = Favorite
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в избранное'
            )
        ]

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeSimpleSerializer(
            instance.recipe,
            context={'request': request}
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для работы картой покупок."""

    class Meta:
        model = ShoppingCart
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в список покупок'
            )
        ]

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeSimpleSerializer(
            instance.recipe,
            context={'request': request}
        ).data
