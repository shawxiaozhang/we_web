from datetime import date, timedelta
import os

from django import forms
from wefacts import wefacts

import util
from models import Order


class OrderForm(forms.Form):
    weather_address = forms.CharField(label='Address', max_length=100000, required=False,
                                      widget=forms.TextInput(attrs={'size': 38}))
    weather_start_date = forms.DateField(label='From',
                                         input_formats=['%Y-%m-%d'],
                                         initial=date.today()-timedelta(days=14),
                                         widget=forms.TextInput(attrs={'size': 12}))
    weather_end_date = forms.DateField(label='To',
                                       input_formats=['%Y-%m-%d'],
                                       initial=date.today()-timedelta(days=7),
                                       widget=forms.TextInput(attrs={'size': 12}))
    customer_email = forms.EmailField(label='Your Email (optional)', required=False)


class DocumentForm(forms.Form):
    address_file = forms.FileField(
        label='Upload address list (separated by lines)    ',
        widget=forms.ClearableFileInput(attrs={'size': 40})
    )


class StationChoiceForm(forms.Form):
    def __init__(self, *args, **kwargs):
        order_id = kwargs.pop('order_id')
        order = Order.objects.get(pk=order_id)
        address_list = [a.strip() for a in order.weather_address.split(';')]
        start_date_local = int(order.weather_start_date.strftime('%Y%m%d'))
        end_date_local = int(order.weather_end_date.strftime('%Y%m%d'))

        metadata_list = [_get_nearby_stations_metadata(address, start_date_local, end_date_local)
                         for address in address_list]

        stations, initial_stations = [], []
        for meta, addr in zip(metadata_list, address_list):
            if meta is None:
                stations.append(('no_station_found',
                                 '%s : No stations found. Try another address :) ' % addr))
            else:
                ss = [('%s' % s,
                       '%s : STA %s, at GPS(%+.2f, %+.2f), %02d miles away, %s'
                       % (addr, s, l['lat'], l['lng'], l['distance'], l['name']))
                      for s, l in meta['station2location'].items()]
                stations.extend(ss)
                initial_stations.append(ss[0][0])

        super(StationChoiceForm, self).__init__(*args, **kwargs)
        self.fields['selected_stations'] = forms.MultipleChoiceField(
            choices=stations,
            widget=forms.CheckboxSelectMultiple(),
            label='Select weather stations to download',
            initial=initial_stations,
            required=False
        )
        self.metadata = metadata_list


def _get_nearby_stations_metadata(address, start_date_local, end_date_local):
    result = wefacts.search_nearby_stations(
        address,
        start_date_local,
        end_date_local,
        search_station_num=8,
        search_option='usaf_wban',
        dir_raw=util.DIR_RAW, dir_local=util.DIR_LOCAL)

    if result is not None:
        station2location, gps, local_tz = result[0], result[1], result[2]
        metadata = {
            'gps': gps,
            'local_tz': local_tz,
            'station2location': station2location,
            'start_date_local': start_date_local,
            'end_date_local': end_date_local,
            'weather_address': address
        }
    else:
        metadata = None

    return metadata
