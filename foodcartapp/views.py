from django.http import JsonResponse
from django.templatetags.static import static
from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from locations.models import Location
from .models import Order, OrderItem, Product
from .serializers import OrderSerializer


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['POST'])
@transaction.atomic
def register_order(request):
    serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    product_ids = list(map(lambda order_item: order_item['product'].id, serializer.validated_data['products']))

    order = Order(
        firstname=serializer.validated_data['firstname'],
        lastname=serializer.validated_data['lastname'],
        phonenumber=serializer.validated_data['phonenumber'],
        address=serializer.validated_data['address'],
    )

    if not order.get_available_restaurants(uninitialized_product_ids=product_ids):
        return Response(
            {'message': 'Не найдены рестораны, способные обработать данный заказ.'},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    Location.create_location_by_address(serializer.validated_data['address'])

    products_fields = serializer.validated_data['products']
    order_items = []
    for product_fields in products_fields:
        product = product_fields['product']
        order_items.append(
            OrderItem(
                product=product,
                order=order,
                quantity=product_fields['quantity'],
                product_price=product.price
            )
        )

    order.save()
    OrderItem.objects.bulk_create(order_items)
    return Response(serializer.data)


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })
