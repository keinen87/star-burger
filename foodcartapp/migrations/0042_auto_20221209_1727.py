from django.db import migrations


def set_price_to_order_items(apps, schema_editor):
    OrderItem = apps.get_model('foodcartapp', 'OrderItem')
    Product = apps.get_model('foodcartapp', 'Product')
    for product in Product.objects.all().iterator():
        order_items = product.order_items.all()
        for order_item in order_items:
            order_item.product_price = product.price

        OrderItem.objects.bulk_update(order_items, ['product_price'])


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0041_alter_orderitem_product'),
    ]

    operations = [
        migrations.RunPython(set_price_to_order_items)
    ]
