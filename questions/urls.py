from django.conf.urls.defaults import patterns,  url

urlpatterns = patterns('questions.views',
    url('^new/$', 'qtype'),
    url('^create/([^/]+)/(.*)', 'qcreate'),
    url('^edit/([^/]+)', 'edit'),
    url('^delete/([^/]+)', 'delete'),
    url('^clone/([^/]+)', 'clone'),
    url('^$', 'index'),
)
