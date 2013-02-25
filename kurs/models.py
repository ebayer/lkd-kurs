# coding=utf-8

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from registration.signals import user_registered
from django.utils.timezone import now as tz_aware_now
from django.db.models.signals import pre_delete
from django import forms
from django.template.defaultfilters import filesizeformat
import magic

class Event(models.Model):
    class Meta:
        verbose_name = "Etkinlik"
        verbose_name_plural = "Etkinlikler"
    
    display_name = models.CharField('Görünen İsim', max_length=200)
    allowed_choice_num = models.IntegerField('Bu etkinlik için kullanıcıların yapabileceği tercih adedi',
                                             default=2)
    venue = models.CharField('Etkinlik mekanı', max_length=200)
    
    def __unicode__(self):
        return self.display_name

class Course(models.Model):
    class Meta:
        verbose_name = "Kurs"
        verbose_name_plural = "Kurslar"
    
    event = models.ForeignKey(Event)
    display_name = models.CharField('Görünen isim', max_length=200)
    description = models.TextField('Açıklama')
    is_open = models.BooleanField('Başvuru yapılabilir?')
    change_allowed_date = models.DateTimeField('Kullanıcıların başvuru/değişiklik yapabilecekleri son tarih')
    agreement = models.TextField('Kurs yükümlülükleri')
    start_date = models.DateField('Kurs başlangıç tarihi')
    end_date = models.DateField('Kurs bitiş tarihi')

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
        verbose_name = "Başvuru"
        verbose_name_plural = "Başvurular"
        unique_together = (("person", "course"),)

    person = models.ForeignKey(User, related_name='application_users')
    course = models.ForeignKey(Course)
    application_date = models.DateTimeField()
    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, related_name='application_approver',
                                    blank=True, null=True)
    approve_date = models.DateTimeField(blank=True, null=True)

    def __unicode__(self):
        return "%s -> %s" % (self.person.username, self.course)

def delete_application_choices(sender, **kwargs):
    instance = kwargs['instance']
    ApplicationChoices.objects.filter(person = instance.person,
                                      event = instance.course.event).delete()

# Delete all application choices for the event
# whenever an application gets deleted
pre_delete.connect(delete_application_choices, sender=Application,
                   dispatch_uid="unique_identifier")

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
        verbose_name = "İzin Yazısı"
        verbose_name_plural = "İzin Yazıları"

    application = models.OneToOneField(Application, unique=True)
    # we use custom filefield with mime-time validation
    file = ValidatedFileField(upload_to = "kurs/application_permits/%Y/%m/%d",
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
    upload_date = models.DateTimeField(auto_now = True, auto_now_add = True)

# Model for other course choices for the same event
# Users not being able to accepted to their first application
# are given a couple of choices to automaticly apply to another
# course in the same event
class ApplicationChoices(models.Model):
    class Meta:
        verbose_name = "Tercih"
        verbose_name_plural = "Tercihler"
        unique_together = (("person", "event", "choice_number"),
                           ("person", "event", "choice"))

    person = models.ForeignKey(User)
    event = models.ForeignKey(Event)
    last_update = models.DateTimeField(auto_now = True, auto_now_add = True)
    choice_number = models.IntegerField()
    choice = models.ForeignKey(Course)

    def __unicode__(self):
        return "%s -> %s -> %s - %s" %(self.person.username, self.event,
                                       self.choice_number, self.choice)

# Comments for a user logged by admins
class UserComment(models.Model):
    class Meta:
        verbose_name = "Yorum"
        verbose_name_plural = "Yorumlar"
        
    user = models.ForeignKey(User)
    comment = models.TextField()
    date = models.DateTimeField(auto_now = True, auto_now_add = True)

    def __unicode__(self):
        return "%s - %s - %s" %(self.user.username, self.comment, self.date)

# Custom user profile in order to extend the standart User object that
# django.contrib.auth uses
class UserProfile(models.Model):
    user = models.OneToOneField(User, unique=True, verbose_name=_('user'), related_name='my_profile')
    company = models.CharField('Çalıştığı Kurum',max_length=30)
    contact_address = models.TextField("İletişim Adresi")
    mobile = models.CharField('Cep Telefonu (2165554433)',max_length=10)
    phone = models.CharField('Ev Telefonu (2165554433)', max_length=10)

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

# When a new user is registered, create his profile too
# Profile of a user can not be empty since we gather this information
# and write to DB at registration time with RegistrationFormUniqueEmailwithProfile
user_registered.connect(create_profile)

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
        verbose_name = "Değişiklik kaydı"
        verbose_name_plural = "Değişiklik kayıtları"

    date = models.DateTimeField(auto_now = True)
    message = models.CharField(max_length = 200)

    def __unicode__(self):
        return "%s - %s" %(self.date, self.message)
