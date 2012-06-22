# Create your views here.
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
import couchdbkit
from documents import forms
from tender.utils import message
import pprint
from documents.classes import TenderDocumentValidator
import re

### Variables used along all the module
db = couchdbkit.ext.django.loading.get_db('documents')
pp = pprint.PrettyPrinter(indent=4)

##### Documents
def index(request):
    documents = db.all_docs()
    return render_to_response('documents/index.html',
                              {'documents': documents},
                                context_instance=RequestContext(request))


def new(request):
    form = forms.NewDocumentForm(request.POST or None, auto_id=False)
    if form.is_valid():
        result = db.save_doc(form.cleaned_data)
        if result['ok']:
            return message('Document Saved',
                           'The document "%s" has been saved' % result['id'])
        else:
            return message('Error',
                'Something went wrong while saving "%s"' % result['id'])

    return render_to_response('documents/new_form.html',
                              {'form': form, 'extra_data': {}},
                              context_instance=RequestContext(request))

def clone(request, doc_id):
    form = forms.NewDocumentForm(request.POST or None, auto_id=False)
    if form.is_valid():
        doc = db.get(doc_id)
        doc['_id'] = form.cleaned_data['_id']
        doc['cloned_from'] = doc_id
        doc['cloned_from_rev'] = doc['_rev']
        del doc['_rev']
        result = db.save_doc(doc)
        if result['ok']:
            ahref= reverse('documents.views.view', args=(result['id'],))

            return message('Document Saved',
                           'The document <a href="%s">%s</a> has been saved' % (ahref, result['id']))
        else:
            return message('Error',
                'Something went wrong while saving "%s"' % result['id'])

    return render_to_response('documents/new_form.html',
                              {'form': form, 'extra_data': {}},
                              context_instance=RequestContext(request))

def view(request, doc_id):
    doc = db.get(doc_id)
    doc['id'] = doc['_id']
    doc['rev'] = doc['_rev']
    del doc['_id']
    del doc['_rev']
    return render_to_response('documents/view.html',
                              {'doc': doc, 'extra_data': {}})


def delete(request, doc_id):
    result = db.delete_doc(doc_id)
    if result['ok']:
        return message('Document Deleted',
                       'Document "%s" has been deleted correctly' % doc_id)
    else:
        return message('Error',
                       'Error while deleting document "%s"' % doc_id)


def validate(request, doc_id):
    validator = TenderDocumentValidator(doc_id)
    result = validator.validate()

    if not result.get('errors',{}):
        ahref= reverse('documents.views.view', args=(doc_id,))
        return message('Document Validated!',
                       'Congratulations, <a href="%s">%s</a> passed validation!' % (ahref, doc_id))

    doc = db.get(doc_id)
    doc['id'] = doc['_id']
    doc['rev'] = doc['_rev']
    return render_to_response('documents/validate_errors.html',
                              {'errors': result['errors'], 'doc': doc},
                              context_instance=RequestContext(request))

def edit_document_root(request, doc_id):

    doc = db.get(doc_id)
    # just to make available the fields starting
    # with underscore in the template
    doc['id'] = doc['_id']
    doc['rev'] = doc['_rev']

    if request.POST:
        form = forms.EditDocumentRootForm(request.POST, auto_id=False)
        if form.is_valid():
            del doc['id']
            del doc['rev']
            doc['intro'] = form.cleaned_data['intro']
            doc['intro_header'] = form.cleaned_data['intro_header']
            doc['questionnaire_intro'] = form.cleaned_data['questionnaire_intro']
            doc['title'] = form.cleaned_data['title']
            # the systems must be reordered
            new_systems = []
            for i in range(0, len(doc.get('systems', []))):
                for s in doc['systems']:
                    if s['name'] == form.cleaned_data['system_%d' % i]:
                        new_systems.append(s)
                        break
            doc['systems'] = new_systems

            new_contacts = []
            for i in range(0, len(doc.get('contacts', []))):
                _ = form.cleaned_data['contact_%d' % i]
                pattern = re.compile(r' \(.*\)$')
                match = pattern.search(_)
                if match:
                    _ = _[:match.start()]

                for c in doc['contacts']:
                    print "teting '%s' == '%s'" % (_,c['name'])
                    if _ == c['name']:
                        print 'contact match'
                        new_contacts.append(c)
                        break
            doc['contacts'] = new_contacts

            result = db.save_doc(doc)
            #ahref = reverse('documents.views.view', args=(doc_id,))
            if result['ok']:
                return HttpResponseRedirect(reverse('documents.views.view', args=(doc_id, )))
                #return message('Document Updated',
                #               'The introduction part of <a href="%s">%s</a> has been updated correctly' % (ahref, doc_id))
            else:
                return message('Error',
                               'Error while updating document "%s"' % doc_id)

    else:
        data = doc
        for i in range(0, len(doc.get('systems', []))):
            data['system_%d' % i] = doc['systems'][i]['name']
        for i in range(0, len(doc.get('contacts',[]))):
            data['contact_%d' % i] = doc['contacts'][i]['name']
        form = forms.EditDocumentRootForm(data, auto_id=False)
    return render_to_response('documents/edit.html',
                            {'form': form, 'extra_data': {'doc': doc or None}},
                            context_instance=RequestContext(request))

