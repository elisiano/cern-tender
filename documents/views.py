# Create your views here.
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
import couchdbkit
from documents import forms
from tender.utils import message


db = couchdbkit.ext.django.loading.get_db('documents')

def index(request):
    documents = db.all_docs()
    #for k in documents:
    #    print "k: ", k, "v: ",documents[k]
    return render_to_response(  'documents/index.html',
            { 'documents':documents },
            context_instance=RequestContext(request)
            )

def new(request):
    form = forms.NewDocumentForm(request.POST or None, auto_id=False)
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

def delete(request,doc_id):
    #print _id
    result = db.delete_doc(doc_id)
    if result['ok']:
        return message('Document Deleted',
                       'Document "%s" has been deleted correctly' % doc_id)
    else:
        return message('Error',
                       'Error while deleting document "%s"' % doc_id)
                       
def edit_document_root(request,doc_id):

    doc = db.get(doc_id)
    # just to make available the fields starting with underscore in the template
    doc['id'] = doc['_id']
    doc['rev'] = doc['_rev']
    form = forms.EditDocumentRootForm(doc,auto_id=False) 
    if request.POST:
        form = forms.EditDocumentRootForm(request.POST,auto_id=False)
        
        if form.is_valid():
            del doc['id']
            del doc['rev']
            doc['intro'] = form.cleaned_data['intro']
            result = db.save_doc(doc)
            ahref = reverse('documents.views.view', args=(doc_id,))
            if result['ok']:
                return message('Document Updated',
                               'The introduction part of <a href="%s">%s</a> has been updated correctly' % (ahref, doc_id))
            else:
                return message('Error',
                               'Error while updating document "%s"' % doc_id)


    #print doc
    return render_to_response('documents/edit.html', 
                              { 'form': form, 'extra_data': {'doc':doc or None} },
                              context_instance=RequestContext(request))
                  

def add_system(request,doc_id):
    doc=db.get(doc_id)
    if request.POST:
        form = forms.AddSystemForm(request.POST)
        if form.is_valid():
            # We don't want the system to have _id and _rev
            del form.cleaned_data['_id']
            del form.cleaned_data['_rev']
            if doc.get('systems',None):
                doc['systems'].append(form.cleaned_data)
            else:
                doc['systems'] = [form.cleaned_data,]
            
            result = db.save_doc(doc)
            if result['ok']:
                return HttpResponseRedirect(reverse('documents.views.edit_document_root', args=(doc_id,)))
            else:
                return message('Error',
                               'Error adding system to "%s"' % doc_id)
    else:
        form = forms.AddSystemForm(doc,auto_id=False)
                               
    return render_to_response('documents/add_system.html',
                              {'form':form, 'extra_data':{'doc':doc or None}},
                              context_instance=RequestContext(request))
                              
def delete_system(request, index, doc_id):
    doc=db.get(doc_id)
    del doc['systems'][int(index)]
    result = db.save_doc(doc)
    if result['ok']:
        return HttpResponseRedirect(reverse('documents.views.edit_document_root', args=(doc_id,)))
    else:
        return message('Error',
                       'Error adding system to "%s"' % doc_id)
