import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipe.models import Ingredient


class Command(BaseCommand):
    """Импортирование данных об ингредиентах с СSV файла"""

    def get_arguments(self, parser):
        parser.add_argument(
            '--delete-existing',
            action='store_true',
            dest='delete_existing',
            default=False,
        )

    def handle(self, *args, **options):
        with open(os.path.join(settings.BASE_DIR, 'data', 'ingredients.csv'),
                  'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            records = []
            for row in reader:
                records.append(Ingredient(
                    name=row[0],
                    measurement_unit=row[1]))
            Ingredient.objects.bulk_create(records)
            self.stdout.write(self.style.SUCCESS('Данные импортированы'))
            csvfile.close()
