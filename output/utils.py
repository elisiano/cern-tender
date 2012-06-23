import couchdbkit
import textwrap
import re
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
import copy
import pprint
pp = pprint.PrettyPrinter(indent=4)
#db = couchdbkit.ext.django.loading.get_db('documents')
### since this module could be used also out of django (for future command line tools)
### I won't use any django specific functionalities, but I will refer to the project settings
# server_uri = "http://procdev14.cern.ch:5985"
from tender import settings
server_uri = "http://" + filter(lambda x: x[0] =='tender.documents', settings.COUCHDB_DATABASES)[0][1].split('/')[2]

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


def get_category_tag_index(doc_id, start_index=1):
    idx = {}
    doc = db.get(doc_id)
    for sys in range(len(doc.get('systems', []))):
        system = doc['systems'][sys]
        for sec in range(len(system.get('sections',[]))):
            section = system['sections'][sec]
            for q in range(len(section.get('questions', []))):
                question = section['questions'][q]
                idx.setdefault(question['category'],{})[question['tag']] = "%d.%d.%d" % (start_index + sys, sec + 1, q + 1)

    return idx

def get_doc_copy_with_references(doc_id, start_index=1, qproperties=['question', 'tech_spec']):
    """
    Returns a copy of the document with the references substituted
    It checks each question of the document. If the properties (found in @qproperties) match the pattern {# category.tag #}
    then the value of the pattern is substituted with the proper reference number

    WARNING: if multiple questions with the same category/tag are defined, all the references will point to the last definition
    """
    reference_pattern = re.compile(r'\{\#\s*(?P<category>.*?)\.(?P<tag>[^%\s]*?)\s*\#\}')
    references = get_category_tag_index(doc_id, start_index)
    doc = db.get(doc_id)

    for sys in range(len(doc.get('systems', []))):
        system = doc['systems'][sys]
        for sec in range(len(system.get('sections',[]))):
            section = system['sections'][sec]
            for q in range(len(section.get('questions', []))):
                question = section['questions'][q]

                ### Replacements in question['question'] and question['tech_spec']
                for prop in qproperties:
                    p = question[prop]
                    match = reference_pattern.search(question[prop])
                    while match:
                        question[prop]= p[0:match.start()] + references[match.group('category')][match.group('tag')] + p[match.end():]
                        p = question[prop]
                        match = reference_pattern.search(p)
    return doc

def get_questionnaire_pdf(filename, doc_id, start_index=1, print_answers=True):
    """ Method which writes to @filename a pdf representing the questionnaire of @doc_id
    By default the first system is numbered starting with 1, this can be overwritten with the @start_index parameter.
    Subsequent systems will have sequential numbers"""


    doc = get_doc_copy_with_references(doc_id, start_index=1)
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

    # this lis will contain the indices of the rows which should have a different
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
                                (str(question['answer'] or '') if print_answers else '')
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


import xlwt
def _get_xls_formula(question, answer_cell_reference):
    if question['doc_type'] == 'QuestionFromList':
        formula="IF(OR("
        tmp_conds=[]
        for k in question['answer_data']:
#            tmp_conds.append('CELL("contents",%s)=="%s"' % (answer_cell_reference, k))
            tmp_conds.append('%s="%s"' % (answer_cell_reference, k))
        formula += ','.join(tmp_conds)
        formula += "),TRUE,FALSE)"
        return xlwt.Formula(formula)
    elif question['doc_type'].find('Range') > -1:
        formula="AND(%s >= %s, %s <= %s)" % ( answer_cell_reference, question['min_'],
                                              answer_cell_reference, question['max_'])
        return xlwt.Formula(formula)

    elif question['doc_type'] == 'QuestionFreeText':
        formula = 'IF(%s="",FALSE,TRUE)' % answer_cell_reference
        return xlwt.Formula(formula)

    else:
        return ""

