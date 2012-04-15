# -*- coding: utf-8 -*-

from django.conf.urls.defaults import patterns,  url

urlpatterns = patterns('documents.views',
    url('^new/$', 'new'),
    url('^view/(.*)', 'view'),
    url('^edit/(.*)', 'edit_document_root'),
#    url('editsystem/(\d+)/(.*)', 'edit_system'),
    url('^addsystem/(.*)', 'add_system'),
    url('^deletesystem/(\d+)/(.*)', 'delete_system'),
    url('^delete/(.*)', 'delete'),
#    url('^clone/(.*)', 'clone'),
    url('^$', 'index'),
)