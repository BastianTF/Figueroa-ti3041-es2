# Uso de IA y entrega final

## Proyecto
Ferretería del Ranco

## Objetivo
Desarrollar una pequeña aplicación web con Django para mostrar un catálogo de productos, con listado, detalle, resumen de stock y una interfaz visual simple.

## ¿Qué se hizo?
- Se creó la estructura base de la app `catalogo`.
- Se configuró la lógica para cargar productos desde un archivo JSON.
- Se implementó la vista `lista` con resumen de productos totales, con stock y sin stock.
- Se implementó la vista `detalle` para mostrar cada producto individualmente.
- Se generaron los templates base y de listado.
- Se añadieron estilos para mejorar la presentación visual.
- Se configuró el enrutado de la app y la estructura de archivos estáticos.

## Herramientas y asistente
Se utilizó un asistente de IA para apoyar en:
- la sugerencia y corrección de código Python y templates Django,
- hacerle poco de mejoras de estilo por recomendaciones,
- configurar los rol de lo que debe cumplir el administrador y el cliente.

## Consulta 1
Puedes darme una idea de empezar hacer el login con credenciales
- Para incorporar un sistema de inicio de sesión (Login) basado en credenciales en tu proyecto Django, puedes aprovechar el sistema de autenticación nativo que ya viene integrado.
- Crear el Formulario en el Template (catalogo/templates/catalogo/login.html)Django maneja la validación de credenciales automáticamente. Solo necesitas renderizar el formulario nativo utilizando etiquetas HTML estándar y Bootstrap para el diseño.
  
## Consulta 2
Puedes explicarme como separar los roles de cliente y administrador al momento de que cada rol tiene su cuenta ya que la idea es que tengan un tope para cada rol.
- Para separar los roles de Cliente y Administrador aprovechando que estás trabajando con datos estáticos en la vista, la forma más limpia y eficiente en Django es utilizar los atributos nativos del usuario (user.is_staff) o los Grupos de Django, controlando los topes mediante condicionales en el código Python.
  
## Consulta 3
corrigeme el error del inicio de sesion
- falla en el redireccionamiento (que te envíe a una URL por defecto como /accounts/profile/ que no existe) o la falta del token CSRF en el formulario de envío.
 
# Agregar obligatoriamente al final de config/settings.py
LOGIN_REDIRECT_URL = 'redireccionar_home'  # Ruta intermedia de roles
LOGOUT_REDIRECT_URL = 'lista_productos'   # Volver al catálogo al salir

## Cómo ejecutar el proyecto
1. Abrir PowerShell en la raíz del proyecto.
2. Activar el entorno virtual:

```powershell
.\venv\Scripts\Activate.ps1
```
3. Ejecutar el servidor Django:

```powershell
python manage.py runserver
```
4. Abrir la URL que muestre Django en el navegador, normalmente:
   
```text
http://127.0.0.1:8000/
```
## Consideraciones finales
El proyecto cumple con la etapa de catálogo y visualización básica de productos. El siguiente paso opcional sería completar la configuración del proyecto principal de Django para que la app se registre correctamente y se pueda acceder desde la raíz del sitio.