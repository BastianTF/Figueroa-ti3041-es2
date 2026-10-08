from django.test import TestCase
from django.urls import reverse

from .views import cargar_productos


class CatalogoTests(TestCase):
	def test_pagina_de_ofertas_muestra_productos_con_descuento(self):
		respuesta = self.client.get(reverse("catalogo:ofertas"))

		self.assertEqual(respuesta.status_code, 200)
		self.assertContains(respuesta, "Taladro percutor 650W")
		self.assertContains(respuesta, "-15%")
		self.assertContains(respuesta, "$33.992")

	def test_filtra_por_categoria_y_ordena_por_precio(self):
		productos = cargar_productos()
		categoria = productos[0]["categoria"]

		respuesta = self.client.get(reverse("catalogo:catalogo"), {"categoria": categoria})
		self.assertEqual(respuesta.status_code, 200)
		self.assertTrue(all(producto["categoria"] == categoria for producto in respuesta.context["productos"]))

		respuesta = self.client.get(reverse("catalogo:catalogo"), {"orden": "precio_asc"})
		precios = [producto["precio"] for producto in respuesta.context["productos"]]
		self.assertEqual(precios, sorted(precios))

	def test_contador_aumenta_y_se_descuenta_al_quitar(self):
		producto = next(producto for producto in cargar_productos() if producto["stock"] > 0)

		self.client.post(reverse("catalogo:agregar_carrito", args=[producto["id"]]))
		respuesta = self.client.get(reverse("catalogo:lista"))
		self.assertContains(respuesta, 'class="cart-badge">1</span>')

		self.client.get(reverse("catalogo:quitar_carrito", args=[producto["id"]]))
		respuesta = self.client.get(reverse("catalogo:lista"))
		self.assertNotContains(respuesta, "cart-badge")
