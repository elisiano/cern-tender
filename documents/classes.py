
import couchdbkit
from questions import models
import pprint

db = couchdbkit.ext.django.loading.get_db('documents')

pp = pprint.PrettyPrinter(indent=4)


class TenderDocumentValidator(object):

    def __init__(self, doc_id):
        self.doc_id = doc_id
        try:
            self.doc=db.get(doc_id)
        except couchdbkit.exceptions.ResourceNotFound:
            self.doc = {}

    def validate(self):
        doc = self.doc
        errors = {}
        result={}
        result['errors'] = errors
        if not self.doc:
            errors[self.doc_id] = "Document not found"
        doc_changed = False
        ### validating questions
        for sys in range(len(doc.get('systems',[]))):
            system = doc['systems'][sys]

            ### Creating the properties dictinary to check the rules later
            properties={}

            ### Checking questions
            for sec in range(len(system.get('sections',[]))):
                section = system['sections'][sec]
                for q in range(len(section.get('questions',[]))):
                    question = section['questions'][q]

                    #### gathering the properties for each question
                    properties.setdefault(question['category'],{})[question['tag']] = question['answer']

                    ### validating the question according to its model
                    try:
                        qm = getattr(models, question['doc_type'])
                    except AttributeError:
                        errors['%s > %s > %s' %
                            (system['name'], section['header'], question['question'])
                            ] = 'Question type %s not found' % question['doc_type']
                    else:
                        try:
                            _q = qm(question)
                            if _q.validate():
                                doc['systems'][sys]['sections'][sec]['questions'][q] = dict(_q)
                                doc_changed = True
                            del _q
                        except couchdbkit.exceptions.BadValueError, e:
                            errors ['%s > %s > %s' %
                            (system['name'], section['header'], question['question'])
                            ] = "Bad Value: %s" % e
                        except models.AnswerNotValid,e :
                            errors ['%s > %s > %s' %
                            (system['name'], section['header'], question['question'])
                            ] = "Answer Not Valid: %s" % e

            ### Checking rules
            for rule in system.get('rules', []):
                try:
                    if not eval(rule, {'__builtins__':{}, 'properties': properties}, {}):
                        errors['%s > Rules > %s' % (system['name'], rule)] = 'Not Satisfied'
                except KeyError, e:
                    errors['%s > Rules > %s' % (system['name'], rule)] = 'Refers to a missing key: %s' % e
                except SyntaxError, e:
                    errors['%s > Rules > %s' % (system['name'], rule)] = "Syntax Error: %s " % e
                except Exception, e:
                    errors['%s > Rules > %s' % (system['name'], rule)] = "Exception: %s" % e
        if doc_changed:
            _ = db.save_doc(doc)
            if not _['ok']:
                errors['Error Saving Document'] = "Error code: %s. Reason: %s" % (_['error'], _['reason'])

        if errors:
            result['ok'] = False
        else:
            result['ok'] = True

        return result