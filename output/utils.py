import reportlab
import couchdbkit

#db = couchdbkit.ext.django.loading.get_db('documents')
### since this module could be used also out of django (for future command line tools)
### I won't use any django specific functionalities
server_uri = "http://procdev14.cern.ch:5985"

db = couchdbkit.client.Server(server_uri).get_db('documents')

def _get_type(question):
    """returns a string describing the question type"""
    if question['doc_type'] == 'QuestionFromList':
        _s = "List:\n"
        _s += '\n'.join(question['answer_data'].keys())
        return _s
    elif question['doc_type'].endswith('Range'):
        _s = question['doc_type'].replace('Question','').replace('Range', ' Range')
        _s += '\nmin: %s\nmax: %s' % (question['min_'], question['max_'])
        return _s
    elif question['doc_type'] == 'QuestionFreeText':
        return "Free Text"


def get_questionnaire_pdf(file, doc_id, start_index=1):
    """ Method which writes to @file a pdf representing the questionnaire of @doc_id
    By default the first system is numbered starting with 1, this can be overwritten with the @start_index parameter.
    Subsequent systems will have sequential numbers"""

    doc = db.get(doc_id)
    
    data = []
    headers = [ 'Ref', 'Question', 'Type', 'Answer' ]
    headers_rows = []

    for sys in range(len(doc.get('systems', []))):
        system = doc['systems'][sys]
        data.append(['%d' % (start_index + sys), system['name'], '', ''])
        for sec in range(len(system.get('sections',[]))):
            section = system['sections'][sec]
            data.append([ '%d.%d' % (start_index + sys, sec + 1), section['header'], '', ''])
            for q in range(len(section.get('questions', []))):
                question = section['questions'][q]
                data.append( [  "%d.%d.%d" % (start_index + sys, sec + 1, q + 1),
                                question['question'],
                                _get_type(question),
                                question['answer'] 
                            ])
    print data
                

