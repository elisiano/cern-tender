from django import forms
import couchdbkit

### Putting it here so it can be used by any form
db = couchdbkit.ext.django.loading.get_db('documents')

class DocBaseForm(forms.Form):
    # By default _id and _rev are hidden (because are taken from the db), except at
    # creation time: _rev must be removed and _id must be editable (done in the
    # constructor of NewDocumentForm)
    _id = forms.CharField(label="Document ID",widget=forms.HiddenInput())
    _rev = forms.CharField(label="Revision", required=False, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super(DocBaseForm, self).__init__(*args, **kwargs)


class NewDocumentForm(DocBaseForm):

    def __init__(self, *args, **kwargs):
        super(NewDocumentForm, self).__init__(*args, **kwargs)
        self.fields['_id'].widget = forms.widgets.TextInput()
        del self.fields['_rev'];

    def clean__id(self):
        data = self.cleaned_data
        if db.doc_exist(data['_id']):
            raise forms.ValidationError('The document "%s" is already present' % data['_id'])

        return data['_id']


class EditDocumentRootForm(DocBaseForm):
    intro = forms.CharField(widget=forms.Textarea(attrs={'class':'ui-widget ui-corner-all','rows':30, 'cols':60}),
                            label="Introduction", required=False)

    def __init__(self, *args, **kwargs):
        super(EditDocumentRootForm,self).__init__(*args, **kwargs)
        doc =  db.get(args[0]['_id'])
        systems = doc.get('systems',[])
        print "args: ",args
        for i in range(0,len(systems)):
           self.fields['system_%d' % i] = forms.CharField(widget=forms.HiddenInput())


class AddSystemForm(DocBaseForm):
    name = forms.CharField()
    description = forms.CharField(widget=forms.Textarea(), required=False)

    def clean_name(self):

        data = self.cleaned_data
        doc = db.get(data['_id'])
        systems = doc.get('systems',[])

        for s in systems:
            if s['name'] == data['name']:
                raise forms.ValidationError('The system "%s" is already present in "%s"' % (data['name'],doc['_id']))
        return data['name']


class EditSystemForm(forms.Form):
    description = forms.CharField(widget=forms.Textarea(), required=False)
    rules = forms.CharField(widget=forms.Textarea(), required=False)

    def __init__(self, *args, **kwargs):
        super(EditSystemForm, self).__init__(*args, **kwargs)
        system = args[0]
        for i in range(len(system.get('sections',[]))):
            self.fields['section_%d' % i] = forms.CharField(widget=forms.HiddenInput())


    ### Iterator over fields starting with section_
    def section_fields(self):
        for f in self.fields:
            if f.startswith('section_'):
                yield(self.data[f])


class AddSystemSectionForm(forms.Form):
    header = forms.CharField(label="Section Header", help_text="Must be unique in the system")
    description = forms.CharField(widget=forms.Textarea(),help_text="Optional", required=False)


    def __init__(self, *args, **kwargs):
        super(AddSystemSectionForm, self).__init__(*args, **kwargs)
        if 'system' in self.initial:
            self.system = self.initial['system']
        elif 'system' in self.data:
            self.system = self.data['system']

    def clean_header(self):
        for sec_idx in range(0,len(self.system.get('sections',[]))):
            print self.system['sections'][sec_idx]
            if self.system['sections'][sec_idx]['header'] == self.cleaned_data['header']:
                raise forms.ValidationError('There is another section with the same name')
        return self.cleaned_data['header']


class EditSystemSectionForm(forms.Form):
    header = forms.CharField(widget=forms.HiddenInput())
    description = forms.CharField(widget=forms.Textarea(), required=False)

    def __init__(self, *args, **kwargs):
        super(EditSystemSectionForm,self).__init__(*args, **kwargs)
        section = args[0]
        for i in range(len(section.get('questions',[]))):
            self.fields['question_%d' % i] = forms.CharField(widget=forms.HiddenInput())
        print "section",section

    def question_fields(self):
        for f in self.fields:
            if f.startswith('question_'):
                yield(self.data[f])


class AddSystemSectionQuestionForm(forms.Form):
    choice = forms.CharField(widget=forms.Select())

    def __init__(self, *args, **kwargs):
        super(AddSystemSectionQuestionForm, self).__init__(*args, **kwargs)
        if args[0].get('choices'):
            self.fields['choice'].widget.choices = args[0]['choices']
