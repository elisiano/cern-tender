# Create your views here.
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
import couchdbkit
from documents import forms
from tender.utils import message


db = couchdbkit.ext.django.loading.get_db('documents')



##### Documents

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

    if request.POST:
        form = forms.EditDocumentRootForm(request.POST,auto_id=False)

        if form.is_valid():
            del doc['id']
            del doc['rev']
            doc['intro'] = form.cleaned_data['intro']
            # the systems must be reordered
            print "cleaned_data: ",form.cleaned_data
            new_systems = []
            for i in range(0,len(doc.get('systems',[]))):
                for s in doc['systems']:
                    if s['name'] == form.cleaned_data['system_%d' % i]:
                        new_systems.append(s)
                        break
            doc['systems'] = new_systems
            #return HttpResponse('Not saved yet')
            result = db.save_doc(doc)
            ahref = reverse('documents.views.view', args=(doc_id,))
            if result['ok']:
                return message('Document Updated',
                               'The introduction part of <a href="%s">%s</a> has been updated correctly' % (ahref, doc_id))
            else:
                return message('Error',
                               'Error while updating document "%s"' % doc_id)

    else:
        data = doc
        for i in range(0,len(doc.get('systems',[]))):
            data['system_%d' % i] = doc['systems'][i]['name']
        form = forms.EditDocumentRootForm(data,auto_id=False)
    #print doc
    return render_to_response('documents/edit.html',
                              { 'form': form, 'extra_data': {'doc':doc or None} },
                              context_instance=RequestContext(request))

##### Document > Systems
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

        form = forms.AddSystemForm(initial=doc,auto_id=False)

    doc['id'] = doc['_id']
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
                       'Error deleting system from "%s"' % doc_id)

def edit_system(request, system_idx, doc_id):
    doc = db.get(doc_id)
    doc['id']=doc['_id'] # used in the header of the tepmplate
    system = doc['systems'][int(system_idx)]


    if request.POST:
        form = forms.EditSystemForm(request.POST,auto_id=False)
        if form.is_valid():
            print "Valid Form: ", form.cleaned_data
            print "Form data:",form.data
            ### Must convert back the system structure
            new_sections=[]
            for section_idx in range(len(system.get('sections',[]))):
                for section in system['sections']:
                    if section['header'] == form.data['section_%d' % section_idx]:
                        new_sections.append(section)
                        break
            doc['systems'][int(system_idx)]['sections'] = new_sections
            result = db.save_doc(doc)
            if result['ok']:
                return HttpResponseRedirect(reverse('documents.views.edit_document_root', args=(doc_id,)))
            else:
                return message('Error',
                               'Error editing system from "%s"' % doc_id)

    else:
        for section in range(len(system.get('sections',[]))):
            system['section_%d' % section] = system['sections'][section]['header']
        form = forms.EditSystemForm(system,auto_id=False)

    system['index']=int(system_idx)
    return render_to_response('documents/edit_system.html',
                              {'form': form, 'extra_data': {'system':system, 'doc': doc}},
                              context_instance=RequestContext(request))

##### Document > System > Sections
def add_system_section(request,system_idx, doc_id):

    doc = db.get(doc_id)
    system = doc['systems'][int(system_idx)]

    if request.POST:
        form_data = request.POST.copy()
        form_data['system'] = system
        form = forms.AddSystemSectionForm(form_data, auto_id=False)
        if form.is_valid():
            doc['systems'][int(system_idx)].setdefault('sections',[]).append(form.cleaned_data)
            result = db.save_doc(doc)
            if result['ok']:
                return HttpResponseRedirect(reverse('documents.views.edit_system', args=(system_idx,doc_id)))
            else:
                return message('Error','Error adding a section to a system in "%s"' % doc_id)

    else:
        form_data = {'system': system}
        form = forms.AddSystemSectionForm(initial=form_data, auto_id=False)

    doc['id'] = doc['_id']
    return render_to_response('documents/add_system_section.html',
                              {'form': form, 'extra_data': {'system':system, 'doc': doc}},
                              context_instance=RequestContext(request))

def edit_system_section(request, section_idx, system_idx, doc_id):
    doc = db.get(doc_id)
    section=doc['systems'][int(system_idx)]['sections'][int(section_idx)]

    if request.POST:
        form = forms.EditSystemSectionForm(request.POST,auto_id=False)
        if form.is_valid():
            print "form cleaned", form.cleaned_data
            print "form data", form.data
            return HttpResponse('Form is valid')

    else:
        for i in range(len(section.get('questions',[]))):
            section['question_%d' % i] = section['questions'][i]['question']

        form = forms.EditSystemSectionForm(section, auto_id=False)

    doc['id'] = doc['_id']
    section['index'] = int(section_idx)
    return render_to_response('documents/edit_system_section.html',
                              {'form': form,
                               'extra_data':
                                   {'section':section,
                                    'system': { 'index': int(system_idx) },
                                    'doc': doc}
                               },
                              context_instance=RequestContext(request))

def delete_system_section(request, section_idx, system_idx, doc_id):
    doc = db.get(doc_id)
    del doc['systems'][int(system_idx)]['sections'][int(section_idx)]
    result = db.save_doc(doc)
    if result['ok']:
        return HttpResponseRedirect(reverse('documents.views.edit_system', args=(system_idx,doc_id)))
    else:
        return message('Error','Error adding a section to a system in "%s"' % doc_id)


##### Document > System > Section > Questions
def add_system_section_question(request, section_idx, system_idx, doc_id):
    return HttpResponse('Work in progress')

def edit_system_section_question(request, question_idx, section_idx, system_idx, doc_id):
    return HttpResponse('Work in progress')

def delete_system_section_question(request, question_idx, section_idx, system_idx, doc_id):
    return HttpResponse('Work in progress')
