# Uso de IA — Etapa 3

Se utilizó asistencia de IA para revisar el catálogo existente de la variante y conectar su poblamiento con el ORM de Django. El archivo `catalogo/data/productos.json` contiene los 40 productos en español, incluyendo categorías, precios, stock, imágenes, características y ofertas.

Se añadió el comando `python manage.py poblar_productos` para importar o actualizar ese catálogo en la base de datos. La carga es repetible y los productos quedan disponibles tanto en el catálogo público como en el administrador de Django.