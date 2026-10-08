from django import template

register = template.Library()


@register.filter
def precio(valor):
    try:
        return f"{int(valor):,}".replace(",", ".")
    except (TypeError, ValueError):
        return valor