def get_questionnaire_xls(filename, doc_id, start_index=1, print_answers=True):
    doc = get_doc_copy_with_references(doc_id, start_index=1)
    wb = xlwt.Workbook()
    sheet = wb.add_sheet('Technical Questionnaire')


    styleH1 = xlwt.easyxf('font: name Calibri, height 300, bold on; align: wrap on, vert centre')
    styleH2 = xlwt.easyxf('font: name Caliri, height 275, bold on; align: wrap on, vert centre')
    styleN = xlwt.easyxf('font: name Calibri, height 275; align: wrap on, vert centre')

    style_centered = xlwt.easyxf('font: name Caliri, height 250; align: wrap on, vert centre, horiz center')

    row = 0
    col = 0
    sheet.write(row,col+1,"Technical Questionaire for %s" % doc_id, styleH1)
    row+=1

    sheet.row(row).height=3333
    sheet.row(row).height_mismatch=True
    sheet.write_merge(row,row,col,col+4,doc['questionnaire_intro'],styleH2)
    row +=2

    sheet.write(row, col  ,"Ref", styleH2)
    sheet.write(row, col+1,"System/Section/Question", styleH2)
    sheet.write(row, col+2,"Type", styleH2)
    sheet.write(row, col+3,"Answer", styleH2)
    sheet.write(row, col+4,"Valid?", styleH2)
    row += 2

    background = xlwt.Pattern()
    background.pattern = xlwt.Pattern.SOLID_PATTERN
    background.pattern_fore_colour = 0x16 #light gray

    borders = xlwt.Borders()
    borders.left = borders.right = borders.top = borders.bottom = xlwt.Borders.THIN

    styleH1.pattern = background
    styleH2.pattern = background
    styleH1.borders = borders
    styleH2.borders = borders

    for sys in range(len(doc.get('systems', []))):
        system = doc['systems'][sys]
        sheet.write(row, col, '%d' % (start_index + sys), styleH1)
        sheet.write_merge(row, row, col+1, col+4, system['name'], styleH1)
        row += 1
        for sec in range(len(system.get('sections',[]))):
            section = system['sections'][sec]
            sheet.write(row, col, '%d.%d' % (start_index + sys, sec + 1), styleH2)
            sheet.write_merge(row, row, col+1, col+4, section['header'], styleH2)
            row += 1

            for q in range(len(section.get('questions', []))):
                question = section['questions'][q]
                sheet.write(row, col, "%d.%d.%d" % (start_index + sys, sec + 1, q + 1), styleN)
                sheet.write(row, col+1, question['question'], styleN)
                sheet.write(row, col+2, _get_type(question), style_centered)
                sheet.write(row, col+3, str(question['answer'] or '') if print_answers else '', style_centered)
                sheet.write(row, col+4, _get_xls_formula(question, xlwt.Utils.rowcol_to_cell(row, col+3)), styleN)
                row += 1

    sheet.col(col).width = 2000
    sheet.col(col+1).width = 20000
    sheet.col(col+2).width = 7500
    sheet.col(col+3).width = 3000
    sheet.row_default_height = 510

    wb.save(filename)


