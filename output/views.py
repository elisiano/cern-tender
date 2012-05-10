# Create your views here.
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
import couchdbkit
from tender.utils import message
import utils
import pprint
from django.template.defaultfilters import slugify

### Variables used along all the module
db = couchdbkit.ext.django.loading.get_db('documents')
pp = pprint.PrettyPrinter(indent=4)

def questionnaire_pdf(request, doc_id):
    doc = None
    try:
        doc = db.get(doc_id)
    except Exception, e:
        return message('Error','Error getting document %s: %s' % (doc_id, e))
    pp.pprint(request.GET)
    response = HttpResponse(mimetype='application/pdf')
    import re
    filename=doc_id
    pattern = re.compile(r'[:|\/";\?]')
    for s in pattern.findall(filename):
        filename = filename.replace(s, '-')

    response['Content-Disposition'] = 'filename=%s-techq.pdf' % filename

    start_idx = request.GET.get('start_index',1)
    pdf = utils.get_questionnaire_pdf(response, doc_id, int(start_idx))
    return response

def document_pdf(request, doc_id):
    pass