##### Document > Contacts

def add_contact(request, doc_id):

    doc = db.get(doc_id)

    form = forms.ContactForm(request.POST or None)
    if form.is_valid():
        doc.setdefault('contacts',[]).append(form.cleaned_data)
        result = db.save_doc(doc)
        if result['ok']:
            return HttpResponseRedirect(reverse('documents.views.edit_document_root', args=(doc_id, )))
        else:
            return message('Error',
                               'Error while updating document "%s"' % doc_id)

    return render_to_response('documents/contact.html',
                              {'form': form},
                                context_instance=RequestContext(request))


def delete_contact(request, index, doc_id):
    doc = db.get(doc_id)
    idx = int(index)
    del doc['contacts'][idx]

    result = db.save_doc(doc)
    if result['ok']:
        return HttpResponseRedirect(reverse('documents.views.edit_document_root', args=(doc_id, )))
    else:
        return message('Error',
                           'Error while updating document "%s"' % doc_id)


def edit_contact(request, index, doc_id):
    doc = db.get(doc_id)
    idx = int(index)

    if request.POST:
        form = forms.ContactForm(request.POST)
        if form.is_valid():
            doc['contacts'][idx] = form.cleaned_data
            result = db.save_doc(doc)
            if result['ok']:
                return HttpResponseRedirect(reverse('documents.views.edit_document_root', args=(doc_id, )))
            else:
                return message('Error',
                               'Error while updating document "%s"' % doc_id)

    else:
        form = forms.ContactForm(initial=doc['contacts'][idx])

    return render_to_response('documents/contact.html',
                              {'form': form},
                                context_instance=RequestContext(request))


##### Document > Systems
def add_system(request, doc_id):
    doc = db.get(doc_id)
    if request.POST:
        form = forms.AddSystemForm(request.POST)
        if form.is_valid():
            # We don't want the system to have _id and _rev
            del form.cleaned_data['_id']
            del form.cleaned_data['_rev']
            if doc.get('systems', None):
                doc['systems'].append(form.cleaned_data)
            else:
                doc['systems'] = [form.cleaned_data, ]

            result = db.save_doc(doc)
            if result['ok']:
                return HttpResponseRedirect(reverse('documents.views.edit_document_root', args=(doc_id, )))
            else:
                return message('Error',
                               'Error adding system to "%s"' % doc_id)
    else:

        form = forms.AddSystemForm(initial=doc, auto_id=False)

    doc['id'] = doc['_id']
    return render_to_response('documents/add_system.html',
                            {'form': form, 'extra_data': {'doc': doc or None}},
                              context_instance=RequestContext(request))


def delete_system(request, index, doc_id):
    doc = db.get(doc_id)
    del doc['systems'][int(index)]
    result = db.save_doc(doc)
    if result['ok']:
        return HttpResponseRedirect(reverse('documents.views.edit_document_root', args=(doc_id,)))
    else:
        return message('Error',
                       'Error deleting system from "%s"' % doc_id)


