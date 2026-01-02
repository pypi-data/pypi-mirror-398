from typing import Optional
from udf_tools.models.document import UDFDocument
from udf_tools.models.elements import UDFParagraph, UDFContent, UDFTab, UDFSpace
from udf_tools.models.styles import UDFStyle
from udf_tools.core.manager import ContentManager
from udf_tools.core.io import UDFIO

class UDFEditor:
    def __init__(self, doc: Optional[UDFDocument] = None):
        self.doc = doc or UDFDocument()
        self.manager = ContentManager(self.doc.content_text)

    def add_paragraph(self, text: str, style: str = "hvl-default", alignment: int = 0):
        start, length = self.manager.add_text(text + "\n") # Adding newline for paragraph
        content = UDFContent(startOffset=start, length=length, style=style)
        para = UDFParagraph(alignment=alignment, elements=[content])
        self.doc.elements.append(para)
        self.doc.content_text = self.manager.content

    def add_style(self, style: UDFStyle):
        self.doc.styles.append(style)

    def save(self, path: str):
        UDFIO.save(self.doc, path)

    @classmethod
    def load(cls, path: str) -> 'UDFEditor':
        doc = UDFIO.load(path)
        return cls(doc)
