import csv
from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Tag


class Command(BaseCommand):
    """Загрузка csv файлов."""

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        """Метод загрузки csv файлов."""
        loadeble_models = ('Ingredient', 'Tag', 'Recipe',)
        path = options['path']

        for key in loadeble_models:
            if path.__contains__(key):
                try:
                    with open(path, mode="r", encoding="utf-8") as csvfile:
                        for row in csv.reader(csvfile):
                            model = globals()[key]
                            if not model:
                                raise NotImplementedError(
                                    f'Модели {key} нет в проекте'
                                )
                            else:
                                model.objects.get_or_create(
                                    **{k: k for k in row}
                                )
                except FileNotFoundError:
                    raise FileNotFoundError(f'Ошибка: файл {path} не найден')
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'{len(model.objects.all())} записей добавлено'
                        )
                    )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'{path} не относится к: {loadeble_models}'
                    )
                )
