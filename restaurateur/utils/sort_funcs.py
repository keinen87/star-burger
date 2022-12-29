from itertools import chain

from foodcartapp.models import Order


def sort_orders_by_status(orders):
    orders_by_status = {
        Order.PROCESS_STATUS: [],
        Order.DELIVER_STATUS: [],
        Order.COOKING_STATUS: [],
        Order.COMPLETE_STATUS: [],
    }

    for order in orders:
        orders_by_status[order.status].append(order)

    return chain(*orders_by_status.values())
