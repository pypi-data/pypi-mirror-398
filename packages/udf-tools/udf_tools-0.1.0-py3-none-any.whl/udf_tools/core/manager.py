from typing import List, Union
from udf_tools.models.elements import UDFContent, UDFTab, UDFSpace

class ContentManager:
    """Manages the root content string and updates offsets for elements."""
    def __init__(self, initial_content: str = ""):
        self.content = initial_content

    def add_text(self, text: str) -> (int, int):
        """Adds text to the end of the content and returns (startOffset, length)."""
        start_offset = len(self.content)
        self.content += text
        return start_offset, len(text)

    def insert_text(self, text: str, offset: int, elements_to_update: List[Union[UDFContent, UDFTab, UDFSpace]]):
        """Inserts text at a given offset and updates all subsequent offsets."""
        self.content = self.content[:offset] + text + self.content[offset:]
        length_diff = len(text)
        for elem in elements_to_update:
            if hasattr(elem, 'startOffset') and elem.startOffset >= offset:
                elem.startOffset += length_diff

    def get_text(self, start_offset: int, length: int) -> str:
        return self.content[start_offset:start_offset + length]
