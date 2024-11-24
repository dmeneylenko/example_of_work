from django.contrib import admin

from recipe.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                           ShoppingCart, Tag, TagRecipe)


class FavoriteAdmin(admin.ModelAdmin):
    ...


class ShoppingCartAdmin(admin.ModelAdmin):
    ...


class TagAdmin(admin.ModelAdmin):
    ...


class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "measurement_unit"
    )
    list_filter = (
        "name",
    )


class TagRecipeInline(admin.TabularInline):
    model = TagRecipe
    min_num = 1


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    min_num = 1


class RecipeAdmin(admin.ModelAdmin):
    inlines = [
        TagRecipeInline,
        RecipeIngredientInline,
    ]
    list_display = ('id', 'name', 'author', 'text',
                    'cooking_time', 'pub_date', 'image',
                    'display_ingredients')
    list_filter = ('name', 'author', 'tags__name')

    def display_ingredients(self, obj):
        return ", ".join([ingredient.name for ingredient
                          in obj.ingredients.all()])

    @admin.display(description='В избранном')
    def favorite_count(self, recipe):
        return recipe.favorites_recipe.count()


class TagRecipeAdmin(admin.ModelAdmin):
    ...


class RecipeIngredientAdmin(admin.ModelAdmin):
    ...


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(TagRecipe, TagRecipeAdmin)
admin.site.register(RecipeIngredient, RecipeIngredientAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
