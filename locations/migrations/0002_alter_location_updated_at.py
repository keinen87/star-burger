# Generated by Django 3.2.15 on 2022-12-25 11:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('locations', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='location',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='дата обновления'),
        ),
    ]
