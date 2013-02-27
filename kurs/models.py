# coding=utf-8

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.dispatch import receiver
from registration.signals import user_registered
from django.db.models.signals import pre_delete
from django.utils.timezone import now as tz_aware_now
from django import forms
from django.template.defaultfilters import filesizeformat
import magic

class Event(models.Model):
    class Meta:
        verbose_name = _('event')
        verbose_name_plural = _('events')
    
    display_name = models.CharField(verbose_name=_('display name'), max_length=200)
    allowed_choice_num = models.IntegerField(verbose_name=_('number of allowed user choices for this event'),
                                             default=2)
    venue = models.CharField(verbose_name=_('venue'), max_length=200)
    
    def __unicode__(self):
        return self.display_name

class Course(models.Model):
    class Meta:
        verbose_name = _("course")
        verbose_name_plural = _("courses")
    
    event = models.ForeignKey(Event, verbose_name=_('event'))
    display_name = models.CharField(verbose_name=_('display name'), max_length=200)
    description = models.TextField(verbose_name=_('description'))
    is_open = models.BooleanField(verbose_name=_('is applicable'))
    change_allowed_date = models.DateTimeField(verbose_name=_('deadline for user application'))
    agreement = models.TextField(verbose_name=_('prerequisites'))
    start_date = models.DateField(verbose_name=_('start date'))
    end_date = models.DateField(verbose_name=_('end date'))

    # We define this logic here in order to use it in user
    # course detail page, we filter messages and links according
    # to this property
    @property
    def can_be_applied(self):
        # We have to use timezone-aware date-time objects because we
        # set USE_TZ=True in settings.py
        if self.is_open and self.change_allowed_date >= tz_aware_now():
            return True
        return False

    def __unicode__(self):
        return "%s (%s)" % (self.display_name, self.event.display_name)

class Application(models.Model):
    class Meta:
        verbose_name = _("application")
        verbose_name_plural = _("applications")
        unique_together = (("person", "course"),)

    person = models.ForeignKey(User, related_name='application_users', verbose_name=_('user'))
    course = models.ForeignKey(Course, verbose_name=_('course'))
    application_date = models.DateTimeField(verbose_name=_('date of application'))
    approved = models.BooleanField(default=False, verbose_name=_('approved'))
    approved_by = models.ForeignKey(User, related_name='application_approver',
                                    blank=True, null=True, verbose_name=_('approver'))
    approve_date = models.DateTimeField(blank=True, null=True, verbose_name=_('date of approval'))

    def __unicode__(self):
        return "%s -> %s" % (self.person.username, self.course)

# Delete all application choices for the event
# whenever an application gets deleted
@receiver(pre_delete, sender=Application, dispatch_uid="unique_identifier")
def delete_application_choices(sender, **kwargs):
    instance = kwargs['instance']
    ApplicationChoices.objects.filter(person = instance.person,
                                      event = instance.course.event).delete()

