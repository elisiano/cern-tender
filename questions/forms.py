from django import forms
from questions import models
from couchdbkit.ext.django.forms import DocumentForm
#from couchdbkit.ext.django import schema

from tender.utils import split_on_caps

class QuestionForm(forms.Form):
    question_type = forms.ChoiceField(
            choices=(
                (x, split_on_caps(x.replace("Question","",1))) for x in dir(models)
                    if (x.startswith('Question') and not x.endswith('Template')
            )))
    qfl_size = forms.IntegerField(label="Size of the list", min_value=0, initial=2)


class QuestionFormBase(DocumentForm):
    _id = forms.CharField(widget=forms.HiddenInput, required=False)
    _rev = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        if 'extra' in kwargs:
            kwargs.pop('extra')
        super(QuestionFormBase, self).__init__(*args, **kwargs)


class QuestionFromListForm(QuestionFormBase):

    qfl_size = forms.IntegerField(required=False)

    class Meta:
        document = models.QuestionFromList

    def __init__(self, *args, **kwargs):
        if 'extra' in kwargs:
            self.qfl_size = kwargs['extra']['qfl_size']
        super(QuestionFromListForm, self).__init__(*args, **kwargs)
        self.fields['tech_spec'].required = False

        for i in range(1, getattr(self,'qfl_size',0)+1):
           self.fields['answer_%s' % i] = forms.CharField(label='Answer %s' %i)
           self.fields['ts_%s' % i] = forms.CharField(label='Tech Spec %s' %i)


class QuestionIntegerRangeForm(QuestionFormBase):

    class Meta:
        document = models.QuestionIntegerRange

    def __init__(self, *args, **kwargs):
        super(QuestionIntegerRangeForm, self).__init__(*args, **kwargs)
        self.fields['tech_spec'].required = False

class QuestionFloatRangeForm(QuestionFormBase):

    class Meta:
        document = models.QuestionFloatRange

    def __init__(self, *args, **kwargs):
        super(QuestionFloatRangeForm, self).__init__(*args, **kwargs)
        self.fields['tech_spec'].required = False


class QuestionFreeTextForm(QuestionFormBase):

    class Meta:
        document = models.QuestionFreeText

    def __init__(self,*args, **kwargs):
        super(QuestionFreeTextForm, self).__init__(*args, **kwargs)
        self.fields['answer'].widget = forms.Textarea(attrs={'class':'ui-widget ui-corner-all','rows':10, 'cols':30})
