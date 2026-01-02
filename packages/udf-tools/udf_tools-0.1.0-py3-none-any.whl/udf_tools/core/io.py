import zipfile
import io
from lxml import etree
from udf_tools.models.document import UDFDocument
from udf_tools.models.styles import UDFStyle
from udf_tools.models.elements import UDFParagraph, UDFContent, UDFTable, UDFRow, UDFCell, UDFTab, UDFSpace
from udf_tools.core.manager import ContentManager

class UDFParser:
    @staticmethod
    def to_xml(doc: UDFDocument) -> str:
        root = etree.Element("template", format_id=doc.format_id, isTemplate=str(doc.isTemplate).lower())
        if doc.description:
            root.set("description", doc.description)

        # Content section
        content_el = etree.SubElement(root, "content")
        content_el.text = etree.CDATA(doc.content_text)

        # Properties
        props_el = etree.SubElement(root, "properties")
        etree.SubElement(props_el, "pageFormat", 
                         mediaSizeName=doc.mediaSizeName,
                         leftMargin=str(doc.leftMargin),
                         rightMargin=str(doc.rightMargin),
                         topMargin=str(doc.topMargin),
                         bottomMargin=str(doc.bottomMargin),
                         paperOrientation=doc.paperOrientation)

        # Styles
        styles_el = etree.SubElement(root, "styles")
        for style in doc.styles:
            etree.SubElement(styles_el, "style", **style.to_xml_attrs())

        # Elements
        elements_el = etree.SubElement(root, "elements")
        for elem in doc.elements:
            UDFParser._append_element(elements_el, elem)

        return etree.tostring(root, encoding='UTF-8', xml_declaration=True, pretty_print=True).decode('utf-8')

    @staticmethod
    def _append_element(parent, elem):
        if isinstance(elem, UDFParagraph):
            p_el = etree.SubElement(parent, "paragraph", Alignment=str(elem.alignment))
            # Add other paragraph attributes here...
            for child in elem.elements:
                UDFParser._append_element(p_el, child)
        elif isinstance(elem, UDFContent):
            etree.SubElement(parent, "content", startOffset=str(elem.startOffset), length=str(elem.length))
        elif isinstance(elem, UDFTab):
            etree.SubElement(parent, "tab", startOffset=str(elem.startOffset), length=str(elem.length))
        elif isinstance(elem, UDFSpace):
            etree.SubElement(parent, "space", startOffset=str(elem.startOffset), length=str(elem.length))
        # Add table/row/cell/image support...

class UDFIO:
    @staticmethod
    def save(doc: UDFDocument, path: str):
        content_xml = UDFParser.to_xml(doc)
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("content.xml", content_xml)

    @staticmethod
    def load(path: str) -> UDFDocument:
        with zipfile.ZipFile(path, 'r') as zf:
            content_xml = zf.read("content.xml")
            # TODO: Implement XML -> UDFDocument parsing
            return UDFDocument()
