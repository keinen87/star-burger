from django.db import models
from django.core.validators import MinValueValidator
from django.contrib import admin

from phonenumber_field.modelfields import PhoneNumberField
from geopy import distance

from locations.models import Location


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def with_price(self):
        return self.annotate(
            price=models.Sum(
                models.F('items__product_price') * models.F('items__quantity')
            ),
        )


class Order(models.Model):
    PROCESS_STATUS = 1
    COOKING_STATUS = 2
    DELIVER_STATUS = 3
    COMPLETE_STATUS = 4

    CARD_PAYMENT_TYPE = 'CARD'
    CASH_PAYMENT_TYPE = 'CASH'

    STATUS_CHOICES = [
        (PROCESS_STATUS, 'Обрабатывается'),
        (COOKING_STATUS, 'Готовится'),
        (DELIVER_STATUS, 'В доставке'),
        (COMPLETE_STATUS, 'Выполнен')
    ]
    PAYMENT_TYPES = [
        (CARD_PAYMENT_TYPE, 'Электронно'),
        (CASH_PAYMENT_TYPE, 'Наличностью'),
    ]

    firstname = models.CharField('имя', max_length=100)
    lastname = models.CharField('фамилия', max_length=100)
    phonenumber = PhoneNumberField('номер телефона')
    address = models.CharField('адрес для доставки', max_length=255)
    created_at = models.DateTimeField('время заказа', auto_now_add=True, db_index=True)
    called_at = models.DateTimeField('время звонка', blank=True, null=True, db_index=True)
    delivered_at = models.DateTimeField('время доставки', blank=True, null=True, db_index=True)
    status = models.IntegerField('статус', choices=STATUS_CHOICES, default=PROCESS_STATUS, db_index=True)
    comment = models.TextField('комментарий', blank=True)
    payment_type = models.CharField(
        'способ оплаты',
        max_length=4,
        choices=PAYMENT_TYPES,
        null=True,
        blank=True,
        db_index=True
    )
    processing_restaurant = models.ForeignKey(
        Restaurant,
        verbose_name='обрабатывающий ресторан',
        related_name='orders',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'
        indexes = [
            models.Index(fields=['firstname', 'lastname']),
            models.Index(fields=['phonenumber']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'Заказ {self.id}'

    def get_available_restaurants(self, menu_items=None, uninitialized_product_ids=None):
        if uninitialized_product_ids is None:
            product_ids = list(self.items.values_list('product_id', flat=True))
        else:
            product_ids = uninitialized_product_ids

        if menu_items is None:
            menu_items_by_product_ids = RestaurantMenuItem.objects.filter(
                availability=True,
                product_id__in=product_ids,
            )
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

    @classmethod
    def get_orders_with_available_restaurants(cls):
        orders = Order.objects.with_price().select_related('processing_restaurant').order_by('status')
        menu_items = RestaurantMenuItem.objects.filter(availability=True).select_related('restaurant')

        orders_with_restaurants_and_locations = []
        for order in orders:
            restaurants = order.get_available_restaurants(menu_items=menu_items)
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

    @admin.display(description='Сумма')
    def price(self, obj):
        return obj.price

    @admin.display(description='Рестораны')
    def available_restaurants(self, obj):
        return obj.get_available_restaurants()


class OrderItem(models.Model):
    product = models.ForeignKey(
        Product,
        related_name='order_items',
        verbose_name='продукт',
        on_delete=models.PROTECT
    )
    order = models.ForeignKey(
        Order,
        related_name='items',
        verbose_name='заказ',
        on_delete=models.CASCADE
    )
    product_price = models.DecimalField(
        'Цена товара',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    quantity = models.PositiveSmallIntegerField(
        'количество',
        default=1,
        validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = 'продукт'
        verbose_name_plural = 'продукты'

    def __str__(self):
        return self.product.name
