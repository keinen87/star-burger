from django.db import models
from django.core.validators import MinValueValidator
from django.contrib import admin

from phonenumber_field.modelfields import PhoneNumberField


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
                models.F('products__product_price') * models.F('products__quantity')
            )
        ).prefetch_related('products').select_related('restaurant')


class Order(models.Model):
    objects = OrderQuerySet.as_manager()
    STATUS_CHOICES = [
        ('PROCESS', 'Обрабатывается'),
        ('COOKING', 'Готовится'),
        ('DELIVER', 'В доставке'),
        ('COMPLETE', 'Выполнен')
    ]
    PAYMENT_TYPES = [
        ('CARD', 'Электронно'),
        ('CASH', 'Наличностью'),
    ]

    firstname = models.CharField('имя', max_length=100)
    lastname = models.CharField('фамилия', max_length=100)
    phonenumber = PhoneNumberField('номер телефона')
    address = models.CharField('адрес для доставки', max_length=255)
    created_at = models.DateTimeField('время заказа', auto_now_add=True, db_index=True)
    called_at = models.DateTimeField('время звонка', blank=True, null=True, db_index=True)
    delivered_at = models.DateTimeField('время доставки', blank=True, null=True, db_index=True)
    status = models.CharField('статус', max_length=10, choices=STATUS_CHOICES, default='PROCESS', db_index=True)
    comment = models.TextField('комментарий', blank=True)
    payment_type = models.CharField(
        'способ оплаты',
        max_length=4,
        choices=PAYMENT_TYPES,
        default='CARD',
        db_index=True
    )
    restaurant = models.ForeignKey(
        Restaurant,
        verbose_name='ресторан',
        related_name='orders',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def get_available_restaurants(self):
        product_ids = list(self.products.all().values_list('product_id', flat=True))
        return Order.get_restaurant_ids_by_product_ids(product_ids)

    @classmethod
    def get_restaurant_ids_by_product_ids(cls, product_ids):
        menu_items = RestaurantMenuItem.objects \
            .filter(availability=True, product_id__in=product_ids) \
            .select_related('restaurant')

        restaurant_by_products = []
        for product_id in product_ids:
            restaurants = {
                menu_item.restaurant for menu_item in menu_items if menu_item.product_id == product_id
            }
            restaurant_by_products.append(restaurants)

        return set.intersection(*restaurant_by_products)

    @admin.display(description='Сумма')
    def price(self, obj):
        return obj.price

    @admin.display(description='Рестораны')
    def available_restaurants(self, obj):
        return obj.get_available_restaurants()

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


class OrderItem(models.Model):
    product = models.ForeignKey(
        Product,
        related_name='order_items',
        verbose_name='продукт',
        on_delete=models.SET_NULL,
        null=True
    )
    order = models.ForeignKey(
        Order,
        related_name='products',
        verbose_name='заказ',
        on_delete=models.CASCADE
    )
    product_price = models.DecimalField(
        'Цена товара',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    quantity = models.PositiveSmallIntegerField('количество', default=1)

    def __str__(self):
        return self.product.name

    class Meta:
        verbose_name = 'продукт'
        verbose_name_plural = 'продукты'
