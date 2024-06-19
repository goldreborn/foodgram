import csv
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Загрузка csv файлов."""
    
    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        """Метод загрузки csv файлов."""
        file_path = options['path']

        try:
            with open(file_path, mode="r", encoding="utf-8") as csvfile:
                csv_reader = csv.DictReader(
                    csvfile, fieldnames=['name', 'measurement_unit'], delimiter=','
                )
                csv_data = [row for row in csv_reader]
        except FileNotFoundError:
            raise FileNotFoundError(f'Ошибка: файл {file_path} не найден')
        
        for row in csv_data:
            
            for key, value in row.items():

                Ingredient.objects.create(
                    name=key,
                    measurement_unit=value
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'{len(Ingredient.objects.all())} записей успешно добавлены'
            )
        )
