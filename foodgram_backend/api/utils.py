from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from recipe.models import Ingredient, RecipeIngredient, Tag, TagRecipe


def get_data_for_bulk(model, recipe, objects=None):
    mapping = {
        TagRecipe: lambda tag: {
            'recipe': recipe, 'tag': tag.id},
        RecipeIngredient: lambda ingredient: {
            'recipe': recipe,
            'ingredient': ingredient['ingredient']['id'],
            'amount': ingredient['amount']}
    }
    if model in mapping:
        return [mapping[model](obj) for obj in objects]
    raise ValueError('Нужно указать в objects теги или ингредиенты')


def create_objects_bulk(model, recipe, objects=None):

    data_list = get_data_for_bulk(model, recipe, objects)

    model_to_related_model = {
        TagRecipe: (Tag, 'tag'),
        RecipeIngredient: (Ingredient, 'ingredient')
    }
    if model not in model_to_related_model:
        raise ValueError('Недопустимая модель')
    related_model, related_field = model_to_related_model[model]

    instances = []
    for data in data_list:
        instance = model()
        related_obj = get_object_or_404(related_model, id=data[related_field])
        setattr(instance, related_field, related_obj)
        for key, value in data.items():
            if key != related_field:
                setattr(instance, key, value)
        instances.append(instance)

    model.objects.bulk_create(instances)


def create_model_instance(request, instance, serializer_name):
    """Добавление рецепта из избранного и списка покупок."""
    serializer = serializer_name(
        data={'user': request.user.id, 'recipe': instance.id, },
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


def delete_model_instance(request, model_name, instance, error_message):
    """Удаление рецепта из избранного и списка покупок."""
    if not model_name.objects.filter(user=request.user,
                                     recipe=instance).exists():
        return Response({'errors': error_message},
                        status=status.HTTP_400_BAD_REQUEST)
    model_name.objects.filter(user=request.user, recipe=instance).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


def download_shopping_list(shopping_list):
    response = HttpResponse(shopping_list, content_type='text/plain')
    response['Content-Disposition'] = \
        'attachment; filename="shopping_cart.txt"'
    return response
