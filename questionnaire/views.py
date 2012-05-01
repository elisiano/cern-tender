from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.forms.formsets import formset_factory
import couchdbkit

from questionnaire import forms
import pprint
pp = pprint.PrettyPrinter(indent=4)

### Putting it here so it can be used by any form
db = couchdbkit.ext.django.loading.get_db('documents')

def questionnaire(request, doc_id):
    doc = db.get(doc_id)

    if request.POST:
        form_data = doc.copy()
        form_data.update(request.POST)
        form = forms.QSystemForm(form_data, auto_id=True)
#        print "Data: ",
#        pp.pprint(form.data)
        if form.is_valid():
#            pp.pprint(form.cleaned_data)
            return HttpResponse('Form is valid')
    else:
        form = forms.QSystemForm(initial=doc, auto_id=True)
        pp.pprint([form.data])

    doc['id'] = doc['_id']
    doc['rev'] = doc['_rev']
    return render_to_response('questionnaire/form.html',
                          {'form': form, 'doc': doc},
                          context_instance=RequestContext(request))

