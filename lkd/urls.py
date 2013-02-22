from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from django.conf import settings
from kurs.forms import ProfileForm
from registration.forms import RegistrationFormUniqueEmail
from kurs.forms import RegistrationFormUniqueEmailwithProfile

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^kurs/', include('kurs.urls')),
    url(r'^accounts/register/$', 'registration.views.register',
            {'form_class': RegistrationFormUniqueEmailwithProfile,
             'backend': 'registration.backends.default.DefaultBackend'},
             name='registration_register'),
    (r'^accounts/', include('registration.backends.default.urls')),

    ('^profile/edit', 'profiles.views.edit_profile', {'form_class': ProfileForm, 'success_url': '/profile/'}),
    url(r'^profile/$', 'kurs.views.profile_detail', name='profiles_profile_detail'),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    # static files (images, css, javascript, etc.)
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {
        'document_root': settings.MEDIA_ROOT}))
