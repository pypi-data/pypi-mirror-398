from typing import List, Optional, Union
from pydantic import BaseModel, Field
from udf_tools.models.elements import UDFParagraph, UDFTable, UDFBaseElement
from udf_tools.models.styles import UDFStyle

class UDFDocument(BaseModel):
    format_id: str = "1.8"
    isTemplate: bool = False
    description: str = ""
    content_text: str = ""
    styles: List[UDFStyle] = Field(default_factory=list)
    elements: List[Union[UDFParagraph, UDFTable]] = Field(default_factory=list)
    
    # Page layout
    mediaSizeName: str = "A4"
    leftMargin: float = 70.86
    rightMargin: float = 70.86
    topMargin: float = 56.69
    bottomMargin: float = 56.69
    paperOrientation: str = "portrait"
