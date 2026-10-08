import json
from pathlib import Path
from datetime import datetime

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .models import Producto

VENTAS_PATH = Path(__file__).resolve().parent / "data" / "ventas.json"

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


def lista(request):
    productos = Producto.objects.order_by("id")
    total_productos = productos.count()
    total_con_stock = productos.filter(stock__gt=0).count()

    contexto = {
        "productos": productos,
        "total_productos": total_productos,
        "total_con_stock": total_con_stock,
        "total_sin_stock": total_productos - total_con_stock,
        "producto_destacado": Producto.objects.filter(
            descuento__gt=0,
            precio_oferta__isnull=False,
        ).order_by("id").first(),
    }
    return render(request, "catalogo/lista.html", contexto)


def ofertas(request):
    productos = Producto.objects.filter(
        descuento__gt=0,
        precio_oferta__isnull=False,
    ).order_by("id")
    return render(request, "catalogo/ofertas.html", {"productos": productos})


def catalogo(request):
    query = (request.GET.get("q") or "").strip()
    categoria = (request.GET.get("categoria") or "").strip()
    orden = request.GET.get("orden") or ""
    precio_minimo = request.GET.get("precio_minimo") or ""
    precio_maximo = request.GET.get("precio_maximo") or ""
    productos = Producto.objects.all()
    categorias = Producto.objects.order_by("categoria").values_list("categoria", flat=True).distinct()

    if query:
        productos = productos.filter(Q(nombre__icontains=query) | Q(categoria__icontains=query))

    if categoria:
        productos = productos.filter(categoria=categoria)

    try:
        if precio_minimo:
            productos = productos.filter(precio__gte=int(precio_minimo))
    except ValueError:
        precio_minimo = ""

    try:
        if precio_maximo:
            productos = productos.filter(precio__lte=int(precio_maximo))
    except ValueError:
        precio_maximo = ""

    ordenes = {
        "precio_asc": "precio",
        "precio_desc": "-precio",
        "nombre": "nombre",
    }
    if orden in ordenes:
        productos = productos.order_by(ordenes[orden])

    total_productos = productos.count()
    total_con_stock = productos.filter(stock__gt=0).count()

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
    producto = get_object_or_404(Producto, pk=producto_id)
    return render(request, "catalogo/detalle.html", {"producto": producto})


def _obtener_carrito(request):
    return {str(producto_id): int(cantidad) for producto_id, cantidad in request.session.get("carrito", {}).items()}


def _guardar_carrito(request, carrito):
    request.session["carrito"] = carrito
    request.session.modified = True


def _datos_carrito(request):
    carrito = _obtener_carrito(request)
    items = []
    total = 0
    productos = Producto.objects.in_bulk(
        int(producto_id) for producto_id in carrito
    )

    for producto_id, cantidad in carrito.items():
        producto = productos.get(int(producto_id))
        if producto is None or cantidad <= 0:
            continue
        subtotal = producto.precio * cantidad
        items.append({"producto": producto, "cantidad": cantidad, "subtotal": subtotal})
        total += subtotal

    return items, total


def agregar_carrito(request, producto_id):
    if request.method != "POST":
        return redirect("catalogo:detalle", producto_id=producto_id)

    if request.user.is_staff:
        messages.error(request, "Los administradores no pueden comprar productos.")
        return redirect("catalogo:detalle", producto_id=producto_id)

    producto = get_object_or_404(Producto, pk=producto_id)

    carrito = _obtener_carrito(request)
    cantidad_actual = carrito.get(str(producto_id), 0)
    if cantidad_actual >= producto.stock:
        messages.error(request, "No puedes agregar más unidades que el stock disponible.")
    else:
        carrito[str(producto_id)] = cantidad_actual + 1
        _guardar_carrito(request, carrito)
        messages.success(request, f"{producto.nombre} se agregó al carrito.")

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

    carrito = _obtener_carrito(request)
    with transaction.atomic():
        productos = Producto.objects.select_for_update().in_bulk(
            int(producto_id) for producto_id in carrito
        )
        for producto_id, cantidad in carrito.items():
            producto = productos.get(int(producto_id))
            if producto is None or cantidad > producto.stock:
                messages.error(request, "Uno de los productos ya no tiene stock suficiente.")
                return redirect("catalogo:carrito")

        for producto_id, cantidad in carrito.items():
            producto = productos[int(producto_id)]
            producto.stock -= cantidad
            producto.save(update_fields=("stock",))

    ventas = cargar_ventas()
    ventas.append({
        "id": len(ventas) + 1,
        "usuario": request.user.username,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total": sum(item["subtotal"] for item in items),
        "productos": [
            {"id": item["producto"].id, "nombre": item["producto"].nombre, "cantidad": item["cantidad"], "subtotal": item["subtotal"]}
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
    productos = Producto.objects.all()
    ventas = cargar_ventas()
    contexto = {
        "productos": productos,
        "ventas": ventas,
        "total_productos": productos.count(),
        "stock_total": sum(producto.stock for producto in productos),
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
            Producto.objects.create(
                nombre=nombre,
                categoria=categoria,
                precio=precio,
                stock=stock,
                imagen=imagen,
                caracteristicas=caracteristicas or [f"Categoría: {categoria}"],
            )
            messages.success(request, "Producto creado correctamente.")
            return redirect("catalogo:admin_productos")

    return render(request, "catalogo/admin_producto_form.html", {"modo": "Crear"})


@user_passes_test(_es_administrador, login_url="catalogo:login")
def admin_producto_editar(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)

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
            producto.nombre = request.POST["nombre"].strip()
            producto.categoria = request.POST["categoria"].strip()
            producto.precio = precio
            producto.stock = stock
            producto.imagen = request.POST.get("imagen", "").strip()
            producto.caracteristicas = [
                line.strip()
                for line in request.POST.get("caracteristicas", "").splitlines()
                if line.strip()
            ]
            producto.save()
            messages.success(request, "Producto actualizado correctamente.")
            return redirect("catalogo:admin_productos")

    return render(request, "catalogo/admin_producto_form.html", {"modo": "Editar", "producto": producto})


@user_passes_test(_es_administrador, login_url="catalogo:login")
def admin_producto_eliminar(request, producto_id):
    if request.method == "POST":
        Producto.objects.filter(pk=producto_id).delete()
        messages.success(request, "Producto eliminado correctamente.")
    return redirect("catalogo:admin_productos")


@user_passes_test(_es_administrador, login_url="catalogo:login")
def admin_productos(request):
    return render(
        request,
        "catalogo/admin_productos.html",
        {"productos": Producto.objects.order_by("id")},
    )