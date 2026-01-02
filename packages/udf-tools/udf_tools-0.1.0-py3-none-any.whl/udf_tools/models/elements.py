from typing import List, Optional, Union
from pydantic import BaseModel, Field

class UDFBaseElement(BaseModel):
    pass

class UDFContent(UDFBaseElement):
    startOffset: int
    length: int
    family: Optional[str] = None
    size: Optional[float] = None
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    underline: Optional[bool] = None
    style: Optional[str] = None
    # Add other formatting fields as needed...

class UDFParagraph(UDFBaseElement):
    alignment: int = 0  # 0: Left, 1: Center, 2: Right, 3: Justify
    leftIndent: float = 0.0
    rightIndent: float = 0.0
    firstLineIndent: float = 0.0
    spaceBefore: float = 0.0
    spaceAfter: float = 0.0
    lineSpacing: float = 1.0
    elements: List[Union[UDFContent, 'UDFTab', 'UDFSpace', 'UDFImage']] = Field(default_factory=list)

class UDFTab(UDFBaseElement):
    startOffset: int
    length: int = 1

class UDFSpace(UDFBaseElement):
    startOffset: int
    length: int = 1

class UDFImage(UDFBaseElement):
    imageData: str  # Base64
    width: float
    height: float
    alignment: int = 1
    description: Optional[str] = None

class UDFCell(UDFBaseElement):
    paragraphs: List[UDFParagraph] = Field(default_factory=list)
    width: Optional[float] = None
    colspan: int = 1
    rowspan: int = 1
    vAlign: str = "middle"

class UDFRow(UDFBaseElement):
    cells: List[UDFCell] = Field(default_factory=list)
    height: Optional[float] = None

class UDFTable(UDFBaseElement):
    rows: List[UDFRow] = Field(default_factory=list)
    columnCount: int
    columnSpans: str
    border: str = "borderCell"

UDFParagraph.model_rebuild()
UDFCell.model_rebuild()
UDFRow.model_rebuild()
UDFTable.model_rebuild()
