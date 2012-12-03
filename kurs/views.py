# coding=utf-8

from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.contrib.formtools.wizard.views import SessionWizardView
from kurs.models import *
from kurs.forms import ApplicationChoiceForm, ApplicationPermitForm
from django.utils import timezone
from django.http import HttpResponseRedirect, HttpResponseServerError
from django.views.generic import DetailView
from django.views.generic.list import ListView
from django.forms.formsets import formset_factory
from django.utils.functional import curry
from django.views.generic.edit import DeleteView
from django.contrib import messages

def _log_action(message, username, REMOTE_ADDR):
    log = ActionsLog(message = "%s. request.user='%s' , request.META['REMOTE_ADDR']='%s'" % (message, username, REMOTE_ADDR))
    log.save()

def index(request):
    return render_to_response('kurs/index.html',
                              {},
                              context_instance=RequestContext(request))
    
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

@login_required
def apply_for_course(request, course_id):
    try:
        course = Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        messages.error(request, "Böyle bir kurs yok")
        return render_to_response('kurs/hata.html',
            context_instance=RequestContext(request))

    # Fixme: Başvuru yaparken tarihleri kontrol et
    previous_applications = Application.objects.filter(course__event=course.event).count()
    if previous_applications == 0:
        # save application to the database
        application = Application(person = request.user, course = course, application_date = timezone.now())
        application.save()
        _log_action("Başvuru yapıldı: %s" % application,
                    request.user, request.META["REMOTE_ADDR"])
        messages.info(request, "Başvurunuz kaydedildi")
        return HttpResponseRedirect('/kurs/etkinlik/' + str(course.event.id) + '/tercihler/')
    else:
        messages.error(request, "Bu etkinlikte sadece bir kursa kaydolabilirsiniz.")
        return render_to_response('kurs/hata.html',
                              context_instance=RequestContext(request))


#    return render_to_response('kurs/hata.html', {
#            'mesaj': "event_id=" + event_id,
#            }, context_instance=RequestContext(request))

class CourseDetailView(DetailView):
    context_object_name = "course"
    model = Course

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(CourseDetailView, self).get_context_data(**kwargs)
        # Add extra context
        # kullanıcının bu event'de başvurduğu kurs var mı kontrol et
        if self.request.user.is_authenticated():
            context['previous_applications'] = Application.objects.filter(course__event = self.object.event).count()
            context['has_applied'] = Application.objects.filter(course = self.object, person = self.request.user).count()
        return context

class ApplicationChoicesList(ListView):
    template_name = "kurs/applicationchoices_list.html"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(ApplicationChoicesList, self).get_context_data(**kwargs)
        context["event_id"] = self.kwargs['event_id']
        return context

    def get_queryset(self):
        return ApplicationChoices.objects.filter(person = self.request.user).filter(event = self.kwargs['event_id']).order_by("choice_number")

