# coding=utf-8

from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.contrib.formtools.wizard.views import SessionWizardView
from kurs.models import *
from kurs.forms import ApplicationAgreement, ApplicationChoice
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.views.generic import DetailView

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

class ApplicationWizard(SessionWizardView):
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(ApplicationWizard, self).get_context_data(**kwargs)
        # Add in the agreement text
        if self.steps.current == "0":
            course = Course.objects.get(pk = self.kwargs['course_id'])
            context['agreement'] = course.agreement
        return context

    def done(self, form_list, **kwargs):
        course_id = self.kwargs['course_id']
        course = Course.objects.get(pk = self.kwargs['course_id'])
        user = self.request.user
        choices = form_list[1].cleaned_data

        # save application to database
        application = Application(person = user, course = course, application_date = timezone.now())
        application.save()

        # save choices to database

        return render_to_response('kurs/application_done.html', {
            'form_data': choices,
            'course_id': user,
        })

    def get_template_names(self):
            return ['kurs/application_form.html']

    def get_form(self, step=None, data=None, files=None):
        course = Course.objects.get(pk = self.kwargs['course_id'])
        courses = Course.objects.filter(event = course.event).exclude(id = self.kwargs['course_id'])

        formset = super(ApplicationWizard, self).get_form(step, data, files)
        if not type(formset) == ApplicationAgreement:
            for form in formset:
                form.fields['choice'].choices = [(x.id,x.display_name) for x in courses]
        return formset

#login_required(ApplicationWizard.as_view([ApplicationAgreement, formset_factory(ApplicationChoice, extra = 4, max_num = 4)]))

@login_required
def apply_for_course(request, course_id):
    course = get_object_or_404(Course, pk=course_id)

    # kullanıcının bu event'de başvurduğu kurs var mı kontrol et
    previous_applications = Application.objects.filter(course__event=course.event).count()
    if previous_applications == 0:
        # save application to the database
        Application(person = request.user, course = course, application_date = timezone.now()).save()
        return HttpResponseRedirect('/kurs/etkinlik/' + str(course.event.id) + '/tercihler/')
    else:
        return render_to_response('kurs/hata.html',
                              {'mesaj': 'Bu etkinlikte sadece bir kursa kaydolabilirsiniz.'},
                              context_instance=RequestContext(request))

@login_required
def edit_choices(request, event_id):
    return render_to_response('kurs/hata.html', {
            'mesaj': "event_id=" + event_id,
            }, context_instance=RequestContext(request))

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
