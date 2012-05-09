from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    #url(r'^$', 'tender.views.home', name='home'),
    url(r'^questions/', include('questions.urls')),
    url(r'^documents/', include('documents.urls')),
    url(r'^questionnaire/', include('questionnaire.urls')),
    url(r'^output/', include('output.urls')),
)

urlpatterns += staticfiles_urlpatterns()
