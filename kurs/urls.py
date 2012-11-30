from django.conf.urls import patterns, include, url
from django.views.generic import DetailView, ListView
from kurs.models import *
from kurs.views import ApplicationWizard
from kurs.forms import ApplicationAgreement, ApplicationChoice
from django.contrib.auth.decorators import login_required
from django.forms.formsets import formset_factory

urlpatterns = patterns('kurs.views',
    url(r'^$', 'index'),
    url(r'^etkinlik/$', ListView.as_view(queryset=Event.objects.order_by('-id'))),
    url(r'^etkinlik/(?P<event_id>\d+)/$', 'list_courses'),
    url(r'^etkinlik/(?P<event_id>\d+)/tercihler/$', 'edit_choices'),
    url(r'^kurs/(?P<pk>\d+)/$', DetailView.as_view(model=Course)),
    url(r'^kurs/(?P<course_id>\d+)/basvur$', 'apply_for_course'),
)
