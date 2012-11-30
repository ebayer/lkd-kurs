# coding=utf-8

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils.translation import ugettext as _
from userena.models import UserenaBaseProfile

class Event(models.Model):
    class Meta:
        verbose_name = "Etkinlik"
        verbose_name_plural = "Etkinlikler"
    
    display_name = models.CharField('Görünen İsim', max_length=200)
    allowed_choice_num = models.IntegerField('Bu etkinlik için kullanıcıların yapabileceği tercih adedi', default=2)
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
    
    def __unicode__(self):
        return self.display_name

class Application(models.Model):
    class Meta:
        verbose_name = "Başvuru"
        verbose_name_plural = "Başvurular"
        unique_together = (("person", "course"),)

    person = models.ForeignKey(User, related_name='application_users')
    course = models.ForeignKey(Course)
    application_date = models.DateTimeField()
    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, related_name='application_approver', blank=True, null=True)
    approve_date = models.DateTimeField(blank=True, null=True)

    def __unicode__(self):
        return self.person.username + " - " + self.course.display_name

class ApplicationChoices(models.Model):
    class Meta:
        verbose_name = "Tercih"
        verbose_name_plural = "Tercihler"
        unique_together = (("person", "event", "choice_number"),
                           ("person", "event", "choice"))

    person = models.ForeignKey(User)
    event = models.ForeignKey(Event)
    last_update = models.DateTimeField()
    choice_number = models.IntegerField()
    choice = models.ForeignKey(Course)

    def __unicode__(self):
        return self.person.username + " - " + self.event.display_name + " - " + self.choice.display_name

class UserComment(models.Model):
    class Meta:
        verbose_name = "Yorum"
        verbose_name_plural = "Yorumlar"
        
    user = models.ForeignKey(User)
    comment = models.TextField()
    date = models.DateTimeField()

class UserProfile(UserenaBaseProfile):
    user = models.OneToOneField(User, unique=True, verbose_name=_('user'), related_name='my_profile')
    company = models.CharField('Çalıştığı Kurum',max_length=30)
    contact_address = models.TextField("İletişim Adresi")
    mobile = models.CharField('Cep Telefonu (2165554433)',max_length=10)
    phone = models.CharField('Ev Telefonu (2165554433)', max_length=10)
    
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)

post_save.connect(create_user_profile, sender=User)