# Validate the permit file accoring to mime-type
# got from
# https://github.com/kaleidos/django-validated-file/blob/master/validatedfile/__init__.py
class ValidatedFileField(models.FileField):
    """
    Same as FileField, but you can specify:
        * content_types - list containing allowed content_types.
        Example: ['application/pdf', 'image/jpeg']
        * max_upload_size - a number indicating the maximum file
        size allowed for upload.
            2.5MB - 2621440
            5MB - 5242880
            10MB - 10485760
            20MB - 20971520
            50MB - 5242880
            100MB 104857600
            250MB - 214958080
            500MB - 429916160
    """
    def __init__(self, *args, **kwargs):
        self.content_types = kwargs.pop("content_types", [])
        self.max_upload_size = kwargs.pop("max_upload_size", 0)
        super(ValidatedFileField, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        data = super(ValidatedFileField, self).clean(*args, **kwargs)
        file = data.file

        if self.content_types:
            content_type_headers = getattr(file, 'content_type', '')

            mg = magic.Magic(mime = True)
            content_type_magic = mg.from_buffer(file.read(1024))
            file.seek(0)

            if not content_type_headers in self.content_types or not content_type_magic in self.content_types:
                raise forms.ValidationError(_('Files of type %(type)s are not supported.') % {'type': content_type_magic})

        if self.max_upload_size:
            if file._size > self.max_upload_size:
                raise forms.ValidationError(_('Files of size greater than %(max_size)s are not allowed. Your file is %(current_size)s') %
                                            {'max_size': filesizeformat(self.max_upload_size),
                                             'current_size': filesizeformat(file._size)})

        return data


class ApplicationPermit(models.Model):
    class Meta:
        verbose_name = _("permit file")
        verbose_name_plural = _("permit files")

    application = models.OneToOneField(Application, unique=True, verbose_name=_('application'))
    # we use custom filefield with mime-time validation
    file = ValidatedFileField(verbose_name=_('file'),
                              upload_to = "kurs/application_permits/%Y/%m/%d",
                              max_upload_size = 5242880,
                              content_types = ['application/msword',
                                               'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                                               'application/vnd.openxmlformats-officedocument.wordprocessingml.template',
                                               'application/x-bzip2',
                                               'application/x-gzip',
                                               'application/x-tar',
                                               'application/zip',
                                               'application/x-compressed-zip',
                                               'application/pdf',
                                               'application/postscript',
                                               'application/vnd.oasis.opendocument.text',
                                               'application/x-vnd.oasis.opendocument.text',
                                               ])
    upload_date = models.DateTimeField(verbose_name=_('upload date'),
                                       auto_now = True, auto_now_add = True)

# Model for other course choices for the same event
# Users not being able to accepted to their first application
# are given a couple of choices to automaticly apply to another
# course in the same event
class ApplicationChoices(models.Model):
    class Meta:
        verbose_name = _('choice')
        verbose_name_plural = _('choices')
        unique_together = (("person", "event", "choice_number"),
                           ("person", "event", "choice"))

    person = models.ForeignKey(User, verbose_name=_('user'))
    event = models.ForeignKey(Event, verbose_name=_('event'))
    last_update = models.DateTimeField(verbose_name=_('last updated'),
                                       auto_now = True, auto_now_add = True)
    choice_number = models.IntegerField(verbose_name=_('choice #'))
    choice = models.ForeignKey(Course, verbose_name=_('choice'))

    def __unicode__(self):
        return "%s -> %s -> %s - %s" %(self.person.username, self.event,
                                       self.choice_number, self.choice)

# Comments for a user logged by admins
class UserComment(models.Model):
    class Meta:
        verbose_name = _('comment')
        verbose_name_plural = _('comments')
        
    user = models.ForeignKey(User, verbose_name=_('user'))
    comment = models.TextField(verbose_name=_('comment'))
    date = models.DateTimeField(verbose_name=_('date'),
                                auto_now = True, auto_now_add = True)

    def __unicode__(self):
        return "%s - %s - %s" %(self.user.username, self.comment, self.date)

# Custom user profile in order to extend the standart User object that
# django.contrib.auth uses
class UserProfile(models.Model):
    user = models.OneToOneField(User, unique=True, verbose_name=_('user'), related_name='my_profile')
    company = models.CharField(verbose_name=_('company'), max_length=30)
    contact_address = models.TextField(verbose_name=_('contact address'))
    mobile = models.CharField(verbose_name=_('mobile'), max_length=10, help_text=_('ie. 2165554433'))
    phone = models.CharField(verbose_name=_('phone'), max_length=10, help_text=_('ie. 2165554433'))

# When a new user is registered, create his profile too
# Profile of a user can not be empty since we gather this information
# and write to DB at registration time with RegistrationFormUniqueEmailwithProfile
@receiver(user_registered)
# user_registered signal provides user and request instances
def create_profile(sender, user, request, **kwargs):
    user.first_name=request.POST['first_name']
    user.last_name=request.POST['last_name']
    user.save()
    (profile, created) = UserProfile.objects.get_or_create(user=user)
    profile.company = request.POST['company']
    profile.contact_address = request.POST['contact_address']
    profile.mobile = request.POST['mobile']
    profile.phone = request.POST['phone']
    profile.save()

# Edit profile page used by the django-profiles module requires
# request.username to be present. This view gets the username
# from the url. However we do not want users to see each others profiles
# so here we limit the username to only the username of the current user
# and change the urlconf to not pass username as a parameter
def get_absolute_url(self):
        return ('profiles_profile_detail', (), { 'username': self.user.username })

get_absolute_url = models.permalink(get_absolute_url)

# Model for all user and admin action logs
class ActionsLog(models.Model):
    class Meta:
        verbose_name = _('changelog')
        verbose_name_plural = _('changelogs')

    date = models.DateTimeField(verbose_name=_('date'), auto_now = True)
    message = models.CharField(verbose_name=_('message'), max_length = 200)

    def __unicode__(self):
        return "%s - %s" %(self.date, self.message)
