"""
Enhanced ExtJS Parser
Extracts detailed information from ExtJS components including:
- Field definitions with types and defaults
- Method implementations
- Validators
- Event handlers
- Store configurations
- Controller actions
"""

import re
import json
from typing import Dict, List, Any, Optional


class ExtJSParser:
    """Parser for ExtJS component files."""
    
    def __init__(self):
        # Patterns for ExtJS structures
        self.define_pattern = re.compile(
            r"Ext\.define\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*\{",
            re.MULTILINE
        )
        self.extends_pattern = re.compile(
            r"extend\s*:\s*['\"]([^'\"]+)['\"]"
        )
        self.fields_pattern = re.compile(
            r"fields\s*:\s*\[(.*?)\]",
            re.DOTALL
        )
        self.method_pattern = re.compile(
            r"(\w+)\s*:\s*function\s*\((.*?)\)\s*\{(.*?)\}(?=\s*,|\s*\})",
            re.DOTALL
        )
        
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse an ExtJS file and extract its structure.
        """
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        result = {
            'file_path': file_path,
            'component_name': None,
            'extends': None,
            'component_type': None,
            'fields': [],
            'methods': [],
            'validators': [],
            'config': {},
            'raw_content': content
        }
        
        # Extract component name
        define_match = self.define_pattern.search(content)
        if define_match:
            result['component_name'] = define_match.group(1)
            result['component_type'] = self._infer_type(result['component_name'])
        
        # Extract extends
        extends_match = self.extends_pattern.search(content)
        if extends_match:
            result['extends'] = extends_match.group(1)
        
        # Extract fields (for Models)
        if 'Model' in result.get('extends', ''):
            result['fields'] = self._extract_fields(content)
            result['validators'] = self._extract_validators(content)
        
        # Extract methods
        result['methods'] = self._extract_methods(content)
        
        # Extract store configuration
        if 'Store' in result.get('extends', ''):
            result['config']['store'] = self._extract_store_config(content)
        
        # Extract controller configuration
        if 'Controller' in result.get('extends', ''):
            result['config']['controller'] = self._extract_controller_config(content)
        
        # Extract service methods
        if 'singleton' in content.lower():
            result['config']['service'] = self._extract_service_config(content)
        
        return result
    
    def _infer_type(self, component_name: str) -> str:
        """Infer component type from name."""
        name_lower = component_name.lower()
        if 'model' in name_lower:
            return 'model'
        elif 'store' in name_lower:
            return 'store'
        elif 'controller' in name_lower:
            return 'controller'
        elif 'service' in name_lower:
            return 'service'
        elif 'view' in name_lower or 'grid' in name_lower or 'form' in name_lower:
            return 'view'
        else:
            return 'utility'
    
    def _extract_fields(self, content: str) -> List[Dict[str, Any]]:
        """Extract field definitions from Model."""
        fields = []
        
        # Find fields array
        fields_match = self.fields_pattern.search(content)
        if not fields_match:
            return fields
        
        fields_content = fields_match.group(1)
        
        # Parse individual field objects
        # Pattern for field definition: { name: 'x', type: 'y', ... }
        field_pattern = re.compile(
            r"\{\s*name\s*:\s*['\"](\w+)['\"]([^}]*)\}",
            re.DOTALL
        )
        
        for match in field_pattern.finditer(fields_content):
            field_name = match.group(1)
            field_config = match.group(2)
            
            field = {
                'name': field_name,
                'type': self._extract_field_type(field_config),
                'default_value': self._extract_default_value(field_config),
                'required': 'allowBlank' in field_config and 'false' in field_config,
                'persist': 'persist:' in field_config
            }
            
            fields.append(field)
        
        return fields
    
    def _extract_field_type(self, field_config: str) -> Optional[str]:
        """Extract field type."""
        type_match = re.search(r"type\s*:\s*['\"](\w+)['\"]", field_config)
        if type_match:
            return type_match.group(1)
        return None
    
    def _extract_default_value(self, field_config: str) -> Optional[Any]:
        """Extract default value."""
        default_match = re.search(r"defaultValue\s*:\s*([^,}]+)", field_config)
        if default_match:
            value = default_match.group(1).strip()
            # Try to parse as JSON
            try:
                return json.loads(value)
            except:
                return value
        return None
    
    def _extract_validators(self, content: str) -> List[Dict[str, Any]]:
        """Extract validators from Model."""
        validators = []
        
        # Find validators object
        validators_match = re.search(
            r"validators\s*:\s*\{(.*?)\}(?=\s*,|\s*\})",
            content,
            re.DOTALL
        )
        
        if validators_match:
            validators_content = validators_match.group(1)
            
            # Extract validator functions
            validator_pattern = re.compile(
                r"(\w+)\s*:\s*(?:function\s*\((.*?)\)\s*\{(.*?)\}|['\"]([^'\"]+)['\"])",
                re.DOTALL
            )
            
            for match in validator_pattern.finditer(validators_content):
                field_name = match.group(1)
                params = match.group(2)
                implementation = match.group(3)
                simple_rule = match.group(4)
                
                validators.append({
                    'field': field_name,
                    'params': params,
                    'implementation': implementation if implementation else simple_rule,
                    'type': 'function' if implementation else 'rule'
                })
        
        return validators
    
    def _extract_methods(self, content: str) -> List[Dict[str, Any]]:
        """Extract all methods with implementations."""
        methods = []
        
        for match in self.method_pattern.finditer(content):
            method_name = match.group(1)
            params = match.group(2)
            implementation = match.group(3)
            
            # Skip certain reserved names
            if method_name in ['extend', 'requires', 'mixins', 'config']:
                continue
            
            methods.append({
                'name': method_name,
                'params': [p.strip() for p in params.split(',') if p.strip()],
                'implementation': implementation.strip(),
                'is_async': 'callback' in params or 'async' in implementation.lower(),
                'has_api_call': any(keyword in implementation for keyword in [
                    'Ajax', 'request', 'http', 'api', '.get(', '.post('
                ])
            })
        
        return methods
    
    def _extract_store_config(self, content: str) -> Dict[str, Any]:
        """Extract Store configuration."""
        config = {
            'model': None,
            'proxy': {},
            'sorters': [],
            'filters': [],
            'auto_load': False
        }
        
        # Extract model
        model_match = re.search(r"model\s*:\s*['\"]([^'\"]+)['\"]", content)
        if model_match:
            config['model'] = model_match.group(1)
        
        # Extract proxy configuration
        proxy_match = re.search(
            r"proxy\s*:\s*\{(.*?)\}(?=\s*,|\s*\})",
            content,
            re.DOTALL
        )
        if proxy_match:
            proxy_content = proxy_match.group(1)
            
            # Extract API URL
            url_match = re.search(r"url\s*:\s*['\"]([^'\"]+)['\"]", proxy_content)
            if url_match:
                config['proxy']['url'] = url_match.group(1)
            
            # Extract API methods
            api_match = re.search(r"api\s*:\s*\{(.*?)\}", proxy_content, re.DOTALL)
            if api_match:
                config['proxy']['api'] = {}
                api_content = api_match.group(1)
                for method in ['read', 'create', 'update', 'destroy']:
                    method_match = re.search(
                        rf"{method}\s*:\s*['\"]([^'\"]+)['\"]",
                        api_content
                    )
                    if method_match:
                        config['proxy']['api'][method] = method_match.group(1)
        
        # Extract autoLoad
        if 'autoLoad:' in content and 'true' in content:
            config['auto_load'] = True
        
        return config
    
    def _extract_controller_config(self, content: str) -> Dict[str, Any]:
        """Extract Controller configuration."""
        config = {
            'refs': [],
            'control': {},
            'stores': [],
            'models': []
        }
        
        # Extract refs
        refs_match = re.search(r"refs\s*:\s*\{(.*?)\}", content, re.DOTALL)
        if refs_match:
            refs_content = refs_match.group(1)
            ref_pattern = re.compile(r"(\w+)\s*:\s*['\"]([^'\"]+)['\"]")
            for match in ref_pattern.finditer(refs_content):
                config['refs'].append({
                    'name': match.group(1),
                    'selector': match.group(2)
                })
        
        # Extract control configuration
        control_match = re.search(r"control\s*:\s*\{(.*?)\}(?=\s*\}|\s*,\s*\w+:)", content, re.DOTALL)
        if control_match:
            control_content = control_match.group(1)
            # This is complex - just store the raw content for now
            config['control'] = {'raw': control_content}
        
        # Extract stores array
        stores_match = re.search(r"stores\s*:\s*\[(.*?)\]", content)
        if stores_match:
            stores_content = stores_match.group(1)
            config['stores'] = [
                s.strip().strip('"\'')
                for s in stores_content.split(',')
                if s.strip()
            ]
        
        return config
    
    def _extract_service_config(self, content: str) -> Dict[str, Any]:
        """Extract Service configuration (singleton utilities)."""
        config = {
            'singleton': True,
            'api_methods': []
        }
        
        # Extract all methods that make API calls
        for method in self._extract_methods(content):
            if method['has_api_call']:
                config['api_methods'].append(method)
        
        return config
