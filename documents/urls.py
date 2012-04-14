# -*- coding: utf-8 -*-

from django.conf.urls.defaults import patterns,  url

urlpatterns = patterns('documents.views',
    url('^new/$', 'new'),
    url('^edit/([^/]+)', 'editDocRoot'),
    url('^delete/([^/]+)', 'delete'),
    url('^clone/([^/]+)', 'clone'),
    url('^$', 'list'),
)