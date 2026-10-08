import json
from pathlib import Path

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import redirect, render

DATA_PATH = Path(__file__).resolve().parent / "data" / "productos.json"
VENTAS_PATH = Path(__file__).resolve().parent / "data" / "ventas.json"

DEFAULT_IMAGE = "https://images.unsplash.com/photo-1581092918056-0c4c3acd3789?auto=format&fit=crop&w=900&q=80"
DESCUENTOS_OFERTA = {11: 15, 12: 10, 14: 20, 15: 25}
IMAGEN_POR_CATEGORIA = {
    "Herramientas manuales": "https://images.unsplash.com/photo-1581149480557-3bc8d4e7d7c8?auto=format&fit=crop&w=900&q=80",
    "Medición": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?auto=format&fit=crop&w=900&q=80",
    "Herramientas eléctricas": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=900&q=80",
    "Fijaciones": "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=900&q=80",
    "Pinturas": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=900&q=80",
    "Electricidad": "https://images.unsplash.com/photo-1621905251918-48416bd8575a?auto=format&fit=crop&w=900&q=80",
    "Gasfitería": "https://images.unsplash.com/photo-1621905252507-b8f0f4d7d28f?auto=format&fit=crop&w=900&q=80",
    "Seguridad": "https://images.unsplash.com/photo-1556157382-97eda2d62296?auto=format&fit=crop&w=900&q=80",
}


def _agregar_imagenes(productos):
    for producto in productos:
        categoria = producto.get("categoria", "")
        if categoria == "Medicion":
            producto["categoria"] = "Medición"
        elif "herramientas" in categoria.lower() and any(fragmento in categoria.lower() for fragmento in ("electric", "elã")):
            producto["categoria"] = "Herramientas eléctricas"
        producto.setdefault("imagen", IMAGEN_POR_CATEGORIA.get(producto.get("categoria"), DEFAULT_IMAGE))
        producto.setdefault("caracteristicas", [
            f"Categoría: {producto.get('categoria', 'General')}",
            f"Código de producto: #{producto.get('id')}",
            "Producto nuevo y listo para despacho",
        ])
        descuento = DESCUENTOS_OFERTA.get(producto.get("id"))
        producto["descuento"] = descuento
        producto["precio_oferta"] = round(producto["precio"] * (100 - descuento) / 100) if descuento else None
    return productos


def cargar_productos():
    with open(DATA_PATH, encoding="utf-8-sig") as archivo:
        productos = json.load(archivo)
    return _agregar_imagenes(productos)


def guardar_productos(productos):
    with open(DATA_PATH, "w", encoding="utf-8") as archivo:
        json.dump(productos, archivo, ensure_ascii=False, indent=2)


def cargar_ventas():
    if not VENTAS_PATH.exists():
        return []
    with open(VENTAS_PATH, encoding="utf-8-sig") as archivo:
        return json.load(archivo)


def guardar_ventas(ventas):
    with open(VENTAS_PATH, "w", encoding="utf-8") as archivo:
        json.dump(ventas, archivo, ensure_ascii=False, indent=2)


def _es_administrador(user):
    return user.is_authenticated and user.is_staff


def _siguiente_id(productos):
    return max((producto["id"] for producto in productos), default=0) + 1


def lista(request):
    productos = cargar_productos()
    total_productos = len(productos)
    total_con_stock = sum(1 for p in productos if p["stock"] > 0)

    contexto = {
        "productos": productos,
        "total_productos": total_productos,
        "total_con_stock": total_con_stock,
        "total_sin_stock": total_productos - total_con_stock,
    }
    return render(request, "catalogo/lista.html", contexto)


def ofertas(request):
    productos = [producto for producto in cargar_productos() if producto.get("descuento")]
    return render(request, "catalogo/ofertas.html", {"productos": productos})


def catalogo(request):
    query = (request.GET.get("q") or "").strip().lower()
    categoria = (request.GET.get("categoria") or "").strip()
    orden = request.GET.get("orden") or ""
    precio_minimo = request.GET.get("precio_minimo") or ""
    precio_maximo = request.GET.get("precio_maximo") or ""
    productos = cargar_productos()
    categorias = sorted({producto.get("categoria", "") for producto in productos if producto.get("categoria")})

    if query:
        productos = [
            producto
            for producto in productos
            if query in producto.get("nombre", "").lower() or query in producto.get("categoria", "").lower()
        ]

    if categoria:
        productos = [producto for producto in productos if producto.get("categoria") == categoria]

    try:
        if precio_minimo:
            productos = [producto for producto in productos if producto["precio"] >= int(precio_minimo)]
    except ValueError:
        precio_minimo = ""

    try:
        if precio_maximo:
            productos = [producto for producto in productos if producto["precio"] <= int(precio_maximo)]
    except ValueError:
        precio_maximo = ""

    ordenes = {
        "precio_asc": lambda producto: producto["precio"],
        "precio_desc": lambda producto: producto["precio"],
        "nombre": lambda producto: producto["nombre"].lower(),
    }
    if orden in ordenes:
        productos.sort(key=ordenes[orden], reverse=orden == "precio_desc")

    total_productos = len(productos)
    total_con_stock = sum(1 for p in productos if p["stock"] > 0)

    contexto = {
        "productos": productos,
        "query": query,
        "categoria": categoria,
        "categorias": categorias,
        "orden": orden,
        "precio_minimo": precio_minimo,
        "precio_maximo": precio_maximo,
        "total_productos": total_productos,
        "total_con_stock": total_con_stock,
        "total_sin_stock": total_productos - total_con_stock,
    }
    return render(request, "catalogo/catalogo.html", contexto)


