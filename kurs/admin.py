# coding=utf-8

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from kurs.models import Event, Course, UserComment, Application, ApplicationChoices, ApplicationPermit, UserProfile, ActionsLog

class EventAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'venue', 'allowed_choice_num')
    search_fields = ['display_name', 'venue']

class CourseAdmin(admin.ModelAdmin):
    list_display = ('event', 'display_name', 'is_open', 'change_allowed_date', 'start_date', 'end_date')
    search_fields = ['display_name']
    list_filter = ['event']
    date_hierarchy = 'start_date'
    ordering = ['-event__id', 'id']

class ApplicationPermitInline(admin.StackedInline):
    model = ApplicationPermit
    can_delete = True
    verbose_name_plural = 'İzin Yazıları'
    verbose_name = 'İzin Yazısı'
    extra=0

class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('person', 'course', 'application_date', 'has_applicationpermit', 'approved', 'approved_by', 'approve_date')
    search_fields = ['person__username', 'course__display_name', 'approved_by__username']
    list_filter = ['course__event', 'approved', 'application_date']
    date_hierarchy = 'application_date'
    ordering = ['person__id', '-application_date']
    inlines = [ApplicationPermitInline]

    def has_applicationpermit(self, obj):
        return True if obj.applicationpermit else False
    has_applicationpermit.boolean = True
    has_applicationpermit.short_description = 'İzin Yazısı'

class ApplicationChoicesAdmin(admin.ModelAdmin):
    list_display = ('person', 'event', 'choice_number', 'choice', 'last_update')
    search_fields = ['person__username', 'event__display_name', 'choice__display_name']
    list_filter = ['event', 'last_update']
    date_hierarchy = 'last_update'
    ordering = ['person__id', '-event__id', 'choice']

class ActionsLogAdmin(admin.ModelAdmin):
    list_display = ('date', 'message')
    search_fields = ['message']
    list_filter = ['date']
    date_hierarchy = 'date'
    ordering = ['-date']

class ApplicationPermitAdmin(admin.ModelAdmin):
    list_display = ('get_application_person', 'get_application_event', 'get_application_course', 'upload_date', 'file')
    search_fields = ['file']
    list_filter = ['upload_date']
    date_hierarchy = 'upload_date'
    ordering = ['-upload_date']

    def get_application_person(self, obj):
        return ("%s" % (obj.application.person.username))
    get_application_person.short_description = 'User'

    def get_application_event(self, obj):
        return ("%s" % (obj.application.course.event.display_name))
    get_application_event.short_description = 'Event'

    def get_application_course(self, obj):
        return ("%s" % (obj.application.course.display_name))
    get_application_course.short_description = 'Course'

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

admin.site.register(Event, EventAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Application, ApplicationAdmin)
admin.site.register(ApplicationChoices, ApplicationChoicesAdmin)
admin.site.register(ApplicationPermit, ApplicationPermitAdmin)
admin.site.register(ActionsLog, ActionsLogAdmin)
