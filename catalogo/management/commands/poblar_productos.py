import json
from pathlib import Path

from django.apps import apps
from django.core.management import BaseCommand, CommandError
from django.core.management.color import no_style
from django.db import connection, transaction

from catalogo.models import Producto


class Command(BaseCommand):
    help = "Carga en la base de datos el catálogo completo de productos en español."

    def handle(self, *args, **options):
        data_path = Path(apps.get_app_config("catalogo").path) / "data" / "productos.json"
        with data_path.open(encoding="utf-8-sig") as data_file:
            data = json.load(data_file)

        if not isinstance(data, list):
            raise CommandError("El archivo de productos debe contener una lista JSON.")

        required_fields = (
            "id",
            "nombre",
            "categoria",
            "precio",
            "stock",
            "imagen",
            "caracteristicas",
            "descuento",
            "precio_oferta",
        )

        with transaction.atomic():
            for index, item in enumerate(data, start=1):
                if not isinstance(item, dict):
                    raise CommandError(f"El producto #{index} no es un objeto JSON.")

                missing_fields = [field for field in required_fields if field not in item]
                if missing_fields:
                    raise CommandError(
                        f"Al producto #{index} le faltan campos: {', '.join(missing_fields)}."
                    )

                Producto.objects.update_or_create(
                    pk=item["id"],
                    defaults={
                        "nombre": item["nombre"],
                        "categoria": item["categoria"],
                        "precio": item["precio"],
                        "stock": item["stock"],
                        "imagen": item["imagen"],
                        "caracteristicas": item["caracteristicas"],
                        "descuento": item["descuento"],
                        "precio_oferta": item["precio_oferta"],
                    },
                )

            with connection.cursor() as cursor:
                for statement in connection.ops.sequence_reset_sql(no_style(), [Producto]):
                    cursor.execute(statement)

        self.stdout.write(
            self.style.SUCCESS(f"Se cargaron {len(data)} productos en la base de datos.")
        )