def detalle(request, producto_id):
    productos = cargar_productos()
    producto = next((p for p in productos if p["id"] == producto_id), None)

    if producto is None:
        raise Http404("El producto solicitado no existe.")

    return render(request, "catalogo/detalle.html", {"producto": producto})


def _obtener_carrito(request):
    return {str(producto_id): int(cantidad) for producto_id, cantidad in request.session.get("carrito", {}).items()}


def _guardar_carrito(request, carrito):
    request.session["carrito"] = carrito
    request.session.modified = True


def _datos_carrito(request):
    productos = cargar_productos()
    carrito = _obtener_carrito(request)
    items = []
    total = 0

    for producto_id, cantidad in carrito.items():
        producto = next((p for p in productos if p["id"] == int(producto_id)), None)
        if producto is None or cantidad <= 0:
            continue
        subtotal = producto["precio"] * cantidad
        items.append({"producto": producto, "cantidad": cantidad, "subtotal": subtotal})
        total += subtotal

    return items, total


def agregar_carrito(request, producto_id):
    if request.method != "POST":
        return redirect("catalogo:detalle", producto_id=producto_id)

    if request.user.is_staff:
        messages.error(request, "Los administradores no pueden comprar productos.")
        return redirect("catalogo:detalle", producto_id=producto_id)

    productos = cargar_productos()
    producto = next((p for p in productos if p["id"] == producto_id), None)
    if producto is None:
        raise Http404("El producto solicitado no existe.")

    carrito = _obtener_carrito(request)
    cantidad_actual = carrito.get(str(producto_id), 0)
    if cantidad_actual >= producto["stock"]:
        messages.error(request, "No puedes agregar más unidades que el stock disponible.")
    else:
        carrito[str(producto_id)] = cantidad_actual + 1
        _guardar_carrito(request, carrito)
        messages.success(request, f"{producto['nombre']} se agregó al carrito.")

    return redirect("catalogo:carrito")


def carrito(request):
    items, total = _datos_carrito(request)
    return render(request, "catalogo/carrito.html", {"items": items, "total": total})


def quitar_del_carrito(request, producto_id):
    carrito = _obtener_carrito(request)
    carrito.pop(str(producto_id), None)
    _guardar_carrito(request, carrito)
    return redirect("catalogo:carrito")


@login_required(login_url="catalogo:login")
def confirmar_carrito(request):
    if request.user.is_staff:
        messages.error(request, "Los administradores no pueden comprar productos.")
        return redirect("catalogo:carrito")

    if request.method != "POST":
        return redirect("catalogo:carrito")

    items, _ = _datos_carrito(request)
    if not items:
        messages.error(request, "Tu carrito está vacío.")
        return redirect("catalogo:carrito")

    productos = cargar_productos()
    carrito = _obtener_carrito(request)
    for producto_id, cantidad in carrito.items():
        producto = next((p for p in productos if p["id"] == int(producto_id)), None)
        if producto is None or cantidad > producto["stock"]:
            messages.error(request, "Uno de los productos ya no tiene stock suficiente.")
            return redirect("catalogo:carrito")

    for producto_id, cantidad in carrito.items():
        producto = next(p for p in productos if p["id"] == int(producto_id))
        producto["stock"] -= cantidad

    guardar_productos(productos)
    ventas = cargar_ventas()
    ventas.append({
        "id": len(ventas) + 1,
        "usuario": request.user.username,
        "fecha": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total": sum(item["subtotal"] for item in items),
        "productos": [
            {"id": item["producto"]["id"], "nombre": item["producto"]["nombre"], "cantidad": item["cantidad"], "subtotal": item["subtotal"]}
            for item in items
        ],
    })
    guardar_ventas(ventas)
    _guardar_carrito(request, {})
    messages.success(request, "Compra confirmada correctamente.")
    return redirect("catalogo:lista")


