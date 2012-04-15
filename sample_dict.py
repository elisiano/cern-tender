### This is an example of the structure of the document
doc ={ 
        '_id':'IT-XYZ/IT', 
        'intro':'blah blah blah very long text\n Seriously.', 
        'systems': [ 
            { 
            'name':'System 1',
            'sections': [   {
                                'header': 'Section 1',
                                'description': 'not mandatory',
                                'questions' :
                                    [
                                        {   'answer': 'blah blah', 
                                            'question':'original question', 
                                            'tech_spec':'some tech spec' 
                                        },
                                        {   'question':'some other dictionary',
                                            'answer':'some other answer'
                                        }
                                        
                                    ],
                            },
                            {
                                'header': 'Section 2',
                                'description': None,
                                'questions':
                                    [
                                        { 'question': 'From list',
                                          'answer_data' : { 'Yes': 'It works',
                                                            'No': "It doesn't work"},
                                            'answer': 'Yes',
                                            'tech_spec': 'It works'
                                        }
                                    ]
                            }
                        ],
            'rules': [ 'first rule','second rule']
            },
            {
            'name': 'System 2',
            'sections': [ {
                            'header': 'Section 1',
                            'description': None,
                            'questions': 
                                [
                                    {   'question': 'first question of the second system',
                                         'answer': 'first answer of the second system'
                                    }
                                ]
                            }
                        ],
            'rules': [ 'psu.modules >= 2', 'cpu.freq >= 3.0' ], 

            }
        ],
    }
