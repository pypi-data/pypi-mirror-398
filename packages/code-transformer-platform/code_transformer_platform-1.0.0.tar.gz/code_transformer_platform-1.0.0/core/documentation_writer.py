from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List


class DocumentationWriter:
    """Handles writing agent execution logs and analysis to a markdown file."""
    
    def __init__(self, output_path: str):
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.doc_file = self.output_path / "migration_analysis.md"
        self._initialize_document()
    
    def _initialize_document(self):
        """Create the initial document with header."""
        with open(self.doc_file, 'w', encoding='utf-8') as f:
            f.write("# Code Migration Analysis & Execution Log\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
    
    def add_agent_section(self, agent_name: str, data: Dict[str, Any]):
        """
        Add a section for an agent's execution with enhanced formatting.
        
        Args:
            agent_name: Name of the agent
            data: Dictionary containing analysis details
        """
        with open(self.doc_file, 'a', encoding='utf-8') as f:
            f.write(f"## {agent_name}\n\n")
            f.write(f"**Timestamp:** {datetime.now().strftime('%H:%M:%S')}\n\n")
            
            # Write each key-value pair
            for key, value in data.items():
                f.write(f"### {key}\n\n")
                self._write_value(f, value, indent_level=0)
            
            f.write("---\n\n")
    
    def _write_value(self, f, value: Any, indent_level: int = 0):
        """
        Write a value with proper formatting based on its type.
        Handles nested structures recursively.
        """
        indent = "  " * indent_level
        
        if isinstance(value, list):
            if value:
                for item in value:
                    if isinstance(item, dict):
                        # Nested dictionary in list
                        for k, v in item.items():
                            f.write(f"{indent}- **{k}**: ")
                            if isinstance(v, (list, dict)):
                                f.write("\n")
                                self._write_value(f, v, indent_level + 1)
                            else:
                                f.write(f"{v}\n")
                    else:
                        f.write(f"{indent}- {item}\n")
                f.write("\n")
            else:
                f.write(f"{indent}*None found*\n\n")
        
        elif isinstance(value, dict):
            if value:
                for k, v in value.items():
                    if isinstance(v, dict):
                        # Nested dictionary
                        f.write(f"{indent}**{k}:**\n")
                        self._write_value(f, v, indent_level + 1)
                    elif isinstance(v, list):
                        # List in dictionary
                        f.write(f"{indent}**{k}:**\n")
                        self._write_value(f, v, indent_level + 1)
                    else:
                        f.write(f"{indent}**{k}:** {v}\n")
                f.write("\n")
            else:
                f.write(f"{indent}*Empty*\n\n")
        
        elif isinstance(value, str):
            if '\n' in value or len(value) > 100:
                f.write(f"{indent}```\n")
                f.write(value)
                f.write(f"\n{indent}```\n\n")
            else:
                f.write(f"{indent}{value}\n\n")
        
        else:
            f.write(f"{indent}{value}\n\n")
    
    def add_summary(self, summary: str):
        """Add a summary section at the end."""
        with open(self.doc_file, 'a', encoding='utf-8') as f:
            f.write(f"## Summary\n\n")
            f.write(f"{summary}\n\n")
    
    def get_file_path(self) -> Path:
        """Return the path to the documentation file."""
        return self.doc_file
