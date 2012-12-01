# coding=utf-8

from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.contrib.formtools.wizard.views import SessionWizardView
from kurs.models import *
from kurs.forms import ApplicationChoiceForm
from django.utils import timezone
from django.http import HttpResponseRedirect, HttpResponseServerError
from django.views.generic import DetailView
from django.views.generic.list import ListView
from django.forms.formsets import formset_factory
from django.utils.functional import curry
from django.views.generic.edit import DeleteView

def index(request):
    return render_to_response('kurs/index.html',
                              {},
                              context_instance=RequestContext(request))
    
def list_courses(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    course_list = get_list_or_404(Course, event=event_id)
    
    return render_to_response('kurs/list_courses.html',
                              {'event': event.display_name,
                               'course_list': course_list,},
                              context_instance=RequestContext(request))

@login_required
def apply_for_course(request, course_id):
    course = get_object_or_404(Course, pk=course_id)

    # Fixme: Başvuru yaparken tarihleri kontrol et
    previous_applications = Application.objects.filter(course__event=course.event).count()
    if previous_applications == 0:
        # save application to the database
        Application(person = request.user, course = course, application_date = timezone.now()).save()
        return HttpResponseRedirect('/kurs/etkinlik/' + str(course.event.id) + '/tercihler/')
    else:
        return render_to_response('kurs/hata.html',
                              {'mesaj': 'Bu etkinlikte sadece bir kursa kaydolabilirsiniz.'},
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
            return render_to_response('kurs/hata.html', {
                        'mesaj': "Bu etkinlikte hiçbir kursa başvurmadınız",
                        }, context_instance=RequestContext(request))

    courses = Course.objects.filter(event = event_id).exclude(id = applied_course.course.id)
    for course in courses:
        choices.append((course.id, course.display_name))
    formset = formset_factory(ApplicationChoiceForm, max_num = max_num, extra = extra)
    formset.form = staticmethod(curry(ApplicationChoiceForm, choices=choices))

    if request.method == 'POST':
        EditChoicesFormSet = formset(request.POST, request.FILES)
        if EditChoicesFormSet.is_valid():
            if not previous_choices.count() == 0:
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
                choice_number += 1

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
        applicationchoices = ApplicationChoices.objects.filter(person = self.request.user).filter(event = application.course.event)
        applicationchoices.delete()
        return DeleteView.delete(self, request, *args, **kwargs)
