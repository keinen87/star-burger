from rest_framework import serializers
from .models import Order, OrderItem


class ProductsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['quantity', 'product']


class OrderSerializer(serializers.ModelSerializer):
    products = ProductsSerializer(many=True, allow_empty=False, write_only=True)

    class Meta:
        model = Order
        fields = ['firstname', 'lastname', 'phonenumber', 'address', 'products']
