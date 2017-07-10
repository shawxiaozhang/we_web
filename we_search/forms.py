from datetime import date, timedelta
import os

from django import forms
from wefacts import wefacts

import util
from models import Order


class OrderForm(forms.Form):
    weather_address = forms.CharField(label='Address', max_length=100)
    weather_start_date = forms.DateField(label='Start Date',
                                         input_formats=['%Y-%m-%d'],
                                         initial=date.today()-timedelta(days=365))
    weather_end_date = forms.DateField(label='End Date',
                                       input_formats=['%Y-%m-%d'],
                                       initial=date.today()-timedelta(days=358))
    customer_email = forms.EmailField(label='Your Email (optional)', required=False)


class StationChoiceForm(forms.Form):
    def __init__(self, *args, **kwargs):
        order_id = kwargs.pop('order_id')
        order = Order.objects.get(pk=order_id)
        weather_address = order.weather_address
        date_start_local = int(order.weather_start_date.strftime('%Y%m%d'))
        date_end_local = int(order.weather_end_date.strftime('%Y%m%d'))
        station2location, gps, local_tz = wefacts.search_nearby_stations(
            order.weather_address,
            date_start_local,
            date_end_local,
            dir_raw=util.DIR_RAW, dir_local=util.DIR_LOCAL)
        stations = [('%s' % station,
                     '%02d miles away at GPS(%+.2f, %+.2f): %s, %s'
                    % (location['distance'],
                       location['lat'], location['lng'],
                       station,
                       location['name']))
                    for station, location in station2location.items()
                    if not station.startswith('999999-')]
        super(StationChoiceForm, self).__init__(*args, **kwargs)
        self.fields['selected_stations'] = forms.MultipleChoiceField(
            choices=stations,
            widget=forms.CheckboxSelectMultiple(),
            label='Select weather stations',
            required=False
        )
        self.metadata = {
            'gps': gps,
            'local_tz': local_tz,
            'station2location': station2location,
            'date_start_local': date_start_local,
            'date_end_local': date_end_local,
            'weather_address': weather_address
        }
