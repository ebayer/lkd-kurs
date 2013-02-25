# coding=utf-8

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from kurs.models import Event, Course, UserComment, Application, ApplicationChoices
from kurs.models import ApplicationPermit, UserProfile, ActionsLog
from django.utils.encoding import force_unicode
from django.contrib.admin import helpers
from django.template.response import TemplateResponse
from django.contrib.admin.util import model_ngettext
from django.utils.translation import ugettext as _
from django.contrib.admin import SimpleListFilter

# Admin action to change the application status of the courses
# used in list courses view (admin/kurs/course)
def change_course_is_open(modeladmin, request, queryset):
    # got from django.contrib.admin.actions
    opts = modeladmin.model._meta
    app_label = opts.app_label

    if request.POST.get('post'):
        n = queryset.count()
        if n:
            queryset.update(is_open = True if request.POST['status'] == 'True' else False)
            modeladmin.message_user(request, _("Successfully changed %(count)d %(items)s.") % {
                "count": n, "items": model_ngettext(modeladmin.opts, n)
            })
        # Return None to display the change list page again.
        return None

    title = _("Are you sure?")

    if len(queryset) == 1:
        objects_name = force_unicode(opts.verbose_name)
    else:
        objects_name = force_unicode(opts.verbose_name_plural)

    courses = queryset.all()
    editable_objects = []
    for course in courses:
        editable_objects.append(course.__unicode__())

    context = {
        "title": title,
        "objects_name": objects_name,
        "editable_objects": [editable_objects],
        'queryset': queryset,
        "opts": opts,
        "app_label": app_label,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
    }

    # Display the confirmation page
    return TemplateResponse(request, 'admin/change_course_is_open.html',
    context, current_app=modeladmin.admin_site.name)
change_course_is_open.short_description = "Seçili kursların başvuru statüsünü değiştir"

# Admin page for events
class EventAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'venue', 'allowed_choice_num')
    search_fields = ['display_name', 'venue']

# Admin page for courses
class CourseAdmin(admin.ModelAdmin):
    list_display = ('event', 'display_name', 'is_open', 'change_allowed_date',
                    'start_date', 'end_date')
    search_fields = ['display_name']
    list_filter = ['event']
    date_hierarchy = 'start_date'
    ordering = ['-event__id', 'id']
    actions = [change_course_is_open]

# We want the applicationpermit of every application to be editable
# inline from application detail view admin page
class ApplicationPermitInline(admin.StackedInline):
    model = ApplicationPermit
    can_delete = True
    verbose_name_plural = 'İzin Yazıları'
    verbose_name = 'İzin Yazısı'
    extra=0

# We want to filter according to the availability of an applicationpermit.
# Since applicationpermit is another model, we need to define a custom way
# to filter queryset according to the one-to-one field
class HasApplicationPermitFilter(SimpleListFilter):
    title = _('izin yazısı')
    parameter_name = 'permit'

    # Available choices for the filter
    def lookups(self, request, model_admin):
        return [
            ('1', 'Var'),
            ('0', 'Yok'),
        ]

    # Filter queryset for application accoring to applicationpermit availability
    def queryset(self, request, queryset):
        if self.value() == '0':
            return queryset.filter(applicationpermit=None)
        if self.value() == '1':
            return queryset.filter(applicationpermit=True)
        else:
            return queryset

# Admin page for applications
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('person', 'course', 'application_date', 'has_applicationpermit',
                    'approved', 'approved_by', 'approve_date')
    search_fields = ['person__username', 'course__display_name', 'approved_by__username']
    list_filter = ['course__event', 'approved', 'application_date', HasApplicationPermitFilter]
    date_hierarchy = 'application_date'
    ordering = ['person__id', '-application_date']
    inlines = [ApplicationPermitInline]

    # We want to see if user has uploaded an applicationpermit when
    # listing all applications
    def has_applicationpermit(self, obj):
        return True if obj.applicationpermit else False
    has_applicationpermit.boolean = True
    has_applicationpermit.short_description = 'İzin Yazısı'

# Admin page for other application choices in this event
class ApplicationChoicesAdmin(admin.ModelAdmin):
    list_display = ('person', 'event', 'choice_number', 'choice', 'last_update')
    search_fields = ['person__username', 'event__display_name', 'choice__display_name']
    list_filter = ['event', 'last_update']
    date_hierarchy = 'last_update'
    ordering = ['person__id', '-event__id', 'choice']

# Admin page for user and admin action logs
class ActionsLogAdmin(admin.ModelAdmin):
    list_display = ('date', 'message')
    search_fields = ['message']
    list_filter = ['date']
    date_hierarchy = 'date'
    ordering = ['-date']

# Admin page for applicationpermits
class ApplicationPermitAdmin(admin.ModelAdmin):
    list_display = ('get_application_person', 'get_application_event',
                    'get_application_course', 'upload_date', 'file')
    search_fields = ['file']
    list_filter = ['upload_date']
    date_hierarchy = 'upload_date'
    ordering = ['-upload_date']

    # Model for applicationpermit only uses an applicationobject as 1-to-1 reference
    # Since we do not have the user/event/course information that this applicationpermit
    # is used by, we need external functions to gather that information to present in
    # admin list view
    def get_application_person(self, obj):
        return ("%s" % (obj.application.person.username))
    get_application_person.short_description = 'User'

    def get_application_event(self, obj):
        return ("%s" % (obj.application.course.event.display_name))
    get_application_event.short_description = 'Event'

    def get_application_course(self, obj):
        return ("%s" % (obj.application.course.display_name))
    get_application_course.short_description = 'Course'

# We like to edit user profile data inline from user detail page
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Kullanıcı Bilgileri'
    verbose_name = 'Kullanıcı Bilgisi'

# We like to edit user comment data inline from user detail page
class UserCommentInline(admin.StackedInline):
    model = UserComment
    can_delete = True
    verbose_name_plural = 'Yorumlar'
    verbose_name = 'Yorum'
    extra=0

# Define a new admin page for editing user details in order to use the inlines
class UserAdmin(UserAdmin):
    inlines = (UserProfileInline, UserCommentInline)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active',
                    'is_staff', 'get_userprofile_company')
    list_filter = ['is_active', 'is_staff',]

    # We do not have the company information in standart user model,
    # we need to get that information from the related UserProfile model
    def get_userprofile_company(self, obj):
        return ("%s" % (obj.my_profile.company))
    get_userprofile_company.short_description = 'Kurum'

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Register admin pages
admin.site.register(Event, EventAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Application, ApplicationAdmin)
admin.site.register(ApplicationChoices, ApplicationChoicesAdmin)
admin.site.register(ApplicationPermit, ApplicationPermitAdmin)
admin.site.register(ActionsLog, ActionsLogAdmin)
