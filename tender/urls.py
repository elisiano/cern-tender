from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    #url(r'^$', 'tender.views.home', name='home'),
    url(r'^questions/', include('questions.urls')),
)
