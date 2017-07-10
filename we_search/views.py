# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import os
import tempfile
import zipfile
import StringIO

from wsgiref.util import FileWrapper
from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader, RequestContext
from django.urls import reverse
from django.utils.encoding import smart_str
from wefacts import wefacts

import util
from .models import Order
from .forms import OrderForm, StationChoiceForm


def get_order(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = OrderForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            data = form.cleaned_data
            order = Order(customer_ip=_get_client_ip(request),
                          customer_email=data['customer_email'],
                          order_time=datetime.datetime.now(),
                          order_completed=False,
                          weather_address=data['weather_address'],
                          weather_start_date=data['weather_start_date'],
                          weather_end_date=data['weather_end_date'])
            order.save()
            # redirect to a new URL:
            return HttpResponseRedirect(reverse('select_station', kwargs={'order_id': order.id}))
    # if a GET (or any other method) we'll create a blank form
    else:
        form = OrderForm()

    return render(request, 'get_order.html', {'form': form})


def select_station(request, order_id):
    # # process order
    if request.method == 'POST':
        form = StationChoiceForm(request.POST, order_id=order_id)
        if form.is_valid():
            # download raw data for selected stations
            selected_stations = form.cleaned_data.get('selected_stations')
            metadata = form.metadata
            station2location = {}
            for s in selected_stations:
                station2location[s] = metadata['station2location'][s]
            gps = metadata['gps']
            weather_address = metadata['weather_address']
            local_tz = metadata['local_tz']
            date_start_local = metadata['date_start_local']
            date_end_local = metadata['date_end_local']
            wefacts.download_raw_weather(
                station2location.keys(), gps, date_start_local, date_end_local, local_tz, util.DIR_RAW)
            # dump weather results
            station2csv, _ = wefacts.dump_weather_result(
                station2location, gps, weather_address, date_start_local, date_end_local, local_tz,
                dir_raw=util.DIR_RAW, dir_result=util.DIR_RESULT)
            # zip results
            # todo delete csv results and only keep a zip
            zip_file_path = '%s%s.zip' % (util.DIR_RESULT, order_id)
            zipf = zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED)
            path_root = ''
            for f in station2csv.values():
                zipf.write(os.path.join(path_root, f), f)
            zipf.close()
            # todo delete zip file routinely
            # redirect to a new URL:
            return HttpResponseRedirect(reverse('download', kwargs={'order_id': order_id}))
    else:
        form = StationChoiceForm(order_id=order_id)

    return render(request, 'select_station.html', {'form': form, 'order_id': order_id})


def download(request, order_id):
    return _send_zip_file(request, order_id)


def _send_zip_file(request, order_id):
    """
    Send a file through Django without loading the whole file into
    memory at once. The FileWrapper will turn the file object into an
    iterator for chunks of 8KB.
    """
    file_name = '%s.zip' % order_id
    file_path = '%s%s' % (util.DIR_RESULT, file_name)
    wrapper = FileWrapper(file(file_path))
    # response = HttpResponse(wrapper, content_type='text/plain')
    response = HttpResponse(wrapper, content_type='application/force-download')
    response['Content-Disposition'] = 'attachment; filename=%s' % 'wefacts-'+smart_str(file_name)
    response['Content-Length'] = os.path.getsize(file_path)
    return response


def _send_zipfile(request, file_list):
    """
    Create a ZIP file on disk and transmit it in chunks of 8KB,
    without loading the whole file into memory. A similar approach can
    be used for large dynamic PDF files.
    """
    for file_name in file_list:
        print file_name

    path_root = 'test'
    file_names = ['xyz.xyz', 'test1.csv']
    zip_name = 'wefacts-order-%d.zip' % 1

    s = StringIO.StringIO()
    zipf = zipfile.ZipFile(s, 'w', zipfile.ZIP_DEFLATED)
    for f in file_names:
        zipf.write(os.path.join(path_root, f), f)
    zipf.close()

    response = HttpResponse(s.getvalue(), content_type='application/x-zip-compressed')
    response['Content-Disposition'] = 'attachment; filename=%s' % zip_name
    return response


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def _get_station_ids(address):
    return ['000000-99999']


def _get_weather_files(station_ids, weather_start_date, weather_end_date):
    return ['']