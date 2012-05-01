from django import forms
import couchdbkit

### Putting it here so it can be used by any form
db = couchdbkit.ext.django.loading.get_db('documents')

import pprint
pp = pprint.PrettyPrinter(indent=4)

#class BaseQuestionForm(forms.Form):
#    doc_type = forms.CharField(widget=forms.HiddenInput())
#    question = forms.CharField(widget=forms.HiddenInput())
#    answer = forms.CharField()
#
#    def __init__(self, *args, **kwargs):
#        super(BaseQuestionForm, self).__init__(*args, **kwargs)
#        if kwargs.get('initial',None):
#            self.q_data = kwargs['initial']
#        else:
#            self.q_data = args[0]
#
#        self.fields['answer'] = forms.CharField(label=self.q_data.get('question', None))
#
#    def clean_answer(self):
#        QuestionModel = getattr(questions.models,self.q_data['doc_type'])
#        self.q_data['answer'] = self.cleaned_data['answer']
#        try:
#            q = QuestionModel(self.q_data)
#            q.validate()
#        except Exception, e:
#            raise forms.ValidationError('Error Validating Question: ', e)
#
#        return self.cleaned_data['answer']
#
#
#class QuestionFromListForm(BaseQuestionForm):
#
#    def __init__(self, *args, **kwargs):
#        super(QuestionFromListForm, self).__init__(*args, **kwargs)
#        choices = tuple((k,k) for k in self.q_data['answer_data'])
#        self.fields['answer'].widget = forms.CharField(widget=forms.Select(choices=choices))
#
#
#
#class BaseRangeQuestionForm(BaseQuestionForm):
#
#    def __init__(self, *args, **kwargs):
#        super(BaseRangeQuestionForm, self).__init__(*args, **kwargs)
#        self.fields['answer'].label += "[ min: %s, max: %s ]" % (self.q_data['min_'], self.q_data['max_'])
#
#class  QuestionIntegerRangeForm(BaseRangeQuestionForm):
#    pass
#
#class QuestionFloatRangeForm(BaseRangeQuestionForm):
#    pass
#
#class QuestionFreeTextForm(BaseQuestionForm):
#    pass

#class QSectionForm(forms.Form):
#
#    def __init__(self, *args, **kwargs):
#        super(QSectionForm, self).__init__(*args, **kwargs)
#        if kwargs.get('initial',None):
#            self.s_data = kwargs['initial']
#        else:
#            self.s_data = args[0]
#
#        for i in range(len(self.s_data['questions'])):
#            self.fields['question_%d' % i] = get_form_field(self.s_data['questions'][i])

def get_form_field(question):
    label = question['question']
    if question['doc_type'] == 'QuestionFromList':
        choices = tuple((k,k) for k in question['answer_data'])
        return forms.CharField(widget=forms.Select(choices=choices), label=label)

    elif question['doc_type'] == 'QuestionIntegerRange':
        label+=' [min=%s, max=%s]' % (question['min_'], question['max_'])
        min_ = question['min_']
        max_ = question['max_']
        field = forms.IntegerField(label=label, min_value=min_, max_value=max_ )
        #pp.pprint(dir(field))
        return field

    elif question['doc_type'] == 'QuestionFloatRange':
        label+=' [min=%s, max=%s]' % (question['min_'], question['max_'])
        field = forms.FloatField(label=label)
        field.min_value = question['min_']
        field.max_value = question['max_']
        return field

    else:
        return forms.CharField(label=label)



class QSystemForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(QSystemForm, self).__init__(*args, **kwargs)
        if kwargs.get('initial',None):
            self.s_data = kwargs['initial']
            print"initial self.s_data: ",
            pp.pprint(self.s_data)
        else:
            self.s_data = args[0]
            print"bond self.s_data: ",
            pp.pprint(self.s_data)

        for sys in range(len(self.s_data.get('systems', []))):
            for sec in range(len(self.s_data['systems'][sys].get('sections', []))):
                for q in range(len(self.s_data['systems'][sys]['sections'][sec].get('questions',[]))):
                    self.fields['sys%d_sec%d_q%d' % (sys, sec, q)] = get_form_field(self.s_data['systems'][sys]['sections'][sec]['questions'][q])