@login_required
def edit_choices(request, event_id):
#    choices = [("1","1"), ("2","2")]
#    initial = [{"choice": "1"}, {"choice": "2"}]

    event = Event.objects.get(id = event_id)
    previous_choices = ApplicationChoices.objects.filter(person = request.user, event = event_id).order_by("choice_number")

    max_num = event.allowed_choice_num
    extra = event.allowed_choice_num - previous_choices.count()

    initial = []
    for choice in previous_choices:
        initial.append({"choice": str(choice.choice.id)})

    choices = []
    try:
        applied_course = Application.objects.get(person = request.user, course__event = event_id)
    except Application.DoesNotExist:
        messages.error(request, "Bu etkinlikte hiçbir kursa başvurmadınız")
        return render_to_response('kurs/hata.html',
                    context_instance=RequestContext(request))

    courses = Course.objects.filter(event = event_id).exclude(id = applied_course.course.id)
    for course in courses:
        choices.append((course.id, course.display_name))
    formset = formset_factory(ApplicationChoiceForm, max_num = max_num, extra = extra)
    formset.form = staticmethod(curry(ApplicationChoiceForm, choices=choices))

    if request.method == 'POST':
        EditChoicesFormSet = formset(request.POST, request.FILES)
        if EditChoicesFormSet.is_valid():
            # Fixme: tüm tercihlerin geçerli olduğunu kontrol et
            if not previous_choices.count() == 0:
                for prev_choices in previous_choices:
                    _log_action("Tercih silindi: %s" % prev_choices,
                                request.user, request.META["REMOTE_ADDR"])
                previous_choices.delete()

            last_update = timezone.now()
            choice_number = 1
            for choices in EditChoicesFormSet.cleaned_data:
                record = ApplicationChoices(person = request.user,
                                            event = Event.objects.get(id = event_id),
                                            last_update = last_update,
                                            choice_number = choice_number,
                                            choice = Course.objects.get(id = choices["choice"]))
                record.save()
                _log_action("Tercih yapıldı: %s" % record,
                    request.user, request.META["REMOTE_ADDR"])
                choice_number += 1

            messages.info(request, "Tercihleriniz kaydedildi")
            return HttpResponseRedirect("/kurs/etkinlik/" + event_id + "/tercihler/")
    else:
        return render_to_response('kurs/applicationchoices_edit.html',
                              {'formset': formset(initial=initial)},
                              context_instance=RequestContext(request))

class ApplicationDeleteView(DeleteView):
    context_object_name = "application"
    model = Application
    success_url = "/kurs/basvurular/"

    def get_queryset(self):
        return Application.objects.filter(person = self.request.user).filter(id = self.kwargs['pk'])

    def delete(self, request, *args, **kwargs):
        # Fixme: kullanıcıya düzgün bir mesaj dön
        # success_message = "jhjhjk"
        application = Application.objects.get(person = self.request.user, id = self.kwargs['pk'])
        if not application.approved:
            applicationchoices = ApplicationChoices.objects.filter(person = self.request.user).filter(event = application.course.event)
            for prev_choices in applicationchoices:
                _log_action("Tercih silindi: %s" % prev_choices,
                            request.user, request.META["REMOTE_ADDR"])
            applicationchoices.delete()
            messages.info(request, "Başvuru tercihleriniz silindi")
            applicationpermit = ApplicationPermit.objects.get(application = application)
            _log_action("İzin yazısı silindi: %s" % applicationpermit,
                    request.user, request.META["REMOTE_ADDR"])
            # this removes the file from fs but does not call object.save()
            applicationpermit.file.delete()
            applicationpermit.delete()
            messages.info(request, "Terich yazınız silindi")
            messages.info(request, "Başvurunuz iptal edildi")
            _log_action("Başvuru silindi: %s" % application,
                    request.user, request.META["REMOTE_ADDR"])
            return DeleteView.delete(self, request, *args, **kwargs)
        else:
            messages.error(request, "Onaylanmış bir başvuruyu iptal edemezsiniz")
            return render_to_response('kurs/hata.html',
                        context_instance=RequestContext(request))

def upload_permit(request, application_id):
    if request.method == 'POST':
        form = ApplicationPermitForm(request.POST, request.FILES)
        if form.is_valid():
            application = Application.objects.get(id = application_id)
            try:
                applicationpermit = ApplicationPermit.objects.get(application__id = application_id)
                _log_action("İzin yazısı silindi: %s" % applicationpermit,
                    request.user, request.META["REMOTE_ADDR"])
                # this removes the file from fs but does not call object.save()
                applicationpermit.file.delete()
                applicationpermit.file = request.FILES["file"]
                applicationpermit.save()
                _log_action("İzin yazısı yüklendi: %s" % applicationpermit,
                    request.user, request.META["REMOTE_ADDR"])
            except ApplicationPermit.DoesNotExist:
                applicationpermit = ApplicationPermit(application = application, file = request.FILES['file'])
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
