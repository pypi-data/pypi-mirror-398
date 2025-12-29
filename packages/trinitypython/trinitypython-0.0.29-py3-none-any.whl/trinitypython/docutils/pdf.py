from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, \
    Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
import html

def escape_text_to_html(text):
    # Escape HTML special characters (&, <, >, ", ')
    escaped = html.escape(text)

    # Replace special whitespace characters with HTML-friendly versions
    escaped = escaped.replace('\n', '<br/>')  # Newlines to line breaks
    escaped = escaped.replace('\t',
                              '&emsp;')  # Tabs to em-space (or use multiple &nbsp;)

    return escaped

class MyDocTemplate(BaseDocTemplate):
    def __init__(self, filename, **kwargs):
        self.bookmarks = []
        self.styles = getSampleStyleSheet()
        BaseDocTemplate.__init__(self, filename, **kwargs)
        frame = Frame(self.leftMargin, self.bottomMargin, self.width,
                      self.height, id='normal')
        template = PageTemplate(id='main', frames=frame)
        self.addPageTemplates([template])

def create_pdf_from_sections(json_data, output_filename):
    doc = MyDocTemplate(output_filename, pagesize=A4, rightMargin=50,
                        leftMargin=50, topMargin=50, bottomMargin=50)
    styles = doc.styles
    story = []

    section_title_style = ParagraphStyle(
        name='SectionTitle',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        spaceAfter=20
    )
    question_style = ParagraphStyle(
        name='Question',
        parent=styles['Heading3'],
        spaceAfter=10
    )
    answer_style = styles['Normal']

    for section, qa_dict in json_data.items():
        story.append(Paragraph(f'{section}',section_title_style))
        story.append(Spacer(1, 12))

        for q, a in qa_dict.items():
            story.append(Paragraph(f'<b>{q}</b>',question_style))
            story.append(Paragraph(escape_text_to_html(a), answer_style))
            story.append(Spacer(1, 12))
        story.append(Spacer(1, 12))

    doc.build(story)

    print(f"✅ PDF generated: {output_filename}")


# Example usage
if __name__ == "__main__":
    input_data = {
        "section1": {
            "question1": "This is a long answer for question1. " * 5,
            "question2": "This is a long answer for question2. " * 6,
            "question3": "This is a long answer for question3. " * 7,
        },
        "section2": {
            "question4": "This is a long answer for question4. " * 3
        },
        "section3": {
            "question5": "This is a long answer for question5. " * 8,
            "question6": "This is a long answer for question6. " * 4
        }
    }

    create_pdf_from_sections(input_data,
               r"C:\Users\Dell\OneDrive\Desktop\output_with_links.pdf")
