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
    allowed_choice_num = models.IntegerField('Bu etkinlik için kullanıcıların yapabileceği tercih adedi')
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
