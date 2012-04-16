# -*- coding: utf-8 -*-

from django.conf.urls.defaults import patterns,  url

urlpatterns = patterns('documents.views',
    url('^new/$', 'new'),
    url('^view/(.*)', 'view'),
    url('^edit/(.*)', 'edit_document_root'),
    url('^delete/(.*)', 'delete'),
    url('^addsystem/(.*)', 'add_system'),
    url('^deletesystem/(\d+)/(.*)', 'delete_system'),
    url('^editystem/(\d+)/(.*)', 'edit_system'),
#    url('^clone/(.*)', 'clone'),
    url('^$', 'index'),
)