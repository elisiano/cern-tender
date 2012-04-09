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
    qfl_size = forms.CharField(label="Size of the list (only for QuestionFromList)", max_length=5, initial="2")
    
    def clean_qfl_size(self):
        qfl_size = self.cleaned_data.get('qfl_size',0)
        try:
            qfl_size=int(qfl_size)

        except Exception:            
            forms.ValidationError("This field must be an integer")

        if qfl_size < 0:
            forms.ValidationError("This field must be a positive integer")

        return qfl_size
        
class QuestionFromListForm(DocumentForm):
    
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


class QuestionIntegerRangeForm(DocumentForm):

    class Meta:
        document = models.QuestionIntegerRange


class QuestionFloatRangeForm(DocumentForm):

    class Meta:
        document = models.QuestionFloatRange


class QuestionFreeTextForm(DocumentForm):

    class Meta:
        document = models.QuestionFreeText
