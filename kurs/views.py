# coding=utf-8

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from kurs.models import ActionsLog, Event, Course, Application, ApplicationChoices
from kurs.models import ApplicationPermit
from kurs.forms import ApplicationChoiceForm, ApplicationPermitForm
from django.utils import timezone
from django.views.generic import DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import DeleteView
from django.forms.formsets import formset_factory
from django.utils.functional import curry
from django.contrib import messages

# FIXME: Better convert this as a signal receiver
def _log_action(message, username, REMOTE_ADDR):
    log = ActionsLog(message = "%s. request.user='%s' , request.META['REMOTE_ADDR']='%s'" %
                     (message, username, REMOTE_ADDR))
    log.save()

def index(request):
    return render_to_response('kurs/index.html',
                              {},
                              context_instance=RequestContext(request))

# List all courses of an event
def list_courses(request, event_id):
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        messages.error(request, "Böyle bir etkinlik yok")
        return render_to_response('kurs/hata.html',
            context_instance=RequestContext(request))
    try:
        course_list = Course.objects.filter(event=event_id)
    except Course.DoesNotExist:
        messages.error(request, "Kurs nesnelerini alırken hata oluştu")
        return render_to_response('kurs/hata.html',
            context_instance=RequestContext(request))
    
    return render_to_response('kurs/list_courses.html',
                              {'event': event.display_name,
                               'course_list': course_list,},
                              context_instance=RequestContext(request))

# User applied for a course
@login_required
def apply_for_course(request, course_id):
    try:
        course = Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        messages.error(request, "Böyle bir kurs yok")
        return render_to_response('kurs/hata.html',
            context_instance=RequestContext(request))

    # FIXME: Check course start and end dates in order to allow
    # applying to more than one course in the same event

    # Check if user has previously applied to another course
    # in the same event
    previous_applications = Application.objects.filter(person = request.user).filter(course__event=course.event).count()
    if previous_applications == 0:
        # FIXME: use tz-aware now
        application = Application(person = request.user, course = course,
                                  application_date = timezone.now())
        application.save()
        _log_action("Başvuru yapıldı: %s" % application,
                    request.user, request.META["REMOTE_ADDR"])
        messages.info(request, "Başvurunuz kaydedildi")
        # Redirect after successful application
        return HttpResponseRedirect('/kurs/etkinlik/' + str(course.event.id) + '/tercihler/')
    else:
        messages.error(request, "Bu etkinlikte sadece bir kursa kaydolabilirsiniz.")
        return render_to_response('kurs/hata.html',
                              context_instance=RequestContext(request))

