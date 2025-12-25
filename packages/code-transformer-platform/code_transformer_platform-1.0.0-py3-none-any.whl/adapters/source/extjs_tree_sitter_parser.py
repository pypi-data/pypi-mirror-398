"""
ExtJS Tree-Sitter Parser
Uses tree-sitter for robust AST parsing of ExtJS files.
"""

import re
from typing import Dict, List, Any, Optional
from tree_sitter import Language, Parser, Node
import tree_sitter_javascript as tsjs


class ExtJSTreeSitterParser:
    """Parse ExtJS files using tree-sitter for robust AST extraction."""
    
    def __init__(self):
        """Initialize tree-sitter parser."""
        self.JS_LANGUAGE = Language(tsjs.language())
        self.parser = Parser(self.JS_LANGUAGE)
    
    def parse(self, content: str) -> Dict[str, Any]:
        """
        Parse ExtJS file content and extract structured information.
        
        Args:
            content: JavaScript file content
            
        Returns:
            Dictionary with component_name, extends, component_type, fields, methods, etc.
        """
        tree = self.parser.parse(bytes(content, "utf8"))
        root_node = tree.root_node
        
        result = {
            'component_name': None,
            'extends': None,
            'component_type': None,
            'fields': [],
            'methods': [],
            'validators': [],
            'config': {},
            'raw_content': content
        }
        
        # Find Ext.define call
        ext_define_node = self._find_ext_define(root_node)
        if ext_define_node:
            result['component_name'] = self._extract_component_name(ext_define_node)
            config_object = self._get_config_object(ext_define_node)
            
            if config_object:
                result['extends'] = self._extract_extends(config_object)
                result['component_type'] = self._infer_component_type(result['extends'])
                result['fields'] = self._extract_fields(config_object, content)
                result['methods'] = self._extract_methods(config_object, content)
                result['validators'] = self._extract_validators(config_object, content)
                result['config'] = self._extract_config(config_object, content)
        
        return result
    
    def _find_ext_define(self, node: Node) -> Optional[Node]:
        """Find Ext.define() call expression."""
        if node.type == 'call_expression':
            callee = node.child_by_field_name('function')
            if callee and self._is_ext_define_callee(callee):
                return node
        
        for child in node.children:
            result = self._find_ext_define(child)
            if result:
                return result
        
        return None
    
    def _is_ext_define_callee(self, node: Node) -> bool:
        """Check if node represents Ext.define."""
        if node.type == 'member_expression':
            obj = node.child_by_field_name('object')
            prop = node.child_by_field_name('property')
            if obj and prop:
                return (obj.text.decode('utf8') == 'Ext' and 
                        prop.text.decode('utf8') == 'define')
        return False
    
    def _extract_component_name(self, ext_define_node: Node) -> Optional[str]:
        """Extract component name from Ext.define first argument."""
        args = ext_define_node.child_by_field_name('arguments')
        if args and len(args.children) > 1:
            first_arg = args.children[1]  # Skip opening paren
            if first_arg.type == 'string':
                name = first_arg.text.decode('utf8').strip('"\'')
                return name
        return None
    
    def _get_config_object(self, ext_define_node: Node) -> Optional[Node]:
        """Get the configuration object (second argument) from Ext.define."""
        args = ext_define_node.child_by_field_name('arguments')
        if args:
            # Find the object expression (skip commas)
            for child in args.children:
                if child.type == 'object':
                    return child
        return None
    
    def _extract_extends(self, config_object: Node) -> Optional[str]:
        """Extract the 'extend' property value."""
        extends_prop = self._find_property(config_object, 'extend')
        if extends_prop:
            value = self._get_property_value(extends_prop)
            if value:
                return value.text.decode('utf8').strip('"\'')
        return None
    
    def _infer_component_type(self, extends: Optional[str]) -> str:
        """Infer component type from extends value."""
        if not extends:
            return 'unknown'
        
        extends_lower = extends.lower()
        if 'model' in extends_lower:
            return 'model'
        elif 'store' in extends_lower:
            return 'store'
        elif 'controller' in extends_lower:
            return 'controller'
        elif 'view' in extends_lower or 'panel' in extends_lower or 'window' in extends_lower:
            return 'view'
        elif 'viewport' in extends_lower:
            return 'view'
        else:
            return 'utility'
    
    def _extract_fields(self, config_object: Node, content: str) -> List[Dict[str, Any]]:
        """Extract fields array from model configuration."""
        fields = []
        fields_prop = self._find_property(config_object, 'fields')
        
        if fields_prop:
            value = self._get_property_value(fields_prop)
            if value and value.type == 'array':
                for child in value.children:
                    if child.type == 'object':
                        field = self._parse_field_object(child, content)
                        if field:
                            fields.append(field)
                    elif child.type == 'string':
                        # Simple field name as string
                        field_name = child.text.decode('utf8').strip('"\'')
                        fields.append({
                            'name': field_name,
                            'type': None,
                            'default_value': None,
                            'required': False
                        })
        
        return fields
    
    def _parse_field_object(self, field_node: Node, content: str) -> Optional[Dict[str, Any]]:
        """Parse a field object {name: 'x', type: 'string', ...}."""
        field = {
            'name': None,
            'type': None,
            'default_value': None,
            'required': False
        }
        
        name_prop = self._find_property(field_node, 'name')
        if name_prop:
            value = self._get_property_value(name_prop)
            if value:
                field['name'] = value.text.decode('utf8').strip('"\'')
        
        type_prop = self._find_property(field_node, 'type')
        if type_prop:
            value = self._get_property_value(type_prop)
            if value:
                field['type'] = value.text.decode('utf8').strip('"\'')
        
        default_prop = self._find_property(field_node, 'defaultValue')
        if default_prop:
            value = self._get_property_value(default_prop)
            if value:
                field['default_value'] = value.text.decode('utf8')
        
        # Check for allowBlank or required validators
        allow_blank = self._find_property(field_node, 'allowBlank')
        if allow_blank:
            value = self._get_property_value(allow_blank)
            if value and value.text.decode('utf8') == 'false':
                field['required'] = True
        
        return field if field['name'] else None
    
    def _extract_methods(self, config_object: Node, content: str) -> List[Dict[str, Any]]:
        """Extract all methods from the configuration object."""
        methods = []
        
        for child in config_object.children:
            if child.type == 'pair':
                key_node = child.child_by_field_name('key')
                value_node = child.child_by_field_name('value')
                
                if key_node and value_node:
                    method_name = self._get_node_text(key_node).strip('"\'')
                    
                    # Check if value is a function
                    if value_node.type in ('function', 'function_expression', 'arrow_function'):
                        method_info = {
                            'name': method_name,
                            'params': self._extract_function_params(value_node),
                            'implementation': self._get_node_text(value_node),
                            'is_async': self._is_async_function(value_node),
                            'has_api_call': self._has_api_call(value_node, content)
                        }
                        methods.append(method_info)
        
        return methods
    
    def _extract_function_params(self, function_node: Node) -> List[str]:
        """Extract parameter names from function node."""
        params = []
        params_node = function_node.child_by_field_name('parameters')
        
        if params_node:
            for child in params_node.children:
                if child.type in ('identifier', 'required_parameter'):
                    params.append(child.text.decode('utf8'))
        
        return params
    
    def _is_async_function(self, function_node: Node) -> bool:
        """Check if function is async."""
        # Look for async keyword in parent or function itself
        text = function_node.text.decode('utf8')
        return 'async' in text[:50]  # Check first 50 chars
    
    def _has_api_call(self, function_node: Node, content: str) -> bool:
        """Check if function contains API/AJAX calls."""
        text = function_node.text.decode('utf8')
        api_patterns = [
            'Ext.Ajax', 'fetch(', 'axios.', '$.ajax',
            'XMLHttpRequest', 'http.get', 'http.post'
        ]
        return any(pattern in text for pattern in api_patterns)
    
    def _extract_validators(self, config_object: Node, content: str) -> List[Dict[str, Any]]:
        """Extract validators from fields or separate validators config."""
        validators = []
        
        # Check fields for inline validators
        fields_prop = self._find_property(config_object, 'fields')
        if fields_prop:
            value = self._get_property_value(fields_prop)
            if value and value.type == 'array':
                for child in value.children:
                    if child.type == 'object':
                        field_validators = self._extract_field_validators(child, content)
                        validators.extend(field_validators)
        
        return validators
    
    def _extract_field_validators(self, field_node: Node, content: str) -> List[Dict[str, Any]]:
        """Extract validators from a single field object."""
        validators = []
        
        field_name = None
        name_prop = self._find_property(field_node, 'name')
        if name_prop:
            value = self._get_property_value(name_prop)
            if value:
                field_name = value.text.decode('utf8').strip('"\'')
        
        # Check for validate function
        validate_prop = self._find_property(field_node, 'validate')
        if validate_prop and field_name:
            value = self._get_property_value(validate_prop)
            if value:
                validators.append({
                    'field': field_name,
                    'type': 'function',
                    'implementation': self._get_node_text(value)
                })
        
        # Check for allowBlank
        allow_blank = self._find_property(field_node, 'allowBlank')
        if allow_blank and field_name:
            value = self._get_property_value(allow_blank)
            if value and value.text.decode('utf8') == 'false':
                validators.append({
                    'field': field_name,
                    'type': 'required',
                    'implementation': 'allowBlank: false'
                })
        
        return validators
    
    def _extract_config(self, config_object: Node, content: str) -> Dict[str, Any]:
        """Extract store, controller, or service configurations."""
        config = {}
        
        # Store configuration
        store_config = self._extract_store_config(config_object)
        if store_config:
            config['store'] = store_config
        
        # Controller configuration
        controller_config = self._extract_controller_config(config_object)
        if controller_config:
            config['controller'] = controller_config
        
        return config
    
    def _extract_store_config(self, config_object: Node) -> Optional[Dict[str, Any]]:
        """Extract store-specific configuration."""
        model_prop = self._find_property(config_object, 'model')
        proxy_prop = self._find_property(config_object, 'proxy')
        
        if not (model_prop or proxy_prop):
            return None
        
        store_config = {}
        
        if model_prop:
            value = self._get_property_value(model_prop)
            if value:
                store_config['model'] = value.text.decode('utf8').strip('"\'')
        
        if proxy_prop:
            proxy_value = self._get_property_value(proxy_prop)
            if proxy_value and proxy_value.type == 'object':
                proxy_config = {}
                
                url_prop = self._find_property(proxy_value, 'url')
                if url_prop:
                    url_value = self._get_property_value(url_prop)
                    if url_value:
                        proxy_config['url'] = url_value.text.decode('utf8').strip('"\'')
                
                api_prop = self._find_property(proxy_value, 'api')
                if api_prop:
                    api_value = self._get_property_value(api_prop)
                    if api_value:
                        # Try to parse as object
                        if api_value.type == 'object':
                            api_dict = {}
                            for child in api_value.children:
                                if child.type == 'pair':
                                    key_node = child.child_by_field_name('key')
                                    value_node = child.child_by_field_name('value')
                                    if key_node and value_node:
                                        key = self._get_node_text(key_node).strip('"\'')
                                        val = self._get_node_text(value_node).strip('"\'')
                                        api_dict[key] = val
                            proxy_config['api'] = api_dict
                        else:
                            # Fallback to raw text
                            proxy_config['api'] = self._get_node_text(api_value)
                
                if proxy_config:
                    store_config['proxy'] = proxy_config
        
        return store_config if store_config else None
    
    def _extract_controller_config(self, config_object: Node) -> Optional[Dict[str, Any]]:
        """Extract controller-specific configuration."""
        refs_prop = self._find_property(config_object, 'refs')
        control_prop = self._find_property(config_object, 'control')
        
        if not (refs_prop or control_prop):
            return None
        
        controller_config = {}
        
        if refs_prop:
            value = self._get_property_value(refs_prop)
            if value:
                controller_config['refs'] = self._get_node_text(value)
        
        if control_prop:
            value = self._get_property_value(control_prop)
            if value:
                controller_config['control'] = self._get_node_text(value)
        
        return controller_config if controller_config else None
    
    def _find_property(self, object_node: Node, property_name: str) -> Optional[Node]:
        """Find a property by name in an object node."""
        for child in object_node.children:
            if child.type == 'pair':
                key_node = child.child_by_field_name('key')
                if key_node:
                    key_text = self._get_node_text(key_node).strip('"\'')
                    if key_text == property_name:
                        return child
        return None
    
    def _get_property_value(self, pair_node: Node) -> Optional[Node]:
        """Get the value node from a property pair."""
        return pair_node.child_by_field_name('value')
    
    def _get_node_text(self, node: Node) -> str:
        """Get text content of a node."""
        return node.text.decode('utf8')
