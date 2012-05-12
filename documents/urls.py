# -*- coding: utf-8 -*-

from django.conf.urls.defaults import patterns,  url

urlpatterns = patterns('documents.views',
    url('^new/$', 'new'),
    url('^view/(.*)', 'view'),
    url('^edit/(.*)', 'edit_document_root'),
    url('^delete/(.*)', 'delete'),
    url('^validate/(.*)', 'validate'),
    url('^addcontct/(.*)', 'add_contact'),
    url('^deletecontact/(\d+)/(.*)', 'delete_contact'),
    url('^editcontact/(\d+)/(.*)', 'edit_contact'),
    url('^addsystem/(.*)', 'add_system'),
    url('^deletesystem/(\d+)/(.*)', 'delete_system'),
    url('^editsystem/(\d+)/(.*)', 'edit_system'),
    url('^addsystemsection/(\d+)/(.*)', 'add_system_section'),
    url('^deletesystemsection/(\d+)/(\d+)/(.*)', 'delete_system_section'),
    url('^editsystemsection/(\d+)/(\d+)/(.*)', 'edit_system_section'),
    url('^addsystemsectionquestion/(\d+)/(\d+)/(.*)', 'add_system_section_question'),
    url('^editsystemsectionquestion/(\d+)/(\d+)/(\d+)/(.*)', 'edit_system_section_question'),
    url('^deletesystemsectionquestion/(\d+)/(\d+)/(\d+)/(.*)', 'delete_system_section_question'),
    url('^$', 'index'),
)