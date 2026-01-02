from typing import Optional
from pydantic import BaseModel, Field

class UDFStyle(BaseModel):
    name: str
    description: Optional[str] = None
    family: str = "Times New Roman"
    size: float = 12.0
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strikethrough: bool = False
    foreground: int = -16777216  # Black
    background: Optional[int] = None
    subscript: bool = False
    superscript: bool = False
    parent: Optional[str] = None

    def to_xml_attrs(self) -> dict:
        attrs = {
            "name": self.name,
            "family": self.family,
            "size": str(self.size),
            "bold": str(self.bold).lower(),
            "italic": str(self.italic).lower(),
            "foreground": str(self.foreground),
        }
        if self.description:
            attrs["description"] = self.description
        if self.underline:
            attrs["underline"] = "true"
        if self.strikethrough:
            attrs["strikethrough"] = "true"
        if self.background is not None:
            attrs["background"] = str(self.background)
        if self.subscript:
            attrs["subscript"] = "true"
        if self.superscript:
            attrs["superscript"] = "true"
        if self.parent:
            attrs["parent"] = self.parent
        return attrs
