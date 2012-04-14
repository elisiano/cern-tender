# Create your views here.
from django.shortcuts import render_to_response
from django.template import RequestContext
import couchdbkit

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
    pass
