from adapters.source.base_adapter import SourceParserAdapter
from xml.etree import ElementTree as ET


class XHTMLParserAdapter(SourceParserAdapter):
    language = "XHTML"

    def parse(self, file_path: str):
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            return {
                "root_tag": root.tag,
                "children_count": len(list(root))
            }
        except Exception as e:
            raise RuntimeError(str(e))
