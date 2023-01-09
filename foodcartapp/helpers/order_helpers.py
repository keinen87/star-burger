from foodcartapp.helpers.restaurant_helpers import get_available_restaurants
from foodcartapp.models import Order, RestaurantMenuItem
from locations.models import Location

from geopy import distance


def get_orders_with_available_restaurants():
    orders = Order.objects.with_price().select_related('processing_restaurant').order_by('status')
    menu_items = RestaurantMenuItem.objects.filter(availability=True).select_related('restaurant')

    orders_with_restaurants_and_locations = []
    for order in orders:
        restaurants = get_available_restaurants(
            order.items.values_list('product_id', flat=True),
            menu_items=menu_items,
        )
        restaurant_addresses = list(map(lambda rest: rest.address, restaurants))
        locations_by_addresses = Location.objects.in_bulk(
            {order.address, *restaurant_addresses},
            field_name='address',
        )
        delivery_location = locations_by_addresses.get(order.address)

        restaurants_and_distances = []

        for restaurant in restaurants:
            restaurant_location = locations_by_addresses.get(restaurant.address)
            if restaurant_location is None or delivery_location is None:
                distance_between = None
            else:
                distance_between = distance.distance(
                    (restaurant_location.latitude, restaurant_location.longitude),
                    (delivery_location.latitude, delivery_location.longitude),
                ).km
                distance_between = round(distance_between, 1)

            restaurants_and_distances.append([restaurant, distance_between])

        sorted_restaurants_and_distances = sorted(
            restaurants_and_distances,
            key=lambda restaurant_and_distance: (restaurant_and_distance[1] is None, restaurant_and_distance[1]),
        )
        orders_with_restaurants_and_locations.append([order, sorted_restaurants_and_distances])

    return orders_with_restaurants_and_locations
