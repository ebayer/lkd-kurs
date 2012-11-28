from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from kurs.models import *

def index(request):
    return render_to_response('kurs/index.html',
                              {},
                              context_instance=RequestContext(request))

def list_events(request):
    event_list = Event.objects.all().order_by('-display_name')
    return render_to_response('kurs/list_events.html',
                              {'event_list': event_list,},
                              context_instance=RequestContext(request))
    
def list_courses(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    course_list = get_list_or_404(Course, event=event_id)
    
    return render_to_response('kurs/list_courses.html',
                              {'event': event.display_name,
                               'course_list': course_list,},
                              context_instance=RequestContext(request))
    
def course_details(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    
    return render_to_response('kurs/course_details.html',
                              {'course': course,},
                              context_instance=RequestContext(request))

@login_required()
def apply_for_course(request, course_id):
    pass

