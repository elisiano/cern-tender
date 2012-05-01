from django.conf.urls.defaults import patterns,  url

urlpatterns = patterns('questionnaire.views',
    url('^(.*)', 'questionnaire')
)
