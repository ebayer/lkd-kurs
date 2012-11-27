from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^kurs/', include('kurs.urls')),
    #(r'^accounts/', include('registration.backends.default.urls')),
    #(r'^accounts/', include('registration.backends.simple.urls')),
    (r'^accounts/', include('userena.urls')),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
