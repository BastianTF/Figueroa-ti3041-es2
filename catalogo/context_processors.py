from .views import cargar_productos


ICONOS_CATEGORIA = {
    "Herramientas manuales": "⚒",
    "Medición": "▥",
    "Herramientas eléctricas": "◫",
    "Fijaciones": "⦿",
    "Pinturas": "◒",
    "Electricidad": "⌁",
    "Gasfitería": "♒",
    "Seguridad": "◇",
}


def categorias_contexto(request):
    categorias = []
    nombres = sorted({producto.get("categoria") for producto in cargar_productos() if producto.get("categoria")})
    for nombre in nombres:
        categorias.append({
            "nombre": nombre,
            "icono": ICONOS_CATEGORIA.get(nombre, "□"),
        })
    return {"categorias_menu": categorias}


def carrito_contexto(request):
    carrito = request.session.get("carrito", {})
    cantidad_carrito = sum(int(cantidad) for cantidad in carrito.values())
    return {"cantidad_carrito": cantidad_carrito}