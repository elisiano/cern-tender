from django import forms
import couchdbkit

### Putting it here so it can be used by any form
db = couchdbkit.ext.django.loading.get_db('documents')

class NewDocument(forms.Form):
    _id = forms.CharField(label="Document ID")
    
    def clean__id(self):
        data = self.cleaned_data
        if db.doc_exist(data['_id']):
            raise forms.ValidationError('The document "%s" is already present' % data['_id'])
            
        return data['_id']
   
