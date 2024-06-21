import csv
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Загрузка csv файлов."""

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        """Метод загрузки csv файлов."""

        try:
            with open(options['path'], mode="r", encoding="utf-8") as csvfile:
                for row in csv.reader(csvfile):
                    name, units = row
                    Ingredient.objects.get_or_create(
                        name=name,
                        measurement_unit=units
                    )
        except FileNotFoundError:
            raise FileNotFoundError(f'Ошибка: файл {csvfile.name} не найден')
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'{len(Ingredient.objects.all())} записей добавлено'
                )
            )
