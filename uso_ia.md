# Uso de IA

## Parte 1: Registro de consultas

### 1. Preparación del repositorio

**Prompt:** “Cree el repositorio apellido-ti3041-es2 y la carpeta de trabajo con venv y requirements.txt (Django; mysqlclient solo si corresponde). Puede partir desde cero, copiar el código de su ES1 (sin venv ni historial git) o clonar el repositorio base del docente. Verifique que levanta antes de continuar. Commit etapa-0-entorno. este es mi repositorio https://github.com/BastianTF/Figueroa-ti3041-es2.git”

**Resumen de la respuesta:** Se revisó el proyecto existente, se preparó el entorno virtual, se dejó Django como dependencia y se verificó el inicio del sitio. Se creó el commit `etapa-0-entorno`; no se pudo publicar en GitHub porque faltaban credenciales.

**Qué usé o modifiqué:** Conservé el proyecto existente, su configuración SQLite y sus dependencias necesarias; excluí el entorno virtual de Git. No agregué `mysqlclient` porque no se usa MySQL.

### 2. Inicio del servidor

**Prompt:** “ejecuta el runserver”

**Resumen de la respuesta:** El servidor inicialmente falló al cargar `catalogo/models.py`, porque `CharField` recibió el argumento inválido `max_value`. La IA explicó el error, cambió ese argumento por `max_length` y comprobó una respuesta HTTP 200.

**Qué usé o modifiqué:** Apliqué la corrección en los campos `nombre` y `categoria` del modelo `Producto`.

### 3. Error al crear migraciones

**Prompt:** Se compartió la salida de `python manage.py makemigrations` y `python manage.py migrate`, que terminaba con `TypeError: Field.__init__() got an unexpected keyword argument 'max_value'`, y se preguntó: “por que dio ese error”.

**Resumen de la respuesta:** La IA explicó que el argumento correcto de `CharField` es `max_length` y señaló que el traceback correspondía a una versión del archivo anterior a la corrección.

**Qué usé o modifiqué:** Verifiqué que los campos del modelo quedaran con `max_length`; luego continué con las migraciones.

### 4. Poblamiento y listado desde la base de datos

**Prompt:** “Etapa 3: Poblamiento con IA y listado desde la BD. Poblamiento con IA (obligatorio): solicite a la IA los datos de su variante (volumen completo, datos realistas en español) como fixture JSON de Django o script de poblamiento con el ORM. Cargue los datos (loaddata o ejecutando el script) y verifíquelos en /admin. Reemplace la lista estática de la ES1: el template principal ahora muestra el listado consultando la BD con el ORM. Queda prohibido mantener datos en duro en vistas o templates. Commit etapa-3-bd.”

**Resumen de la respuesta:** Se adaptó el modelo `catalogo.Producto` para almacenar imagen, características y datos de oferta; se creó la migración `0002`; y se implementó el comando `python manage.py poblar_productos`. Las vistas y el template principal se cambiaron para consultar productos con el ORM. Se verificaron 40 productos y 4 ofertas en SQLite, el catálogo del admin y 6 pruebas.

**Prompt de poblamiento y salida realmente utilizada:** La solicitud de poblamiento fue la del prompt anterior. En ese momento `catalogo/data/productos.json` ya existía en el repositorio y contenía 40 objetos en español. La IA no generó esos 40 registros ni una fixture nueva: generó el comando ORM que lee el JSON existente y crea o actualiza registros. El comando cargó los 40 productos; los nombres de la app y el modelo son `catalogo` y `Producto`. Mapeó `id`, `nombre`, `categoria`, `precio`, `stock`, `imagen`, `caracteristicas`, `descuento` y `precio_oferta` a los campos del modelo. El archivo de entrada es una lista JSON, no una fixture JSON de Django. Para repetir la carga se ejecuta `python manage.py poblar_productos`.

**Qué usé o modifiqué:** Integré los campos y la migración, el comando idempotente, el registro del modelo en `/admin` y las consultas ORM del inicio, catálogo, ofertas, detalle, carrito y administración. El JSON se conservó como fuente para la carga inicial; no se mantuvieron productos codificados en las vistas ni en las plantillas.
