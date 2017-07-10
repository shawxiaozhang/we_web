# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-03 20:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('we_search', '0002_auto_20170702_0830'),
    ]

    operations = [
        migrations.CreateModel(
            name='Station',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('station_usaf', models.CharField(max_length=10)),
                ('station_wban', models.CharField(max_length=10)),
                ('station_name', models.CharField(max_length=100)),
                ('station_country', models.CharField(max_length=5)),
                ('station_state', models.CharField(max_length=5)),
                ('station_icao', models.CharField(max_length=10)),
                ('station_lat', models.FloatField()),
                ('station_lon', models.FloatField()),
                ('station_elev_m', models.FloatField()),
                ('station_begin', models.IntegerField()),
                ('station_end', models.IntegerField()),
                ('record_freq_h', models.IntegerField()),
                ('record_temperature', models.NullBooleanField()),
                ('record_wind_speed', models.NullBooleanField()),
                ('record_precipitation', models.NullBooleanField()),
                ('record_extreme_report', models.NullBooleanField()),
            ],
        ),
        migrations.AddField(
            model_name='order',
            name='order_completed',
            field=models.NullBooleanField(),
        ),
    ]