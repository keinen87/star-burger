# Generated by Django 3.2.15 on 2022-12-10 17:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0043_alter_orderitem_product_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('PROCESS', 'Обрабатывается'), ('COOKING', 'Готовится'), ('DELIVER', 'В доставке'), ('COMPLETE', 'Выполнен')], db_index=True, default='PROCESS', max_length=10),
        ),
    ]