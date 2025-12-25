import ast as py_ast  # placeholder for structure
from adapters.source.base_adapter import SourceParserAdapter
from adapters.source.extjs_tree_sitter_parser import ExtJSTreeSitterParser
from adapters.source.extjs_parser import ExtJSParser


class JavaScriptParserAdapter(SourceParserAdapter):
    language = "JavaScript"
    
    def __init__(self):
        super().__init__()
        self.tree_sitter_parser = ExtJSTreeSitterParser()
        self.regex_parser = ExtJSParser()

    def parse(self, file_path: str):
        """
        Parse JavaScript/ExtJS files using tree-sitter, fallback to regex parser.
        """
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
        
        # Try tree-sitter parser first (most robust)
        try:
            result = self.tree_sitter_parser.parse(source)
            result['file_path'] = file_path
            result['type'] = 'Program'
            return result
        except Exception as e:
            print(f"Warning: Tree-sitter parsing failed for {file_path}: {e}")
            
            # Fallback to regex parser
            try:
                result = self.regex_parser.parse(file_path)
                return result
            except Exception as e2:
                # Final fallback
                print(f"Warning: Regex parsing failed for {file_path}: {e2}")
                return {
                    "type": "Program",
                    "file_path": file_path,
                    "component_name": None,
                    "raw_content": source,
                "parse_error": str(e)
            }
