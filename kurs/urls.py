from django.conf.urls import patterns, include, url

urlpatterns = patterns('kurs.views',
    url(r'^$', 'index'),
    url(r'^events/$', 'list_events'),
    url(r'^event/(?P<event_id>\d+)/$', 'list_courses'),
    url(r'^kurs/(?P<course_id>\d+)/$', 'course_details'),
)