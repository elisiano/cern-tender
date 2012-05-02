from django import forms
import couchdbkit

### Putting it here so it can be used by any form
db = couchdbkit.ext.django.loading.get_db('documents')

import pprint
pp = pprint.PrettyPrinter(indent=4)


def get_form_field(question):
    label = question['question']
    if question['doc_type'] == 'QuestionFromList':
        choices = tuple((k,k) for k in question['answer_data'])
        return forms.CharField(widget=forms.Select(choices=choices), label=label)

    elif question['doc_type'] == 'QuestionIntegerRange':
        label+=' [min=%s, max=%s]' % (question['min_'], question['max_'])
        initial = question.get('answer', None)
        field = forms.FloatField(label=label, initial=initial)
        min_ = int(question['min_'])
        max_ = int(question['max_'])
        field = forms.IntegerField(label=label, min_value=min_, max_value=max_ )
        #pp.pprint(dir(field))
        return field

    elif question['doc_type'] == 'QuestionFloatRange':
        label+=' [min=%s, max=%s]' % (question['min_'], question['max_'])
        initial = question.get('answer', None)
        field = forms.FloatField(label=label, initial=initial)
        field.min_value = float(question['min_'])
        field.max_value = float(question['max_'])
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

        print "Data: :",
        pp.pprint(self.data)
        for sys in range(len(self.s_data.get('systems', []))):
            for sec in range(len(self.s_data['systems'][sys].get('sections', []))):
                for q in range(len(self.s_data['systems'][sys]['sections'][sec].get('questions',[]))):
                    self.fields['sys%d_sec%d_q%d' % (sys, sec, q)] = get_form_field(self.s_data['systems'][sys]['sections'][sec]['questions'][q])
