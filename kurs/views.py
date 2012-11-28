from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from kurs.models import *

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

@login_required()
def apply_for_course(request, course_id):
    pass

