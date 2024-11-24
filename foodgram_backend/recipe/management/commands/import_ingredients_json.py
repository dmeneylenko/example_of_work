import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipe.models import Ingredient


class Command(BaseCommand):
    """Импортирование данных об ингредиентах с JSON файла"""
    help = 'Import data from JSON file'

    def handle(self, *args, **kwargs):
        path = os.path.join(settings.BASE_DIR, 'data', 'ingredients.json')
        with open(path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            for item in data:
                your_model_instance = Ingredient(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                )
                your_model_instance.save()
