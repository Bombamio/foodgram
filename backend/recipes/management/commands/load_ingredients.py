import csv
from pathlib import Path

from django.core.management.base import BaseCommand

from recipes.models import Ingredients


class Command(BaseCommand):
    help = 'Загружает ингредиенты из CSV-файла в базу данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            default=None,
            help='Путь к CSV-файлу. По умолчанию: data/ingredients.csv'
        )

    def handle(self, *args, **options):
        path = options.get('path')
        if path is None:
            base_dir = Path(__file__).resolve().parent.parent.parent.parent
            path = base_dir / 'data' / 'ingredients.csv'
        else:
            path = Path(path)

        if not path.exists():
            self.stderr.write(
                self.style.ERROR(f'Файл не найден: {path}')
            )
            return

        created_count = 0
        with open(path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) < 2:
                    continue
                name, measurement_unit = row[0].strip(), row[1].strip()
                if not name or not measurement_unit:
                    continue
                _, created = Ingredients.objects.get_or_create(
                    name=name,
                    measurement_unit=measurement_unit
                )
                if created:
                    created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Загружено ингредиентов: {created_count}. '
                f'Всего в БД: {Ingredients.objects.count()}'
            )
        )
