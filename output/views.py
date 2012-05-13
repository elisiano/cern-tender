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
import re

### Variables used along all the module
db = couchdbkit.ext.django.loading.get_db('documents')
pp = pprint.PrettyPrinter(indent=4)


def _clean_filename(string):
    filename = string
    pattern = re.compile(r'[:|\/";\?]')
    for s in pattern.findall(filename):
        filename = filename.replace(s, '-')

    return filename

def questionnaire_pdf(request, doc_id):
    doc = None
    try:
        doc = db.get(doc_id)
    except Exception, e:
        return message('Error','Error getting document %s: %s' % (doc_id, e))

    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'filename=%s-techq.pdf' % _clean_filename(doc_id)

    start_idx = request.GET.get('start_index',1)
    pdf = utils.get_questionnaire_pdf(response, doc_id, int(start_idx))
    return response

def document_pdf(request, doc_id):
    doc = None
    try:
        doc = db.get(doc_id)
    except Exception, e:
        return message('Error','Error getting document %s: %s' % (doc_id, e))

    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'filename=%s.pdf' % _clean_filename(doc_id)

    start_idx = request.GET.get('start_index',1)
    pdf = utils.get_document_pdf(response, doc_id, int(start_idx))
    return response