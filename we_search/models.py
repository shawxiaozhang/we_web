# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class Order(models.Model):
    weather_address = models.CharField(max_length=200)
    weather_start_date = models.DateField()
    weather_end_date = models.DateField()
    order_time = models.DateTimeField()
    order_completed = models.NullBooleanField()
    customer_email = models.EmailField()
    customer_ip = models.GenericIPAddressField()

    def __str__(self):
        return '%s, %s, %s, %s, %s, %s, %s' \
               % (self.weather_address,
                  self.weather_start_date,
                  self.weather_end_date,
                  self.order_time,
                  self.order_completed,
                  self.customer_email,
                  self.customer_ip)


class Station(models.Model):
    station_usaf = models.CharField(max_length=10)
    station_wban = models.CharField(max_length=10)
    station_name = models.CharField(max_length=100)
    station_country = models.CharField(max_length=5)
    station_state = models.CharField(max_length=5)
    station_icao = models.CharField(max_length=10)
    station_lat = models.FloatField()
    station_lon = models.FloatField()
    station_elev_m = models.FloatField()
    station_begin = models.IntegerField()
    station_end = models.IntegerField()
    record_freq_h = models.IntegerField()
    record_temperature = models.NullBooleanField()
    record_wind_speed = models.NullBooleanField()
    record_precipitation = models.NullBooleanField()
    record_extreme_report = models.NullBooleanField()

    def __str__(self):
        return '%s-%s' \
               % (self.station_usaf,
                  self.station_wban)


class Document(models.Model):
    address_file = models.FileField(upload_to='address_file/%Y/%m/%d')