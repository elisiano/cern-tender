from couchdbkit.ext.django.schema import StringProperty, Document, DictProperty, IntegerProperty, FloatProperty


class AnswerNotValid(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class QuestionTemplate(Document):
    question = StringProperty(required=True)
    tech_spec = StringProperty(required=True, verbose_name="Technical Specification")
    category = StringProperty(required=True)
    tag = StringProperty(required=True)


class QuestionFromList(QuestionTemplate):
    answer = StringProperty()
    answer_data = DictProperty(required=True)

    def __init__(self, *args, **kwargs):
        super(QuestionFromList, self).__init__(*args, **kwargs)
        self._properties['answer'].choices = self.answer_data  # the Property extracts the keys automagically
        if not self.tech_spec:
            self.tech_spec = "Dynamically generated during validation"

    def validate(self, **params):
        super(QuestionFromList, self).validate(**params)  # if it fails it raises an exception
        if self.answer:
            self.tech_spec = self.answer_data[self.answer]
        return True

#from couchdbkit.schema.properties import FloatProperty, IntegerProperty
class QuestionRangeTemplate(QuestionTemplate):
    ts_formatter = StringProperty()

    def __init__(self, *args, **kwargs):
        for p in ['min_', 'max_', 'answer' ]:
            if args[0].get(p, None):
                if isinstance(self._properties[p], FloatProperty):
                    val = args[0][p]
                    args[0][p] = float(val)
                elif isinstance(self._properties[p], IntegerProperty):
                    val = args[0][p]
                    args[0][p] = int(val)
            else:
                val = args[0].get(p, None)
                print "it didn't match %s %s %s" % (p, val, type(val) )



        super(QuestionRangeTemplate, self).__init__(*args, **kwargs)
        if not self.tech_spec:
            self.tech_spec = "Dynamically generated during validation"

    def validate(self, **params):
        for p in ['min_', 'max_', 'answer' ]:
            if getattr(self, p, None):
                if isinstance(self._properties[p], FloatProperty):
                    setattr(self,p,float(getattr(self,p)))
                elif isinstance(self._properties[p], IntegerProperty):
                    setattr(self,p,int(getattr(self,p)))

        print "self.min_: ", self.min_
        print "self.max_: ", self.max_
        super(QuestionRangeTemplate, self).validate(**params)
        if self.answer or self.answer == 0.0:
            if self.min_ <= self.answer <= self.max_:
                if self.ts_formatter:
                    self.tech_spec = self.ts_formatter % self.answer
                return True
            else:
                raise AnswerNotValid("The answer (%s) should be between %s and %s"
                        % (self.answer, self.min_, self.max_))


class QuestionIntegerRange(QuestionRangeTemplate):
    min_ = IntegerProperty(required=True)
    max_ = IntegerProperty(required=True)
    answer = IntegerProperty()


class QuestionFloatRange(QuestionRangeTemplate):
    min_ = FloatProperty(required=True)
    max_ = FloatProperty(required=True)
    answer = FloatProperty()


class QuestionFreeText(QuestionTemplate):
        answer = StringProperty()  # not used?
