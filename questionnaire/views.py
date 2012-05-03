from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
#from django.forms.formsets import formset_factory
import couchdbkit
from tender.utils import message
from questionnaire import forms
import pprint
import re

pp = pprint.PrettyPrinter(indent=4)

### Putting it here so it can be used by any form
db = couchdbkit.ext.django.loading.get_db('documents')

def questionnaire(request, doc_id):
    doc = db.get(doc_id)
    pattern = re.compile(r"sys(?P<sys>\d+)_sec(?P<sec>\d+)_q(?P<q>\d+)")


    if request.POST:
        form_data = doc.copy()
        form_data.update(request.POST)

        # Apparently each field ofthe data is enveloped in a list at this point.
        # Converting it back to the orinal format
        for f in form_data:
            match = pattern.match(str(f))
            if match:
                form_data[f] = form_data[f][0]

        form = forms.QSystemForm(form_data, doc=doc, auto_id=True)

        if form.is_valid():
#            pp.pprint(form.cleaned_data)
            # now there is to convert back the key sysX_secY_qZ to the respective entry
            for f in form.cleaned_data:
                match = pattern.match(str(f))
                if match:
                    sys = int(match.group('sys'))
                    sec = int(match.group('sec'))
                    q = int(match.group('q'))
                    doc['systems'][sys]['sections'][sec]['questions'][q]['answer'] = form.cleaned_data[f]

            result = db.save_doc(doc)
            if result['ok']:
                return HttpResponseRedirect(reverse('documents.views.validate', args=(doc_id, )))
            else:
                return message('Error',
                               'Something went wrong while saving "%s"' % doc_id)
    else:
        initial = {}
        systems = doc.get('systems',[])
        for sys in range(len(systems)):
            sections = systems[sys].get('sections',[])
            for sec in range(len(sections)):
                questions = sections[sec].get('questions', [])
                for q in range(len(questions)):
                    question = questions[q]
                    if question['answer'] or type(question['answer']) in [ int, float]:
                        initial['sys%d_sec%d_q%d' % (sys, sec, q)] = question['answer']
        form = forms.QSystemForm(initial=initial, doc=doc, auto_id=True)
        pp.pprint([form.data])

    doc['id'] = doc['_id']
    doc['rev'] = doc['_rev']
    # appending extra attributes to the form fields
    form_extra_data = {}
    for f in form:
        match = pattern.match(str(f.name))
        if match:
            sys = int(match.group('sys'))
            sec = int(match.group('sec'))
            q = int(match.group('q'))
            form_extra_data[f.name] = {
                'system': doc['systems'][sys]['name'],
                'section': doc['systems'][sys]['sections'][sec]['header']
                    }
        f.field.extra = form_extra_data[f.name]
        #pp.pprint(form_extra_data)

    return render_to_response('questionnaire/form.html',
                          {'form': form, 'doc': doc},
                          context_instance=RequestContext(request))

