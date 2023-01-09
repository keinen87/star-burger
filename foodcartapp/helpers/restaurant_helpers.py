from foodcartapp.models import RestaurantMenuItem


def get_available_restaurants(product_ids, menu_items=None):
    if menu_items is None:
        menu_items_by_product_ids = RestaurantMenuItem.objects.filter(
            availability=True,
            product_id__in=product_ids,
        ).select_related('restaurant', 'product')
    else:
        menu_items_by_product_ids = set(
            filter(
                lambda menu_item: menu_item.product_id in product_ids,
                menu_items
            )
        )

    restaurant_by_products = []
    for product_id in product_ids:
        restaurants = {
            menu_item.restaurant for menu_item in menu_items_by_product_ids if menu_item.product_id == product_id
        }
        restaurant_by_products.append(restaurants)

    return set.intersection(*restaurant_by_products)
