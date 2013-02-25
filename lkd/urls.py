# coding=utf-8

from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf import settings
from kurs.forms import ProfileForm
from kurs.forms import RegistrationFormUniqueEmailwithProfile

admin.autodiscover()

urlpatterns = patterns('',
    # application views
    url(r'^kurs/', include('kurs.urls')),

    # Custom registration view
    # We needed this to use unique email addresses and generate a UserProfile
    # object at the time of account creation
    url(r'^accounts/register/$', 'registration.views.register',
            {'form_class': RegistrationFormUniqueEmailwithProfile,
             'backend': 'registration.backends.default.DefaultBackend'},
             name='registration_register'),
    # Other pre-defined registration views
    (r'^accounts/', include('registration.backends.default.urls')),

    # Custom form is beeing used to edit profile
    ('^profile/edit', 'profiles.views.edit_profile', {'form_class': ProfileForm, 'success_url': '/profile/'}),
    # Other pre-defined profile views
    url(r'^profile/$', 'kurs.views.profile_detail', name='profiles_profile_detail'),

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
