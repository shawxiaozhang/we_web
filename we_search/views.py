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
from .models import Order, Document
from .forms import OrderForm, StationChoiceForm, DocumentForm


def get_order(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST' and 'search' in request.POST:
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
    elif request.method == 'POST' and 'upload_address_list' in request.POST:
        form = DocumentForm()
    elif request.method == 'POST' and 'upload' in request.POST:
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            file_content = request.FILES['address_file'].read()
            doc = Document(address_file=request.FILES['address_file'])
            # TODO schema for address list: store in sql or directory
            doc.save()
            addresses = '; '.join(line for line in file_content.splitlines())
            form = OrderForm(initial={'weather_address': addresses})
        else:
            form = OrderForm()
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

            station2csv = _compose_result_files(selected_stations, metadata)

            zip_file_path = '%s%s.zip' % (util.DIR_RESULT, order_id)
            zipf = zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED)
            path_root = ''
            for f in station2csv.values():
                zipf.write(os.path.join(path_root, f), f)
            zipf.close()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('download', kwargs={'order_id': order_id}))
    else:
        form = StationChoiceForm(order_id=order_id)

    return render(request, 'select_station.html', {'form': form, 'order_id': order_id})


def _compose_result_files(selected_stations, metadata_list):
    if metadata_list is None or len(metadata_list) == 0:
        return {'no_station_found': 'README.txt'}

    station2csv = {}
    for meta in metadata_list:
        if meta is None:    # TODO weather add a note to users
            continue
        station2location = {s: l for s, l in meta['station2location'].items() if s in selected_stations}
        gps = meta['gps']
        weather_address = meta['weather_address']
        local_tz = meta['local_tz']
        start_date_local = meta['start_date_local']
        end_date_local = meta['end_date_local']

        wefacts.download_raw_weather(station2location.keys(), start_date_local, end_date_local,
                                     local_tz, util.DIR_RAW)

        # station2quality = wefacts.check_station_quality(station2location.keys(), start_date_local, end_date_local,
        #                                                 local_tz, util.DIR_RAW)

        s2csv, _ = wefacts.compose_weather_result(
            station2location, gps, weather_address, start_date_local, end_date_local, local_tz,
            dir_raw=util.DIR_RAW, dir_result=util.DIR_RESULT)
        station2csv.update(s2csv)

    return station2csv


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
    # TODO: on mobile: response = HttpResponse(wrapper, content_type='text/plain')
    response = HttpResponse(wrapper, content_type='application/force-download')
    response['Content-Disposition'] = 'attachment; filename=%s' % 'wefacts-'+smart_str(file_name)
    response['Content-Length'] = os.path.getsize(file_path)
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