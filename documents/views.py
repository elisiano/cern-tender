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
    return render_to_response('documents/index.html',
                              {'documents': documents},
                                context_instance=RequestContext(request))


def new(request):
    form = forms.NewDocumentForm(request.POST or None, auto_id=False)
    if form.is_valid():
        print form.cleaned_data
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


def view(request, doc_id):
    doc = db.get(doc_id)
    doc['id'] = doc['_id']
    doc['rev'] = doc['_rev']
    del doc['_id']
    del doc['_rev']
    return render_to_response('documents/view.html',
                              {'doc': doc, 'extra_data': {}})


def delete(request, doc_id):
    #print _id
    result = db.delete_doc(doc_id)
    if result['ok']:
        return message('Document Deleted',
                       'Document "%s" has been deleted correctly' % doc_id)
    else:
        return message('Error',
                       'Error while deleting document "%s"' % doc_id)


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
            # the systems must be reordered
            print "cleaned_data: ", form.cleaned_data
            new_systems = []
            for i in range(0, len(doc.get('systems', []))):
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
        for i in range(0, len(doc.get('systems', []))):
            data['system_%d' % i] = doc['systems'][i]['name']
        form = forms.EditDocumentRootForm(data, auto_id=False)
    #print doc
    return render_to_response('documents/edit.html',
                            {'form': form, 'extra_data': {'doc': doc or None}},
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
    system = doc['systems'][int(system_idx)]

    if request.POST:
        form = forms.EditSystemForm(request.POST, auto_id=False)
        if form.is_valid():
            print "Valid Form: ", form.cleaned_data
            print "Form data:", form.data
            ### Must convert back the system structure
            new_sections = []
            for section_idx in range(len(system.get('sections', []))):
                for section in system['sections']:
                    if section['header'] == form.data['section_%d' % section_idx]:
                        new_sections.append(section)
                        break
            doc['systems'][int(system_idx)]['sections'] = new_sections
            result = db.save_doc(doc)
            if result['ok']:
                return HttpResponseRedirect(reverse('documents.views.edit_document_root', args=(doc_id, )))
            else:
                return message('Error',
                               'Error editing system from "%s"' % doc_id)

    else:
        for section in range(len(system.get('sections', []))):
            system['section_%d' % section] = system['sections'][section]['header']
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

    print "Section:", section
    if request.POST:
        form = forms.EditSystemSectionForm(request.POST, auto_id=False)
        if form.is_valid():
            print "form cleaned", form.cleaned_data
            print "form data", form.data
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
    print "Section Questions:", section_questions
    print "ASSQ POST:", request.POST

    question_list = questions_db.view('questions/by_category')
    choices_dict = {}
    for q in question_list:
        v = q['value']
        if not v['category'] in choices_dict:
            choices_dict[v['category']] = []
        choices_dict[v['category']].append((v['_id'], v['question']))

    _ = []
    #print choices_dict
    for k in choices_dict:
        #print k, "==>", tuple(choices_dict[k])
        _.append((k, tuple(sorted(choices_dict[k], key=lambda x: x[1]))))
    choices = tuple(_)
    data = {}
    data['section_questions'] = section_questions
    data['choices'] = choices

    if request.POST:
        data.update(request.POST.copy())

        form = forms.AddSystemSectionQuestionForm(data, auto_id=False)
        if form.is_valid():
            print "Add Question Form:", form.cleaned_data
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

    if request.POST:
        form = forms.EditSystemSectionQuestionForm(request.POST, auto_id=True)
        if form.is_valid():
            print "Cleaned", form.cleaned_data
            print "Data", form.data
            question = form.cleaned_data
            if question['doc_type'] == 'QuestionFromList':
                i = 1
                while question.get('answer_%d' % i, None):
                    print "converting attribute"
                    question.setdefault('answer_data',{})[question['answer_%d' % i]] = question['tech_spec_%d' % i]
                    del question['answer_%d' % i]
                    del question['tech_spec_%d' % i]
                    i+=1

            print "New Question: ", question
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
            print "Mangled Question:", question
        form = forms.EditSystemSectionQuestionForm(question, auto_id=True)

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