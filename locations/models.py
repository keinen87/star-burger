from django.db import models
from .services import fetch_coordinates


class Location(models.Model):
    address = models.CharField('адрес', max_length=255, unique=True)
    longitude = models.FloatField('долгота', null=True, blank=True)
    latitude = models.FloatField('широта', null=True, blank=True)
    updated_at = models.DateTimeField('дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'локация'
        verbose_name_plural = 'локации'

    def save(self, *args, **kwargs):
        coordinates = fetch_coordinates(self.address)
        if coordinates is None:
            return super().save(*args, **kwargs)

        self.longitude, self.latitude = coordinates
        super().save(*args, **kwargs)
