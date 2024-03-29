from django import forms
import couchdbkit
import pprint

### Putting it here so it can be used by any form
db = couchdbkit.ext.django.loading.get_db('documents')

pp = pprint.PrettyPrinter(indent=12)


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
    intro_header = forms.CharField(label="Introduction Header", required=False)
    intro = forms.CharField(widget=forms.Textarea(attrs={'class':'ui-widget ui-corner-all','rows':30, 'cols':60}),
                            label="Introduction", required=False)


    questionnaire_intro = forms.CharField(widget=forms.Textarea(attrs={'class':'ui-widget ui-corner-all','rows':30, 'cols':60}),
                            label="Questionnaire Introduction", required=False)
    title = forms.CharField()

    def __init__(self, *args, **kwargs):
        super(EditDocumentRootForm,self).__init__(*args, **kwargs)
        doc =  db.get(args[0]['_id'])
        systems = doc.get('systems',[])
        contacts = doc.get('contacts',[])
        for i in range(0,len(systems)):
           self.fields['system_%d' % i] = forms.CharField(widget=forms.HiddenInput())
        for i in range(0,len(contacts)):
             self.fields['contact_%d' % i ] = forms.CharField(widget=forms.HiddenInput())

class ContactForm(forms.Form):
    type_ = forms.CharField()
    name = forms.CharField()
    address = forms.CharField(widget=forms.Textarea(attrs={'class':'ui-widget ui-corner-all','rows':4, 'cols':20}))
    tel = forms.CharField()
    fax = forms.CharField()
    email = forms.EmailField(label='E-mail')


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
    rules = forms.CharField(widget=forms.Textarea(attrs={'cols':120}), required=False, help_text="""<pre>
    Rules are Python expressions, one per line, accessing a dictionary called "properties".
    The dictionary will contain the defined categories -> tags as nested keys.

    Example:
        properties['psu']['modules_number'] >= 2 and properties['psu']['modules_redundant'] == 'Yes'

    </pre>""")

    def __init__(self, *args, **kwargs):
        super(EditSystemForm, self).__init__(*args, **kwargs)
        system = args[0]
        properties = {}
        for s in range(len(system.get('sections',[]))):
            self.fields['section_%d' % s] = forms.CharField(widget=forms.HiddenInput())
            for q in range(len(system['sections'][s].get('questions',[]))):
                question = system['sections'][s]['questions'][q]
                properties.setdefault(question['category'], {})[question['tag']] = { 'question': question['question'],
                                                                                     'answer': question['answer']
                                                                                     }

        indent = " " * 8
        _txt = ""
        for cat_k in properties:
            for tag_k in properties[cat_k]:
                _txt += "properties['%s']['%s']\n\tCurrent value: %s\n\tDefined in question: %s\n\n" % (cat_k, tag_k, properties[cat_k][tag_k]['answer'].__repr__(),properties[cat_k][tag_k]['question'])
        _txt = _txt.replace('\n','\n%s' % indent)
        help_text = """<pre>
    Currently Defined Properties:
        %s
    </pre>""" % (_txt if _txt else "No property defined at the moment")
        self.fields['rules'].help_text += help_text

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

    def question_fields(self):
        for f in self.fields:
            if f.startswith('question_'):
                yield(self.data[f])


class AddSystemSectionQuestionForm(forms.Form):
    choice = forms.CharField(widget=forms.Select())

    def __init__(self, *args, **kwargs):
        super(AddSystemSectionQuestionForm, self).__init__(*args, **kwargs)
        if kwargs.get('initial'):
            self.fields['choice'].widget.choices = kwargs['initial'].get('choices',[])
            self.section_questions = kwargs['initial'].get('section_questions',[])
        else:
            self.fields['choice'].widget.choices = args[0]['choices']
            self.section_questions = args[0].get('section_questions',[])

    def clean_choice(self):
        choice = self.cleaned_data['choice'][3:-2]
        dbq = couchdbkit.ext.django.loading.get_db('questions')
        qdoc = dbq.get(choice)
        for q in self.section_questions:
            if q == qdoc['question']:
                raise forms.ValidationError('Question already present in the section')
        return choice


class EditSystemSectionQuestionForm(forms.Form):
    #question = forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    question = forms.CharField(widget=forms.TextInput())
    answer = forms.CharField(required=False)
    category = forms.CharField()
    tag = forms.CharField()
    doc_type = forms.CharField(widget=forms.HiddenInput())
    tech_spec = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(EditSystemSectionQuestionForm, self).__init__(*args, **kwargs)

        if kwargs.get('initial'):
            self.data = kwargs['initial']
        else:
            self.data = args[0]

        # Duck Typing: if some known fields are present they will be added to the form
        ### First Case: QuestionFromList
        i = 1
        while self.data.get('answer_%d' % i, None):
            self.fields['answer_%d' % i] = forms.CharField()
            self.fields['tech_spec_%d' % i] = forms.CharField()
            i+=1
        ### For range types there are min_, max_ and ts_formatter
        for f in [('min_', None), ('max_', None), ('ts_formatter', 'Tech Spec Formatter')]:
            if self.data.get(f[0], None) or type(self.data.get(f[0], None)) in [int, float]:
                self.fields[f[0]] = forms.CharField(label=f[1])

    def clean_question(self):
            db = couchdbkit.ext.django.loading.get_db('documents')
            doc = db.get(self.data['from_doc'])
            section = doc['systems'][int(self.data['from_sys'])]['sections'][int(self.data['from_sec'])]
            section['questions'].pop(int(self.data['from_qid']))

            for q in section['questions']:
                print "%s == %s ? %s" % (q['question'], self.cleaned_data['question'], q['question'] == self.cleaned_data['question'])
                if q['question'].strip() == self.cleaned_data['question'][3:-2].strip():
                    raise forms.ValidationError('Question already present in the section')
                
            return self.cleaned_data['question']

    # due to a nasty bug somewhere I need to clean the cleaned_data dictionary
    # if the previous method (clean_question) is removed, this is not necessary
    def clean(self):
        data = {}
        for field in self.cleaned_data:
            data[field] = self.cleaned_data[field][3:-2].strip()
        
        return data

