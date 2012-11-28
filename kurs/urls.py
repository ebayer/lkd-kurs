from django.conf.urls import patterns, include, url
from django.views.generic import DetailView, ListView
from kurs.models import *

urlpatterns = patterns('kurs.views',
    url(r'^$', 'index'),
    url(r'^etkinlik/$',
        ListView.as_view(
            queryset=Event.objects.order_by('-id'))),
    url(r'^etkinlik/(?P<event_id>\d+)/$', 'list_courses'),
    url(r'^kurs/(?P<pk>\d+)/$',
        DetailView.as_view(
            model=Course,)),
)
