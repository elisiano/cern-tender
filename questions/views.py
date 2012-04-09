from django.shortcuts import render_to_response #, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
#from django.core.urlresolvers import reverse
# Create your views here.
import django.forms
from questions import forms
from questions import models

def list(request):
    return render_to_response('questions/index.html')


def qtype(request):
    #print request
    if request.method == 'POST':
        form = forms.QuestionForm(request.POST)
        if form.is_valid():
            print form.cleaned_data
            uri = '/questions/create/%s' % form.cleaned_data['question_type']
            if form.cleaned_data['question_type']== "QuestionFromList":
                uri += '/%d' % form.cleaned_data['qfl_size']
            return HttpResponseRedirect(uri)
    else:
        form = forms.QuestionForm()

    return render_to_response('questions/question_form.html',
            {'form': form, 'extra_data': {'action':'/questions/new/'}},
                              context_instance=RequestContext(request))


def qcreate(request, type_, qfl_size=0):
    print "GET: ",  request.GET
    print "POST: ",  request.POST
    print "qfl_size in view: ", qfl_size
    if not type_:
        return HttpResponse("Invalid Type")

    if type_ == 'QuestionFromList':
        if not qfl_size:
            return HttpResponse("Invalid List Size")
        try:
            qfl_size = int(qfl_size)
        except ValueError, e:
            raise django.forms.ValidationError("Size (%s) is not a valid integer" % qfl_size)
            
    form = getattr(forms, type_ + 'Form', None)
    if not form:
        HttpRepsponse('The specified form is invalid')
    
    extra_data={'question_type': type_}
    
    _extra = {}
    _extra['qfl_size'] = qfl_size
    if request.method=="POST":
        form = form(request.POST, extra=_extra)
        if form.is_valid():
            ### QuestionFromList must be treated differently
            if type_ == 'QuestionFromList':
                answer_data={}
                for i in range(1,qfl_size+1):
                    _ans = form.cleaned_data.pop('answer_%s' %i)
                    _ts = form.cleaned_data.pop('ts_%s' %i)
                    answer_data[_ans] = _ts
                q = getattr(models, type_)(form.cleaned_data, answer_data=answer_data)
            ### Other forms
            else:
                q = getattr(models, type_)(form.cleaned_data)
            q.save()
            return HttpResponse('<pre>' + q.to_json() + '</pre>')
                
    else:
        form=form(extra=_extra)
        
    return render_to_response('questions/question_form.html',
                              {'form': form, 'extra_data': extra_data},
                                context_instance=RequestContext(request))
 
        
