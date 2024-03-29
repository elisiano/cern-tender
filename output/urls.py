from django.conf.urls.defaults import patterns,  url

urlpatterns = patterns('output.views',
    url('questionnaire/pdf/(.*)', 'questionnaire_pdf'),
    url('questionnaire/xls/(.*)', 'questionnaire_xls'),
    url('document/pdf/(.*)', 'document_pdf'),
    url('document/docx/(.*)', 'document_docx'),
)