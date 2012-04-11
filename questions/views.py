from django.shortcuts import render_to_response #, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
#from django.core.urlresolvers import reverse
# Create your views here.
import django.forms
from questions import forms
from questions import models

import couchdbkit

def list(request):
    db = couchdbkit.ext.django.loading.get_db('questions')
    # categories_count = db.view('questions/categories_count', group=True)
    questions = db.view('questions/by_category')
    return render_to_response(  'questions/index.html',
            { 'questions':questions },
            context_instance=RequestContext(request)
            )


def delete(request,qid):
    db = couchdbkit.ext.django.loading.get_db('questions')
    if not db.doc_exist(qid):
        return HttpResponse("The indicated document (%s) doesn't exist" % qid)
    result = db.delete_doc(qid)
    if(result['ok']):
        return HttpResponse("Document %s Deleted" % qid)
    else:
        return HttpResponse("Something happened, please check document %s in the db" % qid)


def edit(request, qid):
    db = couchdbkit.ext.django.loading.get_db('questions')
    try:
        doc = db.get(qid)
    except couchdbkit.exceptions.ResourceNotFound:
        return HttpResponse("The indicated document (%s) doesn't exist" % qid)


    action = "/questions/create/%s" % doc['doc_type']
    form = getattr(forms,doc['doc_type'] + 'Form')
    if doc['doc_type'] == 'QuestionFromList':
        _extra={}
        _extra['qfl_size'] = len(doc['answer_data'])
        action +="/%s" % _extra['qfl_size']

        # the form will already receive doc['answer_data'] but here I will
        # structure it in a way that I can easily use in the form constructor
        for i in enumerate(doc['answer_data'],1):
            doc['answer_%s' % i[0]] = i[1]
            doc['ts_%s' % i[0]] = doc['answer_data'][i[1]]

        form = form(doc,extra=_extra)
    else:
        form = form(doc)

    return render_to_response(  'questions/question_form.html',
                              { 'form':form, 'extra_data': {'action':action} },
                                context_instance=RequestContext(request))

def clone(request, qid):
    db = couchdbkit.ext.django.loading.get_db('questions')
    try:
        doc = db.get(qid)
    except couchdbkit.exceptions.ResourceNotFound:
        return HttpResponse("The indicated document (%s) doesn't exist" % qid)

    del doc['_id']
    del doc['_rev']
    result = db.save_doc(doc)
    return edit(request, result['id'])

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
    # print "GET: ",  request.GET
    # print "POST: ",  request.POST
    # print "qfl_size in view: ", qfl_size
    if not type_:
        return HttpResponse("Invalid Type")

    if type_ == 'QuestionFromList':
        if not qfl_size:
            return HttpResponse("Invalid List Size")
        try:
            qfl_size = int(qfl_size)
        except ValueError:
            raise django.forms.ValidationError("Size (%s) is not a valid integer" % qfl_size)

    form = getattr(forms, type_ + 'Form', None)
    if not form:
        return HttpResponse('The specified form is invalid')

    extra_data={'question_type': type_}

    _extra = {}
    _extra['qfl_size'] = qfl_size
    form = form(request.POST or None, extra=_extra)
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
        return HttpResponse('The Question "%s" has been saved' % q.question)


    return render_to_response('questions/question_form.html',
                              {'form': form, 'extra_data': extra_data},
                                context_instance=RequestContext(request))