def get_document_pdf(filename, doc_id, start_index=1):
    doc = get_doc_copy_with_references(doc_id, start_index=1)
    story = [Spacer(1,10*cm)]
    if doc.get('intro', None):
        story.append(P(doc['intro_header'] or 'Scope of the invitation to Tender',styleH1))
        styleP = copy.deepcopy(styleN)
        styleP.firstLineIndent=20
        styleP.alignment = TA_JUSTIFY
        for p in doc['intro'].replace('\r','').split('\n'):
            if not p: # empty line:
                story.append(Spacer(1,12))
            else:
                story.append(P(p, styleP))

    styleN.alignment = TA_JUSTIFY
    H1 = partial(Paragraph, style=styleH1)
    H2 = partial(Paragraph, style=styleH2)
    H3 = partial(Paragraph, style=styleH3)
    N = partial(Paragraph, style=styleN)

    for s in [styleH1, styleH2, styleH3]:
        s.bulletFontSize = s.fontSize

    indent=30
    styleH1L1 = ParagraphStyle(name='H1L1', parent=styleH1, leftIndent=indent, bulletIndent=indent)
    styleH1L1.bulletFontSize = styleH1.bulletFontSize
    H1L1 = partial(Paragraph,style=styleH1L1)

    styleH2L1 = ParagraphStyle(name='H2L1', parent=styleH2, leftIndent=indent, bulletIndent=indent)
    H2L1 = partial(Paragraph, style=styleH2L1)

    styleNL1 = ParagraphStyle(name='NL1', parent=styleN, leftIndent=indent*2, bulletIndent=indent, spaceAfter=5)
    NL1 = partial(Paragraph, style=styleNL1)



    for sys in range(len(doc.get('systems',[]))):
        system = doc['systems'][sys]

        bt = "%d" % (start_index + sys)
        story.append(Spacer(1,cm))
        story.append(
                        H1(system['name'], bulletText = bt )
                    )
        if system['description']:
            story.append(N(system['description']))


        # due to this http://two.pairlist.net/pipermail/reportlab-users/2008-January/006676.html
        # the use of a table is not suitable. I will build the list with bulleted paragraphs
        for sec in range(len(system.get('sections',[]))):

            section=system['sections'][sec]
            bt = '%d.%d' % (start_index + sys, sec+1)

            story.append(
                        H2(section['header'], bulletText=bt)
                    )

            if section['description']:
                story.append(N(section['description']))

            for q in range(len(section.get('questions',[]))):
                question = section['questions'][q]
                bt = "%d.%d.%d" % (start_index + sys, sec+1, q+1)

                story.append(NL1(question['tech_spec'], bulletText=bt))



    if doc.get('contacts', None):
        contacts_per_row=3
        _cs = copy.deepcopy(doc.get('contacts',[]))
        table_data = []
        # let's pad the table
        while len(_cs) % contacts_per_row != 0:
            _cs.append(dict({u'type_':'', u'name':'', u'address':'',u'tel':'',u'fax':'', u'email':''}))
        stack = []
        for ci in range(len(_cs)):
            stack.append(_cs[ci])
            if len(stack) == contacts_per_row:
                table_data.append([ u'']       + [c['type_']+':' if c['type_'] else '' for c in stack])
                table_data.append([u'Name']    + [c['name'] for c in stack])
                table_data.append([u'Address'] + [c['address'].replace('\r','') for c in stack])
                table_data.append([u'Tel']     + [c['tel'] for c in stack])
                table_data.append([u'Fax']     + [c['fax'] for c in stack])
                table_data.append([u'E-mail']  + [c['email'] for c in stack])
                table_data.append([u'']*(contacts_per_row+1))
                stack=[]

        table_style=TableStyle([('VALIGN',(0,0), (-1,-1), 'TOP'),
                                ('ALIGN', (0,0), (0,-1), 'LEFT'),
                                ('ALIGN', (0,0), (0,-1), 'RIGHT'),
                                #('GRID',(0,0), (-1,-1), 0.25, colors.black)
                            ])
        table=Table(table_data, colWidths=[2.5*cm]+[4.5*cm]*contacts_per_row, style=table_style)
        #story.append(Spacer(1,cm)) 
        story.append(PageBreak()) # as requested now there is a PageBreak before the Contacts
        story.append(H1('Contacts'))
        story.append(table)


    pdf = SimpleDocTemplate(filename)
    _on_first_page = partial(_first_page, doc_id=doc_id, title=doc['title'], type_="Technical Specifications")
    _on_later_pages = partial(_later_pages, doc_id=doc_id, type_="Technical Specifications")
    pdf.build(story, onFirstPage=_on_first_page, onLaterPages=_on_later_pages)

    return pdf


