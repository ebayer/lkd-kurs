from django.conf.urls import patterns, url
from django.views.generic import ListView
from kurs.models import *
from kurs.views import CourseDetailView, ApplicationDeleteView, ApplicationChoicesList, ApplicationList
from django.contrib.auth.decorators import login_required

urlpatterns = patterns('kurs.views',
    url(r'^$', 'index'),
    url(r'^etkinlik/$', ListView.as_view(queryset=Event.objects.order_by('-id'))),
    url(r'^etkinlik/(?P<event_id>\d+)/$', 'list_courses'),
    url(r'^etkinlik/(?P<event_id>\d+)/tercihler/$', login_required(ApplicationChoicesList.as_view())),
    url(r'^etkinlik/(?P<event_id>\d+)/tercihler/edit/$', 'edit_choices'),
    url(r'^kurs/(?P<pk>\d+)/$', CourseDetailView.as_view()),
    url(r'^kurs/(?P<course_id>\d+)/basvur/$', 'apply_for_course'),
    url(r'^basvurular/(?P<pk>\d+)/iptal/$', login_required(ApplicationDeleteView.as_view())),
    url(r'^basvurular/(?P<application_id>\d+)/izin/$', 'upload_permit'),
    url(r'^basvurular/$', login_required(ApplicationList.as_view())),
)