def edit_system(request, system_idx, doc_id):
    doc = db.get(doc_id)
    doc['id'] = doc['_id']  # used in the header of the tepmplate
    sys_idx = int(system_idx)
    system = doc['systems'][sys_idx]

    if request.POST:
        form = forms.EditSystemForm(request.POST, auto_id=False)
        if form.is_valid():
            #pp.pprint(form.cleaned_data)
            ### Must convert back the system structure
            new_sections = []
            for section_idx in range(len(system.get('sections', []))):
                for section in system['sections']:
                    if section['header'] == form.data['section_%d' % section_idx]:
                        new_sections.append(section)
                        break
            doc['systems'][sys_idx]['sections'] = new_sections
            doc['systems'][sys_idx]['description'] = form.cleaned_data['description']
            rules=[]
            for line in form.cleaned_data['rules'].split('\n'):
                line = line.strip('\r\n')
                if line:
                    rules.append(line)
            #print "Converted rules:", pp.pprint(rules)
            doc['systems'][sys_idx]['rules'] = rules

            result = db.save_doc(doc)
            if result['ok']:
                return HttpResponseRedirect(reverse('documents.views.edit_document_root', args=(doc_id, )))
            else:
                return message('Error',
                               'Error editing system from "%s"' % doc_id)

    else:
        for section in range(len(system.get('sections', []))):
            system['section_%d' % section] = system['sections'][section]['header']

        if system.get('rules', None):
            system['rules'] = "\r\n\r\n".join(system['rules'])
        else:
            ### to avoid having an empty list displayed
            try:
                del system['rules']
            except KeyError:
                pass
        form = forms.EditSystemForm(system, auto_id=False)

    system['index'] = int(system_idx)
    return render_to_response('documents/edit_system.html',
                              {'form': form, 'extra_data': {'system': system, 'doc': doc}},
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
                return HttpResponseRedirect(reverse('documents.views.edit_system', args=(system_idx, doc_id)))
            else:
                return message('Error','Error adding a section to a system in "%s"' % doc_id)

    else:
        form_data = {'system': system}
        form = forms.AddSystemSectionForm(initial=form_data, auto_id=False)

    doc['id'] = doc['_id']
    return render_to_response('documents/add_system_section.html',
                              {'form': form, 'extra_data': {'system': system, 'doc': doc}},
                              context_instance=RequestContext(request))


def edit_system_section(request, section_idx, system_idx, doc_id):
    doc = db.get(doc_id)
    sys = int(system_idx)
    sec = int(section_idx)
    section = doc['systems'][sys]['sections'][sec]

    if request.POST:
        form = forms.EditSystemSectionForm(request.POST, auto_id=False)
        if form.is_valid():
            new_questions = []
            for i in range(len(section.get('questions', []))):
                for q in section['questions']:
                    if q['question'] == form.data['question_%d' % i]:
                        new_questions.append(q)
            doc['systems'][sys]['sections'][sec]['questions'] = new_questions
            doc['systems'][sys]['sections'][sec]['description'] = form.cleaned_data['description']

            result = db.save_doc(doc)
            if result['ok']:
                return HttpResponseRedirect(reverse('documents.views.edit_system', args=(system_idx, doc_id)))
            else:
                return message('Error', 'Error saving section of a system in "%s"' % doc_id)

    else:
        for i in range(len(section.get('questions', []))):
            section['question_%d' % i] = section['questions'][i]['question']

        form = forms.EditSystemSectionForm(section, auto_id=False)

    doc['id'] = doc['_id']
    section['index'] = int(section_idx)
    return render_to_response('documents/edit_system_section.html',
                              {'form': form,
                               'extra_data':
                                   {'section': section,
                                    'system': {'index': int(system_idx)},
                                    'doc': doc}
                               },
                              context_instance=RequestContext(request))


def delete_system_section(request, section_idx, system_idx, doc_id):
    doc = db.get(doc_id)
    del doc['systems'][int(system_idx)]['sections'][int(section_idx)]
    result = db.save_doc(doc)
    if result['ok']:
        return HttpResponseRedirect(reverse('documents.views.edit_system', args=(system_idx, doc_id)))
    else:
        return message('Error', 'Error adding a section to a system in "%s"' % doc_id)


##### Document > System > Section > Questions
def add_system_section_question(request, section_idx, system_idx, doc_id):
    questions_db = couchdbkit.ext.django.loading.get_db('questions')
    sys = int(system_idx)
    sec = int(section_idx)
    section_questions = [q['question'] for q in db.get(doc_id)['systems'][sys]['sections'][sec].get('questions', [])]


    question_list = questions_db.view('questions/by_category')
    choices_dict = {}
    for q in question_list:
        v = q['value']
        if not v['category'] in choices_dict:
            choices_dict[v['category']] = []
        choices_dict[v['category']].append((v['_id'], v['question']))

    _ = []
    for k in choices_dict:
        _.append((k, tuple(sorted(choices_dict[k], key=lambda x: x[1]))))
    choices = tuple(_)
    data = {}
    data['section_questions'] = section_questions
    data['choices'] = choices

    if request.POST:
        data.update(request.POST.copy())

        form = forms.AddSystemSectionQuestionForm(data, auto_id=False)
        if form.is_valid():
            # The form is clean, at this point we retrieve the question from
            # the catalog and we remove the extra bits
            q = questions_db.get(form.cleaned_data['choice'])
            del q['_id']
            del q['_rev']
            doc = db.get(doc_id)
            doc['systems'][sys]['sections'][sec].setdefault('questions', []).append(q)
            result = db.save_doc(doc)
            if result['ok']:
                return HttpResponseRedirect(reverse('documents.views.edit_system_section', args=(section_idx, system_idx, doc_id)))
            else:
                return message('Error', 'Error adding the selected question to "%s"' % doc_id)
    else:

        form = forms.AddSystemSectionQuestionForm(initial=data, auto_id=False)

    return render_to_response('documents/add_system_section_question.html',
                              {'form': form, 'extra_data': {}},
                              context_instance=RequestContext(request))


def edit_system_section_question(request, question_idx, section_idx, system_idx, doc_id):
    sys = int(system_idx)
    sec = int(section_idx)
    qid = int(question_idx)
    doc = db.get(doc_id)

    question = doc['systems'][sys]['sections'][sec]['questions'][qid]
    
    # used to check the question validity in the form (i.e. no duplicates) when modifying the question itself
    question['from_doc'] = doc_id 
    question['from_sys'] = sys
    question['from_sec'] = sec
    question['from_qid'] = qid

    if request.POST:
        # now the we remove the previously added fields
        data = dict(request.POST)
        data['from_doc'] = doc_id 
        data['from_sys'] = sys
        data['from_sec'] = sec
        data['from_qid'] = qid

        form = forms.EditSystemSectionQuestionForm(data, auto_id=True)
        
        if form.is_valid():
            pp.pprint(form.cleaned_data)
            try:
                del data['from_doc']
                del data['from_sys']
                del data['from_sec']
                del data['from_qid']
            except Exception:
                pass
            
            question = form.cleaned_data
            if question['doc_type'] == 'QuestionFromList':
                i = 1
                while question.get('answer_%d' % i, None):
                    question.setdefault('answer_data',{})[question['answer_%d' % i]] = question['tech_spec_%d' % i]
                    del question['answer_%d' % i]
                    del question['tech_spec_%d' % i]
                    i+=1

            doc['systems'][sys]['sections'][sec]['questions'][qid] = question
            result = db.save_doc(doc)
            if result['ok']:
                return HttpResponseRedirect(reverse('documents.views.edit_system_section', args=(section_idx, system_idx, doc_id)))
            else:
                return message('Error', 'Error editing selected question in "%s"' % doc_id)
    else:

        if question['doc_type'] == "QuestionFromList":
            for _t in enumerate(question['answer_data'],1):
                question['answer_%d' % _t[0]] = _t[1]
                question['tech_spec_%d' % _t[0]] = question['answer_data'][_t[1]]
            del question['answer_data']
            
        form = forms.EditSystemSectionQuestionForm(initial=question, auto_id=True)

    return render_to_response('documents/edit_system_section_question.html',
                             {'form': form, 'question': question},
                                context_instance=RequestContext(request))


def delete_system_section_question(request, question_idx, section_idx, system_idx, doc_id):
    doc = db.get(doc_id)
    sys = int(system_idx)
    sec = int(section_idx)
    del doc['systems'][sys]['sections'][sec]['questions'][int(question_idx)]
    result = db.save_doc(doc)
    if result['ok']:
        return HttpResponseRedirect(reverse('documents.views.edit_system_section', args=(section_idx, system_idx, doc_id)))
    else:
        return message('Error', 'Error deleting the selected question from "%s"' % doc_id)