import docx
import tempfile
import os
def get_document_docx(filename, doc_id, start_index=1):
    """filename is a file like object (like an HttpResponse)"""
    
    doc = get_doc_copy_with_references(doc_id, start_index=1)
    
    H1 = partial(docx.heading,headinglevel=1)
    H2 = partial(docx.heading,headinglevel=2)
    N = partial(docx.paragraph,style='')
    
    ### Followed the example of the author of the library
    relationships = docx.relationshiplist()
    document = docx.newdocument()
    docbody = document.xpath('/w:document/w:body', namespaces=docx.nsprefixes)[0]

    docbody.append(docx.paragraph([('CERN - European Organisation for Nuclear Research','b')],jc='center'))
    docbody.append(docx.paragraph([('1211 Geneva 23, Switzerland', 'b')],jc='center'))


    ### Unable to center the table, commending it for no
#    docbody.append(docx.table(
#                            [[docx.paragraph([('Invitation to tender %s' % doc_id,'b')],jc='center')]], 
#                            heading=False,
#                            borders={'all':{'color':'auto', 'size':'1', 'val':'single'}},
#                                
#                            ))

    story = docbody
    story.append(N(''))
    story.append(N(''))
    story.append(docx.paragraph([('Invitation to tender %s' % doc_id,'bu')],jc='center'))
    story.append(N(''))
    story.append(docx.paragraph([('Technical Specifications','bi')],jc='center'))
    story.append(N(''))

    
    if doc.get('intro', None):
        story.append(H1(doc['intro_header'] or 'Scope of the invitaion to Tender'))
        story.append(N(doc['intro']))
        
    for sys in range(len(doc.get('systems',[]))):
        system = doc['systems'][sys]
        bt = "%d" % (start_index + sys)
        story.append(N('\n\n'))
        story.append(H1('%s. %s' % (bt, system['name'])))

        if system['description']:
            story.append(N(system['description']))

        for sec in range(len(system.get('sections',[]))):

            section=system['sections'][sec]
            bt = '%d.%d' % (start_index + sys, sec+1)

            story.append(
                        H2('%s. %s' % (bt, section['header']))
                    )

            if section['description']:
                story.append(N(section['description']))

            for q in range(len(section.get('questions',[]))):
                question = section['questions'][q]
                bt = "%d.%d.%d" % (start_index + sys, sec+1, q+1)

                story.append(N('\t%s. %s' % (bt, question['tech_spec'])))


    if doc.get('contacts', None):
        contacts_per_row=3
        _cs = copy.deepcopy(doc.get('contacts',[]))
        table_data = []
        # let's pad the table
        while len(_cs) % contacts_per_row != 0:
            _cs.append(dict({u'type_':'', u'name':'', u'address':'',u'tel':'',u'fax':'', u'email':''}))
        stack = []
        for ci in range(len(_cs)):
            stack.append(_cs[ci])
            if len(stack) == contacts_per_row:
                table_data.append([ u'']       + [c['type_']+':' if c['type_'] else '' for c in stack])
                table_data.append([u'Name']    + [c['name'] for c in stack])
                table_data.append([u'Address'] + [c['address'].replace('\r','') for c in stack])
                table_data.append([u'Tel']     + [c['tel'] for c in stack])
                table_data.append([u'Fax']     + [c['fax'] for c in stack])
                table_data.append([u'E-mail']  + [c['email'] for c in stack])
                table_data.append([u'']*(contacts_per_row+1))
                stack=[]

        story.append(N(''))
        story.append(docx.table(table_data, heading=False))

    # Create our properties, contenttypes, and other support files
    coreprops = docx.coreproperties(title='Invitation to tender %s' % doc_id,subject='IT %s Technical Specifications',creator='Elisiano Petrini',keywords=['tender','Office Open XML','Word','%s' % doc_id])
    appprops = docx.appproperties()
    contenttypes = docx.contenttypes()
    websettings = docx.websettings()
    wordrelationships = docx.wordrelationships(relationships)
    f = tempfile.NamedTemporaryFile(delete=False)
    docx.savedocx(document,coreprops,appprops,contenttypes,websettings,wordrelationships, f.name)
    f.close()
    with open(f.name, 'rb') as f:
        filename.write(f.read())
    os.unlink(f.name)
    return document
