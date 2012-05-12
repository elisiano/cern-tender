import couchdbkit
import textwrap
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Table, TableStyle, SimpleDocTemplate, Spacer, PageBreak
from reportlab.lib.enums import TA_JUSTIFY
style = getSampleStyleSheet()
styleN = style['Normal']
styleH1 = style['Heading1']
styleH2 = style['Heading2']
styleH3 = style['Heading3']
P = Paragraph

#from reportlab.rl_config import defaultPageSize
from reportlab.lib.pagesizes import A4 as defaultPageSize
PAGE_HEIGHT=defaultPageSize[1]; PAGE_WIDTH=defaultPageSize[0]

from functools import partial

import pprint
pp = pprint.PrettyPrinter(indent=4)
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


def _print_footer(canvas, left_string, page):
    canvas.setFont('Times-Roman',9)
    canvas.drawString(2*cm, cm, left_string)

    page_str="Page %3d" % page
    size = canvas.stringWidth(page_str, 'Times-Roman', 9)
    canvas.drawString(PAGE_WIDTH - size - 4*cm, cm, page_str)


def _first_page(canvas, doc, doc_id='<doc id>', title='<title>', type_="<type>"):
    canvas.saveState()
    canvas.setFont('Times-Bold', 12)
    canvas.drawCentredString(PAGE_WIDTH/2.0, PAGE_HEIGHT-40,
                              "CERN - European Organisation for Nuclear Research")
    canvas.drawCentredString(PAGE_WIDTH/2.0, PAGE_HEIGHT-52,
                             "1211 Geneva 23, Switzerland")

    canvas.setFont('Times-Roman', 16)
    canvas.drawCentredString(PAGE_WIDTH/2.0, PAGE_HEIGHT-100, "Invitation to Tender %s" % doc_id)
    canvas.setLineWidth(0.5)
    canvas.rect(2*cm, PAGE_HEIGHT-4.15*cm, PAGE_WIDTH-4*cm, 1.5*cm)

    canvas.setFont('Times-Bold', 16)
    canvas.drawCentredString(PAGE_WIDTH/2.0, PAGE_HEIGHT-150, type_)

    title_size=34
    canvas.setFont('Times-BoldItalic', title_size)

    current_y = PAGE_HEIGHT-210
    for line in textwrap.wrap(title,35):
        canvas.drawCentredString(PAGE_WIDTH/2.0, current_y, line)
        current_y -= title_size


    _print_footer(canvas, "%s - %s" % (doc_id, type_), doc.page)

    canvas.restoreState()
    #canvas.showPage()

def _later_pages(canvas, doc, doc_id="<doc_id>", type_="<type>" ):
    canvas.saveState()
    _print_footer(canvas, "%s - %s" % (doc_id, type_), doc.page)
    canvas.restoreState()