class CourseDetailView(DetailView):
    context_object_name = "course"
    model = Course

    # We need extra context data in template in order to show informational
    # messages to user about why he can not apply for a selected course
    def get_context_data(self, **kwargs):
        context = super(CourseDetailView, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated():
            # Check if user has applied to another course in the same event
            context['previous_applications'] = Application.objects.filter(person = self.request.user).filter(course__event = self.object.event).count()
            # Check if user has applied to this course already
            context['has_applied'] = Application.objects.filter(course = self.object, person = self.request.user).count()
        return context

# List all previous applications of a user
class ApplicationList(ListView):
    template_name = "kurs/application_list.html"

    def get_queryset(self):
        return Application.objects.filter(person = self.request.user).order_by('-application_date', 'course__event')

# List all ApplicationChoice objects of user for this event
class ApplicationChoicesList(ListView):
    template_name = "kurs/applicationchoices_list.html"

    # Get eventid from request context
    # It gets passed to context from url
    def get_context_data(self, **kwargs):
        context = super(ApplicationChoicesList, self).get_context_data(**kwargs)
        context["event_id"] = self.kwargs['event_id']
        return context

    # Limit application choices to be displayed to only the current event
    def get_queryset(self):
        return ApplicationChoices.objects.filter(person = self.request.user).filter(event = self.kwargs['event_id']).order_by("choice_number")

# Edit ApplicationChoice objects of user for this event
@login_required
def edit_choices(request, event_id):

    event = Event.objects.get(id = event_id)
    # Get all previously made choices for this event
    previous_choices = ApplicationChoices.objects.filter(person = request.user, event = event_id).order_by("choice_number")

    max_num = event.allowed_choice_num
    extra = event.allowed_choice_num - previous_choices.count()

    # example: initial = [{"choice": "1"}, {"choice": "2"}]
    initial = []
    # Previous choices of the user must come pre-selected in edit form
    for choice in previous_choices:
        initial.append({"choice": str(choice.choice.id)})

    # example: choices = [("1","1"), ("2","2")]
    choices = []

    # Remove applied course from possible choices for this event
    try:
        applied_course = Application.objects.get(person = request.user, course__event = event_id)
    except Application.DoesNotExist:
        messages.error(request, "Bu etkinlikte hiçbir kursa başvurmadınız")
        return render_to_response('kurs/hata.html',
                    context_instance=RequestContext(request))

    # FIXME: use only courses that are open for application
    courses = Course.objects.filter(event = event_id).exclude(id = applied_course.course.id)
    for course in courses:
        choices.append((course.id, course.display_name))

    # initialize form according to allowed_choice_num for the event
    # the reason we use formset here instead of a regular form is
    # we do now know in advance how many allowed_choice_num there will be
    # for a given event. Since the number is dynamic (coming from model/DB)
    # we have to use formset and generate necessary number of choice drop-down
    formset = formset_factory(ApplicationChoiceForm, max_num = max_num, extra = extra)
    formset.form = staticmethod(curry(ApplicationChoiceForm, choices=choices))

    if request.method == 'POST':
        EditChoicesFormSet = formset(request.POST, request.FILES)
        if EditChoicesFormSet.is_valid():
            # Delete all choices made previously in order to overwrite
            if not previous_choices.count() == 0:
                for prev_choices in previous_choices:
                    _log_action("Tercih silindi: %s" % prev_choices,
                                request.user, request.META["REMOTE_ADDR"])
                previous_choices.delete()

            # save all applicationchoices of user to the DB
            choice_number = 1
            for choices in EditChoicesFormSet.cleaned_data:
                record = ApplicationChoices(person = request.user,
                                            event = Event.objects.get(id = event_id),
                                            choice_number = choice_number,
                                            choice = Course.objects.get(id = choices["choice"]))
                record.save()
                _log_action("Tercih yapıldı: %s" % record,
                    request.user, request.META["REMOTE_ADDR"])
                choice_number += 1

            messages.info(request, "Tercihleriniz kaydedildi")
            # redirect to his applicationchoice list for this event
            return HttpResponseRedirect("/kurs/etkinlik/" + event_id + "/tercihler/")

    else:
        return render_to_response('kurs/applicationchoices_edit.html',
                              {'formset': formset(initial=initial)},
                              context_instance=RequestContext(request))

# Delete a selected previous application
# primarykey (pk) is coming from the url
class ApplicationDeleteView(DeleteView):
    context_object_name = "application"
    model = Application
    success_url = "/kurs/basvurular/"

    # We do not want current user to delete other users applications
    # therefore we modify the queryset to return the object given in url
    # only if he owns the application
    def get_queryset(self):
        return Application.objects.filter(person = self.request.user).filter(id = self.kwargs['pk'])

    def delete(self, request, *args, **kwargs):
        application = Application.objects.get(person = self.request.user, id = self.kwargs['pk'])

        # We do not want the user to delete an application already approved
        # this will mess up with class counts and expectations
        if not application.approved:
            # Delete application permit file associated with this application
            try:
                applicationpermit = ApplicationPermit.objects.get(application = application)
                _log_action("İzin yazısı silindi: %s" % applicationpermit,
                    request.user, request.META["REMOTE_ADDR"])
                applicationpermit.delete()
                messages.info(request, "İzin yazınız silindi")
            except ApplicationPermit.DoesNotExist:
                pass

            messages.info(request, "Başvurunuz iptal edildi")
            messages.info(request, "Başvuru tercihleriniz silindi")
            _log_action("Başvuru silindi: %s" % application,
                    request.user, request.META["REMOTE_ADDR"])
            return DeleteView.delete(self, request, *args, **kwargs)

        else:
            messages.error(request, "Onaylanmış bir başvuruyu iptal edemezsiniz")
            return render_to_response('kurs/hata.html',
                        context_instance=RequestContext(request))

# Allow user to upload a permit file for an application
# application_id is coming from url
def upload_permit(request, application_id):

    if request.method == 'POST':
        form = ApplicationPermitForm(request.POST, request.FILES)
        if form.is_valid():
            # FIXME: Check if this user is the owner of the application
            application = Application.objects.get(id = application_id)
            try:
                applicationpermit = ApplicationPermit.objects.get(application__id = application_id)
                applicationpermit.file = request.FILES["file"]
                applicationpermit.save()
                _log_action("İzin yazısı yüklendi: %s" % applicationpermit,
                            request.user, request.META["REMOTE_ADDR"])
            except ApplicationPermit.DoesNotExist:
                applicationpermit = ApplicationPermit(application = application,
                                                      file = request.FILES['file'])
                applicationpermit.save()
                _log_action("İzin yazısı yüklendi: %s" % applicationpermit,
                            request.user, request.META["REMOTE_ADDR"])

            messages.info(request, "İzin yazınız kaydedildi")
            return HttpResponseRedirect('/kurs/basvurular/')

    else:
        form = ApplicationPermitForm()

    return render_to_response('kurs/applicationpermit_form.html',
                              {'form': form},
                              context_instance=RequestContext(request))

# Allow user to see his profile
def profile_detail(request):
    profile_obj = request.user.get_profile()

    return render_to_response('kurs/profile_detail.html',
                              { 'profile': profile_obj },
                              context_instance=RequestContext(request))
