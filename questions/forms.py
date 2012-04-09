from django import forms
from questions import models
from couchdbkit.ext.django.forms import DocumentForm
from couchdbkit.ext.django import schema

class QuestionForm(forms.Form):
    question_type = forms.ChoiceField(
            choices=(
                (x, x) for x in dir(models)
                    if (x.startswith('Question') and not x.endswith('Template')
            )))
    qfl_size = forms.IntegerField(label="Size of the list (only for QuestionFromList)", min_value=0, initial=2)
    
        
class QuestionFormBase(DocumentForm):

    def __init__(self, *args, **kwargs):
        if 'extra' in kwargs:
            kwargs.pop('extra')
        super(QuestionFormBase, self).__init__(*args, **kwargs)

class QuestionFromListForm(QuestionFormBase):
    
    qfl_size = forms.IntegerField(required=False)

    class Meta:
        document = models.QuestionFromList

    def __init__(self, *args, **kwargs):
        print 'kwargs: ', kwargs
        self.qfl_size = kwargs.pop('extra')['qfl_size']
        super(QuestionFromListForm, self).__init__(*args, **kwargs)

        for i in range(1, self.qfl_size+1):
           self.fields['answer_%s' % i] = forms.CharField(label='Answer %s' %i)         
           self.fields['ts_%s' % i] = forms.CharField(label='Tech Spec %s' %i)         


class QuestionIntegerRangeForm(QuestionFormBase):

    class Meta:
        document = models.QuestionIntegerRange


class QuestionFloatRangeForm(QuestionFormBase):

    class Meta:
        document = models.QuestionFloatRange


class QuestionFreeTextForm(QuestionFormBase):

    class Meta:
        document = models.QuestionFreeText
