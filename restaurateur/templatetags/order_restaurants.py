from django import template

register = template.Library()


@register.filter
def get_available_restaurants(order): return order.get_available_restaurants()
