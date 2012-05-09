from django.conf.urls.defaults import patterns,  url

urlpatterns = patterns('output.views',
    url('questionnaire/pdf/(.*)', 'questionnaire_pdf'),
    url('document/pdf/(.*)', 'document_pdf'),
)