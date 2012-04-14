# Create your views here.
from django.shortcuts import render_to_response
from django.template import RequestContext
import couchdbkit
from documents import forms
from tender.utils import message

db = couchdbkit.ext.django.loading.get_db('documents')

def list(request):
    documents = db.all_docs()
    for k in documents:
        print "k: ", k, "v: ",documents[k]
    return render_to_response(  'documents/index.html',
            { 'documents':documents },
            context_instance=RequestContext(request)
            )

def new(request):
    form = forms.NewDocument(request.POST or None, auto_id=False)
    if form.is_valid():
        print form.cleaned_data
        result=db.save_doc(form.cleaned_data)
        if result['ok']:
            return message('Document Saved',
                           'The document "%s" has been saved' % result['id'] )
        else:
            return message('Error',
                           'Something went wrong while saving "%s"' % result['id'])

    return render_to_response('documents/new_form.html', 
                              { 'form': form, 'extra_data': {} },
                              context_instance=RequestContext(request))
                              

def view(request,_id):
    doc = db.get(_id)
    doc['id'] = doc['_id']
    doc['rev'] = doc['_rev']
    del doc['_id']
    del doc['_rev']
    return render_to_response('documents/view.html', 
                              { 'doc': doc, 'extra_data': {} })

def delete(request,_id):
    print _id
    result = db.delete_doc(_id)
    if result['ok']:
        return message('Document Deleted',
                       'Document "%s" has been deleted correctly' % _id)
    else:
        return message('Error',
                       'Error while deleting document "%s"' % _id)