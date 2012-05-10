import couchdbkit

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import cm, inch
from reportlab.platypus import Paragraph, Table, TableStyle, SimpleDocTemplate, Spacer
style = getSampleStyleSheet()
styleN = style['Normal']
styleH1 = style['Heading1']
styleH2 = style['Heading2']
styleH3 = style['Heading3']

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


def _print_footer(canvas, doc_id, page):
    canvas.setFont('Times-Roman',9)
    canvas.drawString(2*cm, cm, "%s - Technical Questionnaire" % doc_id)

    page_str="Page %3d" % page
    size = canvas.stringWidth(page_str, 'Times-Roman', 9)
    canvas.drawString(PAGE_WIDTH - size - 4*cm, cm, page_str)


def tq_first_page(canvas, doc, doc_id='<doc id>', title='<title>'):
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
    canvas.drawCentredString(PAGE_WIDTH/2.0, PAGE_HEIGHT-150, 'Technical Questionnaire')

    title_size=34
    canvas.setFont('Times-BoldItalic', title_size)
    import textwrap
    current_y = PAGE_HEIGHT-210
    for line in textwrap.wrap(title,35):
        canvas.drawCentredString(PAGE_WIDTH/2.0, current_y, line)
        current_y -= title_size


    _print_footer(canvas, doc_id, doc.page)

    canvas.restoreState()
    #canvas.showPage()

def tq_later_pages(canvas, doc, doc_id="<doc_id>" ):
    canvas.saveState()
    _print_footer(canvas, doc_id, doc.page)
    canvas.restoreState()

def get_questionnaire_pdf(filename, doc_id, start_index=1):
    """ Method which writes to @filename a pdf representing the questionnaire of @doc_id
    By default the first system is numbered starting with 1, this can be overwritten with the @start_index parameter.
    Subsequent systems will have sequential numbers"""

    doc = db.get(doc_id)
    story = [Spacer(1,10*cm)]
    #story.append(Paragraph('Questionnarire for %s' % doc_id, styleH1))
    story.append(Spacer(1,3*cm))
    data = [[ 'Ref', 'Header/Question', 'Type', 'Answer' ]]

    # this lis will contain the indeces of the rows which shoud have a differnt
    # formatting (headers)
    headers_rows = []
    headers_rows.append(len(data)-1)

    for sys in range(len(doc.get('systems', []))):
        system = doc['systems'][sys]
        data.append(['%s' % (start_index + sys), Paragraph(system['name'], styleH2), '', ''])
        headers_rows.append(len(data)-1)
        for sec in range(len(system.get('sections',[]))):
            section = system['sections'][sec]
            data.append([ '%s.%s' % (start_index + sys, sec + 1), Paragraph(section['header'], styleH3), '', ''])
            headers_rows.append(len(data)-1)
            for q in range(len(section.get('questions', []))):
                question = section['questions'][q]
                data.append( [  "%d.%d.%d" % (start_index + sys, sec + 1, q + 1),
                                Paragraph(question['question'], styleN),
                                _get_type(question),
                                str(question['answer'])
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
    pdf.build(story, onFirstPage=partial(tq_first_page, doc_id=doc_id, title=doc['title']), onLaterPages=partial(tq_later_pages, doc_id=doc_id))

    return pdf

