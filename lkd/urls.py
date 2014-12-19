# coding=utf-8

from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf import settings
from kurs.forms import SignupFormwithProfile

admin.autodiscover()

urlpatterns = patterns('',
    # application views
    url(r'^kurs/', include('kurs.urls')),

    (r'^accounts/signup/$', 'userena.views.signup', {'signup_form': SignupFormwithProfile}),
    # registration and profile management
    (r'^accounts/', include('userena.urls')),

    # Default admin views
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),

    (r'^i18n/', include('django.conf.urls.i18n')),
)

if settings.DEBUG:
    # static files (images, css, javascript, etc.)
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {
        'document_root': settings.MEDIA_ROOT}))
