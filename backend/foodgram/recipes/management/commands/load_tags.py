import csv
from django.core.management.base import BaseCommand

from recipes.models import Tag


class Command(BaseCommand):
    """Загрузка csv файлов."""

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        """Метод загрузки csv файлов."""
        path = options['path']
        try:
            with open(path, mode="r", encoding="utf-8") as csvfile:
                for row in csv.reader(csvfile):
                    name, slug = row
                    print(row)
                    Tag.objects.get_or_create(
                        name=name, slug=slug
                    )
        except FileNotFoundError:
            raise FileNotFoundError(f'Ошибка: файл {path} не найден')
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'{len(Tag.objects.all())} записей добавлено'
                )
            )
