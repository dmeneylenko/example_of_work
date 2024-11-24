from colorfield.fields import ColorField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from recipe.constants import (MAX_AMOUNT, MAX_COOKING_TIME,
                              MAX_LENGTH_COLORFIELD,
                              MAX_LENGTH_MEASUREMENT_INGREDIENT,
                              MAX_LENGTH_NAME_INGREDIENT,
                              MAX_LENGTH_NAME_RECIPE, MAX_LENGTH_NAME_TAG,
                              MAX_LENGTH_SLUG_TAG, MIN_AMOUNT,
                              MIN_COOKING_TIME)
from users.models import User


class Tag(models.Model):
    """Модель Тегов."""

    name = models.CharField(
        verbose_name='Название тега',
        max_length=MAX_LENGTH_NAME_TAG,
        unique=True,
        help_text='Введите Название тега'
    )

    color = ColorField(default='#FF0000',
                       max_length=MAX_LENGTH_COLORFIELD,
                       verbose_name='Цвет тега',
                       unique=True,
                       help_text='Введите Цвет тега',)

    slug = models.SlugField(
        unique=True,
        verbose_name='Slug тега',
        max_length=MAX_LENGTH_SLUG_TAG,
        help_text='Введите Slug тега'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'slug'],
                name='unique_slug'
            )
        ]
        ordering = ('name',)

    def __str__(self):
        return f'{self.name},{self.color},{self.slug}'


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField(
        max_length=MAX_LENGTH_NAME_INGREDIENT,
        verbose_name='Название ингредиента',
        help_text='Введите название ингредиента'
    )
    measurement_unit = models.CharField(
        max_length=MAX_LENGTH_MEASUREMENT_INGREDIENT,
        verbose_name='Единица измерения',
        help_text='Введите единицу измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент',
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]
        ordering = ('name',)

    def __str__(self):
        return f'Ингредиент {self.name}'


class Recipe(models.Model):
    """Модель Рецептов."""

    author = models.ForeignKey(
        User,
        verbose_name='Автор рецепта',
        on_delete=models.CASCADE,
        related_name='recipes')
    name = models.CharField(
        max_length=MAX_LENGTH_NAME_RECIPE,
        verbose_name='Название рецепта',
        help_text='Введите Название рецепта',
        blank=False
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Фото',
        help_text='Введите Фото',
        blank=False
    )
    text = models.TextField(
        verbose_name='Описание',
        help_text='Добавьте Описание',
        blank=False
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        through_fields=('recipe', 'ingredient', 'amount'),
        related_name='recipes',
        verbose_name='Ингредиенты рецепта'
    )
    tags = models.ManyToManyField(
        Tag,
        through='TagRecipe',
        related_name='recipes',
        verbose_name='Тэги рецепта'
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(MIN_COOKING_TIME),
            MaxValueValidator(MAX_COOKING_TIME)
        ],
        verbose_name='Время приготовления блюда',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата добавления рецепта'
    )

    class Meta:
        verbose_name = 'Рецепт',
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'author'],
                name='unique_name_author'
            )
        ]

    def __str__(self):
        return f'Названиие рецепта: {self.name}, автор: {self.author}'


class RecipeIngredient(models.Model):
    """Промежуточная модель рецепт - ингредиент."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_set',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(MIN_AMOUNT),
            MaxValueValidator(MAX_AMOUNT)
        ]
    )

    class Meta:
        verbose_name = 'Рецепт-Ингредиент',
        verbose_name_plural = 'Рецепты-Ингредиенты'
        unique_together = ('recipe', 'ingredient')
        ordering = ('recipe',)

    def __str__(self):
        return f'{self.recipe}, {self.ingredient}, {self.amount}'


class TagRecipe(models.Model):
    """Промежуточная модель тег - рецепт."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тег'
    )

    class Meta:
        verbose_name = 'Рецепт-Тег',
        verbose_name_plural = 'Рецепты-Теги'
        ordering = ('recipe',)

    def __str__(self):
        return f'{self.recipe} {self.tag}'


class Favorite(models.Model):
    """Модель избранное."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorites'
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='favorites',
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Рецепт в избранном',
        verbose_name_plural = 'Рецепты в избранном'
        ordering = ('recipe',)

    def __str__(self):
        return f'{self.recipe}, {self.user}'


class ShoppingCart(models.Model):
    """Модель корзины покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Юзер'
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='shopping_cart',
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Корзина покупок',
        verbose_name_plural = 'Корзины покупок'
        ordering = ('recipe',)

    def __str__(self):
        return f'{self.recipe}, {self.user}'
