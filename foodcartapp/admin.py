from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import reverse
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.http import url_has_allowed_host_and_scheme
from django import forms

from .models import Order, OrderItem, Product
from .models import ProductCategory
from .models import Restaurant
from .models import RestaurantMenuItem
from star_burger.settings import ALLOWED_HOSTS


class RestaurantMenuItemInline(admin.TabularInline):
    model = RestaurantMenuItem
    extra = 0


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    search_fields = [
        'name',
        'address',
        'contact_phone',
    ]
    list_display = [
        'name',
        'address',
        'contact_phone',
    ]
    inlines = [
        RestaurantMenuItemInline
    ]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'get_image_list_preview',
        'name',
        'category',
        'price',
    ]
    list_display_links = [
        'name',
    ]
    list_filter = [
        'category',
    ]
    search_fields = [
        # FIXME SQLite can not convert letter case for cyrillic words properly, so search will be buggy.
        # Migration to PostgreSQL is necessary
        'name',
        'category__name',
    ]

    inlines = [
        RestaurantMenuItemInline
    ]
    fieldsets = (
        ('Общее', {
            'fields': [
                'name',
                'category',
                'image',
                'get_image_preview',
                'price',
            ]
        }),
        ('Подробно', {
            'fields': [
                'special_status',
                'description',
            ],
            'classes': [
                'wide'
            ],
        }),
    )

    readonly_fields = [
        'get_image_preview',
    ]

    class Media:
        css = {
            "all": (
                static("admin/foodcartapp.css")
            )
        }

    def get_image_preview(self, obj):
        if not obj.image:
            return 'выберите картинку'
        return format_html('<img src="{url}" style="max-height: 200px;"/>', url=obj.image.url)
    get_image_preview.short_description = 'превью'

    def get_image_list_preview(self, obj):
        if not obj.image or not obj.id:
            return 'нет картинки'
        edit_url = reverse('admin:foodcartapp_product_change', args=(obj.id,))
        return format_html('<a href="{edit_url}"><img src="{src}" style="max-height: 50px;"/></a>', edit_url=edit_url, src=obj.image.url)
    get_image_list_preview.short_description = 'превью'


@admin.register(ProductCategory)
class ProductAdmin(admin.ModelAdmin):
    pass


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    fields = ['product', 'quantity', 'product_price']
    extra = 0


class OrderForm(forms.ModelForm):
    # fields = [
    #     'firstname',
    #     'lastname',
    #     'phonenumber',
    #     'address',
    #     'created_at',
    #     'called_at',
    #     'delivered_at',
    #     'status',
    #     'price',
    #     'payment_type',
    #     'comment',
    #     'restaurant',
    # ]

    class Meta:
        model = Order
        fields = [
            'firstname',
            'lastname',
            'phonenumber',
            'address',
            'called_at',
            'delivered_at',
            'status',
            'payment_type',
            'comment',
            'restaurant',
        ]

    def clean(self):
        if self.cleaned_data['restaurant'] is None and self.cleaned_data['status'] != 'PROCESS':
            raise forms.ValidationError({'restaurant': 'Вы должны выбрать ресторан'})
        return self.cleaned_data


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    form = OrderForm
    readonly_fields = ['price', 'created_at']
    inlines = [OrderItemInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.with_price()

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        restaurant_ids = list(map(lambda rest: rest.id, obj.get_available_restaurants()))
        form.base_fields['restaurant'].queryset = Restaurant.objects.filter(id__in=restaurant_ids)
        return form

    def save_model(self, request, obj, form, change):
        if form.cleaned_data['restaurant'] and form.cleaned_data['status'] == 'PROCESS':
            obj.status = 'COOKING'

        super().save_model(request, obj, form, change)

    def response_change(self, request, obj):
        res = super().response_post_save_change(request, obj)
        if 'next' in request.GET and url_has_allowed_host_and_scheme(request.GET['next'], ALLOWED_HOSTS):
            return HttpResponseRedirect(request.GET['next'])
        else:
            return res
