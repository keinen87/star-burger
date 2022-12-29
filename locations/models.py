from django.db import models

from locations.services.geocoder import fetch_coordinates


class Location(models.Model):
    address = models.CharField('адрес', max_length=255, unique=True)
    longitude = models.FloatField('долгота')
    latitude = models.FloatField('широта')
    last_request_to_geocoder = models.DateTimeField('дата запроса координат', auto_now_add=True)

    class Meta:
        verbose_name = 'локация'
        verbose_name_plural = 'локации'

    def __str__(self):
        return self.address

    @classmethod
    def create_location_by_address(cls, address):
        coords = fetch_coordinates(address)
        if coords is not None:
            longitude, latitude = coords
            location, created = Location.objects.get_or_create(
                address=address,
                defaults={
                    'longitude': longitude,
                    'latitude': latitude,
                }
            )
            return location
        return None

    @classmethod
    def get_location_or_none(cls, address):
        try:
            location = cls.objects.get(address=address)
        except cls.DoesNotExist:
            location = None
        return location
