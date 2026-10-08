from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Producto


class CatalogoTests(TestCase):
	def setUp(self):
		self.producto = Producto.objects.create(
			nombre="Taladro de prueba",
			categoria="Herramientas eléctricas",
			precio=39990,
			stock=8,
			imagen="https://example.com/taladro.jpg",
			caracteristicas=["Potencia: 650 W"],
			descuento=15,
			precio_oferta=33992,
		)
		Producto.objects.create(
			nombre="Martillo de prueba",
			categoria="Herramientas manuales",
			precio=7990,
			stock=24,
			imagen="https://example.com/martillo.jpg",
			caracteristicas=["Peso: 16 oz"],
		)

	def test_inicio_lista_productos_desde_la_base_de_datos(self):
		respuesta = self.client.get(reverse("catalogo:lista"))

		self.assertEqual(respuesta.status_code, 200)
		self.assertContains(respuesta, "Taladro de prueba")
		self.assertContains(respuesta, "Martillo de prueba")
		self.assertEqual(respuesta.context["total_productos"], 2)

	def test_pagina_de_ofertas_muestra_productos_con_descuento(self):
		respuesta = self.client.get(reverse("catalogo:ofertas"))

		self.assertEqual(respuesta.status_code, 200)
		self.assertContains(respuesta, "Taladro de prueba")
		self.assertContains(respuesta, "-15%")
		self.assertContains(respuesta, "$33.992")

	def test_filtra_por_categoria_y_ordena_por_precio(self):
		categoria = self.producto.categoria

		respuesta = self.client.get(reverse("catalogo:catalogo"), {"categoria": categoria})
		self.assertEqual(respuesta.status_code, 200)
		self.assertTrue(all(producto.categoria == categoria for producto in respuesta.context["productos"]))

		respuesta = self.client.get(reverse("catalogo:catalogo"), {"orden": "precio_asc"})
		precios = [producto.precio for producto in respuesta.context["productos"]]
		self.assertEqual(precios, sorted(precios))

	def test_contador_aumenta_y_se_descuenta_al_quitar(self):
		self.client.post(reverse("catalogo:agregar_carrito", args=[self.producto.pk]))
		respuesta = self.client.get(reverse("catalogo:lista"))
		self.assertContains(respuesta, 'class="cart-badge">1</span>')

		self.client.get(reverse("catalogo:quitar_carrito", args=[self.producto.pk]))
		respuesta = self.client.get(reverse("catalogo:lista"))
		self.assertNotContains(respuesta, "cart-badge")

	def test_comando_puebla_catalogo_completo_y_es_repetible(self):
		call_command("poblar_productos", stdout=StringIO())
		self.assertEqual(Producto.objects.count(), 40)
		self.assertEqual(Producto.objects.filter(descuento__gt=0).count(), 4)

		call_command("poblar_productos", stdout=StringIO())
		self.assertEqual(Producto.objects.count(), 40)

	def test_producto_se_muestra_en_el_admin_de_django(self):
		call_command("poblar_productos", stdout=StringIO())
		administrador = User.objects.create_superuser(
			username="admin-prueba",
			password="prueba-segura",
			email="admin@example.com",
		)
		self.client.force_login(administrador)

		respuesta = self.client.get("/admin/catalogo/producto/")

		self.assertEqual(respuesta.status_code, 200)
		self.assertContains(respuesta, "Taladro percutor 650W")
