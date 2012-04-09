from django.conf.urls.defaults import patterns,  url

urlpatterns = patterns('questions.views',
    url('^new/$', 'qtype'),
    url('^create/([^/]+)/(.*)', 'qcreate'),
    #url('^edit/(.*)/$', 'edit'),
    url('^$', 'list'),
)