def get_questionnaire_pdf(filename, doc_id, start_index=1):
    """ Method which writes to @filename a pdf representing the questionnaire of @doc_id
    By default the first system is numbered starting with 1, this can be overwritten with the @start_index parameter.
    Subsequent systems will have sequential numbers"""


    doc = db.get(doc_id)
    story = [Spacer(1,10*cm)]
    story.append( P(doc['questionnaire_intro'],
                  ParagraphStyle( name='ItalicJustified',
                                  alignment=TA_JUSTIFY,
                                  fontName='Times-Italic')))
    story.append(Spacer(1,3*cm))


    company_data = [['0', P('Company and Offer',styleH1), ''],
                    ['0.1', P('Company Name', styleN), ''],
                    ['0.2', P('if alternative proposal(s) submitted: Bid (Conforming bid or alternative proposal)', styleN), '']
                ]
    company_style = TableStyle([
                ('GRID',    (0, 0), (-1, -1), 0.25, colors.black),
                ('VALIGN',  (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND',  (0, 0), (-1, 0), colors.lightgrey),
        ])

    table = Table(company_data, colWidths=[ 1.5*cm, 11.5*cm, 6*cm], style=company_style)
    story.append(table)
    story.append(PageBreak())

    data = [[ 'Ref', 'Header/Question', 'Type', 'Answer' ]]

    # this lis will contain the indeces of the rows which shoud have a differnt
    # formatting (headers)
    headers_rows = []
    headers_rows.append(len(data)-1)

    for sys in range(len(doc.get('systems', []))):
        system = doc['systems'][sys]
        data.append(['%s' % (start_index + sys), P(system['name'], styleH2), '', ''])
        headers_rows.append(len(data)-1)
        for sec in range(len(system.get('sections',[]))):
            section = system['sections'][sec]
            data.append([ '%s.%s' % (start_index + sys, sec + 1), P(section['header'], styleH3), '', ''])
            headers_rows.append(len(data)-1)
            for q in range(len(section.get('questions', []))):
                question = section['questions'][q]
                data.append( [  "%d.%d.%d" % (start_index + sys, sec + 1, q + 1),
                                P(question['question'], styleN),
                                _get_type(question),
                                str(question['answer'] or '')
                            ])

    table_styles = TableStyle([
                ('GRID', (0,0), (-1,-1), 0.25, colors.black),
                ('VALIGN', (0,0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (2,0), (3,-1), 'CENTER'),
        ])
    for h in headers_rows:
        table_styles.add('BACKGROUND', (0,h), (-1,h), colors.lightgrey)

    table = Table(data , colWidths=[ 1.5*cm, 12.5*cm, 3*cm, 2*cm], style=table_styles)
    story.append(table)

    pdf = SimpleDocTemplate(filename)
    #title="Very very very very very long title which probably will not fit in one line and the behaviour is not known"
    #title="Short title"
    _on_first_page = partial(_first_page, doc_id=doc_id, title=doc['title'], type_="Technical Questionnaire")
    _on_later_pages = partial(_later_pages, doc_id=doc_id, type_="Technical Questionnaire")
    pdf.build(story, onFirstPage=_on_first_page, onLaterPages=_on_later_pages)

    return pdf


def get_document_pdf(filename, doc_id, start_index=1):
    doc = db.get(doc_id)
    story = [Spacer(1,10*cm)]

    if doc.get('intro', None):
        story.append(P('Scope of the invitationto Tender',styleH1))
        story.append(P(doc['intro'], styleN))

    outer_table = []
    outer_h1s = []
    outer_h2s = []
    outer_h3s = []
    outer_spans = []
    H1 = partial(Paragraph, style=styleH1)
    H2 = partial(Paragraph, style=styleH2)
    H3 = partial(Paragraph, style=styleH3)
    N = partial(Paragraph, style=styleN)

    for sys in range(len(doc.get('systems',[]))):
        system = doc['systems'][sys]
        outer_table.append([
                        H1("%d" % (start_index + sys)),
                        H1(system['name'])
                    ])
        outer_h1s.append(start_index + sys)
        if system['description']:
            outer_table.append([system['description'], ''])
            outer_spans.append(len(outer_table)-1)

        inner_table=[]
        for sec in range(len(system.get('sections',[]))):
            section=system['sections'][sec]
            outer_table.append([
                        H2('%d.%d' % (start_index+sys, sec+1)),
                        H2(section['header'])
                    ])
            outer_h2s.append(len(outer_table)-1)
            if section['description']:
                outer_table.append('',N(section['description']))

            for q in range(len(section.get('questions',[]))):
                question = section['questions'][q]
                inner_table.append([
                                N('%d.%d.%d' % (start_index+sys, sec+1, q+1)),
                                N(question['tech_spec'] or 'No TS')
                        ])
            it = Table(inner_table, colWidths=[1.5*cm,10*cm])
            outer_table.append(['',it])
    table = Table(outer_table, colWidths=[2*cm,15*cm])
    story.append(table)
    pdf = SimpleDocTemplate(filename)
    _on_first_page = partial(_first_page, doc_id=doc_id, title=doc['title'], type_="Technical Specifications")
    _on_later_pages = partial(_later_pages, doc_id=doc_id, type_="Technical Specifications")
    pdf.build(story, onFirstPage=_on_first_page, onLaterPages=_on_later_pages)

    return pdf




