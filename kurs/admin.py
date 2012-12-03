# coding=utf-8

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from kurs.models import Event, Course, UserComment, Application, ApplicationChoices, ApplicationPermit, UserProfile, ActionsLog

admin.site.register(Event)
admin.site.register(Course)
admin.site.register(Application)
admin.site.register(ApplicationChoices)
admin.site.register(ApplicationPermit)
admin.site.register(ActionsLog)

# Define an inline admin descriptor for UserProfile model
# which acts a bit like a singleton
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Kullanıcı Bilgileri'
    verbose_name = 'Kullanıcı Bilgisi'
    
class UserCommentInline(admin.StackedInline):
    model = UserComment
    can_delete = True
    verbose_name_plural = 'Yorumlar'
    verbose_name = 'Yorum'
    extra=0

# Define a new User admin
class UserAdmin(UserAdmin):
    inlines = (UserProfileInline, UserCommentInline)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
