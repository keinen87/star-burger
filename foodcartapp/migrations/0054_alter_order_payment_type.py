# Generated by Django 3.2.15 on 2023-01-09 12:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0053_alter_order_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='payment_type',
            field=models.CharField(blank=True, choices=[('CARD', 'Электронно'), ('CASH', 'Наличностью')], db_index=True, max_length=4, null=True, verbose_name='способ оплаты'),
        ),
    ]