def registro(request):
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        email = (request.POST.get("email") or "").strip()
        password = request.POST.get("password") or ""
        password2 = request.POST.get("password2") or ""

        if not username or not password or not email:
            messages.error(request, "Debes completar todos los campos.")
            return render(request, "catalogo/registro.html")

        if password != password2:
            messages.error(request, "Las contraseñas no coinciden.")
            return render(request, "catalogo/registro.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Ese nombre de usuario ya existe.")
            return render(request, "catalogo/registro.html")

        user = User.objects.create_user(username=username, email=email, password=password)
        messages.success(request, "Cuenta creada correctamente.")
        return redirect("catalogo:login")

    return render(request, "catalogo/registro.html")


def iniciar_sesion(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("catalogo:lista")

        messages.error(request, "Credenciales inválidas.")

    return render(request, "catalogo/login.html")


def cerrar_sesion(request):
    logout(request)
    return redirect("catalogo:lista")


@login_required(login_url="catalogo:login")
def comprar_producto(request, producto_id):
    return agregar_carrito(request, producto_id)


@user_passes_test(_es_administrador, login_url="catalogo:login")
def admin_panel(request):
    productos = cargar_productos()
    ventas = cargar_ventas()
    contexto = {
        "productos": productos,
        "ventas": ventas,
        "total_productos": len(productos),
        "stock_total": sum(producto["stock"] for producto in productos),
        "ventas_total": sum(venta["total"] for venta in ventas),
    }
    return render(request, "catalogo/admin_panel.html", contexto)


@user_passes_test(_es_administrador, login_url="catalogo:login")
def admin_producto_nuevo(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        categoria = request.POST.get("categoria", "").strip()
        imagen = request.POST.get("imagen", "").strip()
        caracteristicas = [line.strip() for line in request.POST.get("caracteristicas", "").splitlines() if line.strip()]
        try:
            precio = int(request.POST.get("precio", "0"))
            stock = int(request.POST.get("stock", "0"))
        except ValueError:
            messages.error(request, "Precio y stock deben ser números enteros.")
            return render(request, "catalogo/admin_producto_form.html", {"modo": "Crear"})

        if not nombre or not categoria or precio < 0 or stock < 0:
            messages.error(request, "Completa los campos y usa valores no negativos.")
        else:
            productos = cargar_productos()
            productos.append({
                "id": _siguiente_id(productos), "nombre": nombre, "categoria": categoria,
                "precio": precio, "stock": stock, "imagen": imagen or DEFAULT_IMAGE,
                "caracteristicas": caracteristicas or [f"Categoría: {categoria}"],
            })
            guardar_productos(productos)
            messages.success(request, "Producto creado correctamente.")
            return redirect("catalogo:admin_productos")

    return render(request, "catalogo/admin_producto_form.html", {"modo": "Crear"})


@user_passes_test(_es_administrador, login_url="catalogo:login")
def admin_producto_editar(request, producto_id):
    productos = cargar_productos()
    producto = next((p for p in productos if p["id"] == producto_id), None)
    if producto is None:
        raise Http404("El producto solicitado no existe.")

    if request.method == "POST":
        try:
            precio = int(request.POST.get("precio", "0"))
            stock = int(request.POST.get("stock", "0"))
        except ValueError:
            messages.error(request, "Precio y stock deben ser números enteros.")
            return render(request, "catalogo/admin_producto_form.html", {"modo": "Editar", "producto": producto})

        if precio < 0 or stock < 0 or not request.POST.get("nombre", "").strip():
            messages.error(request, "El nombre es obligatorio y los valores no pueden ser negativos.")
        else:
            producto.update({
                "nombre": request.POST["nombre"].strip(), "categoria": request.POST["categoria"].strip(),
                "precio": precio, "stock": stock, "imagen": request.POST.get("imagen", "").strip() or DEFAULT_IMAGE,
                "caracteristicas": [line.strip() for line in request.POST.get("caracteristicas", "").splitlines() if line.strip()],
            })
            guardar_productos(productos)
            messages.success(request, "Producto actualizado correctamente.")
            return redirect("catalogo:admin_productos")

    return render(request, "catalogo/admin_producto_form.html", {"modo": "Editar", "producto": producto})


@user_passes_test(_es_administrador, login_url="catalogo:login")
def admin_producto_eliminar(request, producto_id):
    if request.method == "POST":
        productos = cargar_productos()
        productos = [producto for producto in productos if producto["id"] != producto_id]
        guardar_productos(productos)
        messages.success(request, "Producto eliminado correctamente.")
    return redirect("catalogo:admin_productos")


@user_passes_test(_es_administrador, login_url="catalogo:login")
def admin_productos(request):
    return render(request, "catalogo/admin_productos.html", {"productos": cargar_productos()})