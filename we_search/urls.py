from django.conf.urls import url

from . import views

urlpatterns = [
    # ex: /
    url(r'^$', views.get_order, name='home'),
    # ex: /get_order/
    url(r'^get_order/$', views.get_order, name='get_order'),
    # ex: /select_station/1
    url(r'^select_station/$', views.select_station, name='select_station'),
    url(r'^select_station/(?P<order_id>[0-9]+)/$', views.select_station, name='select_station'),
    # ex: /thanks/
    url(r'^download/(?P<order_id>[0-9]+)/$', views.download, name='download'),
]