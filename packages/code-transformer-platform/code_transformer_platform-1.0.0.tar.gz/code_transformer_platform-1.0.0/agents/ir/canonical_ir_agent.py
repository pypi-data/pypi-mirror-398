from core.agent import Agent
from core.context import ExecutionContext
from models.canonical_ir import (
    CanonicalIR,
    IRComponent,
    IRState,
    IRAction,
    IRDependency,
    IRView,
    IRValidator,
    IRApiConfig
)


class CanonicalIRAgent(Agent):
    name = "canonical-ir-agent"

    def run(self, context: ExecutionContext) -> None:
        ast_index = context.get_artifact("ast_index").asts
        dependency_graph = context.get_artifact("resolved_dependency_graph").internal_graph

        components = []

        for file_path, source_ast in ast_index.items():
            component = self._build_component(file_path, source_ast, dependency_graph)
            if component:
                components.append(component)

        canonical_ir = CanonicalIR(components=components)

        context.add_artifact("canonical_ir", canonical_ir)

        context.add_doc("ir", {
            "total_components": len(components),
            "component_names": [c.name for c in components]
        })
        
        # Log to migration analysis document
        context.log_agent_execution("Canonical IR Agent", {
            "Total Components": len(components),
            "Component Names": [c.name for c in components],
            "Component Types": {c.name: c.component_type for c in components}
        })

    def _build_component(self, file_path, source_ast, dependency_graph):
        # Get parsed AST data
        ast_data = source_ast.ast
        
        name = ast_data.get('component_name') or self._derive_name(file_path)
        component_type = ast_data.get('component_type') or self._infer_component_type(source_ast.language)

        state = self._extract_state(ast_data)
        actions = self._extract_actions(ast_data)
        view = self._extract_view(source_ast, ast_data)
        dependencies = self._extract_dependencies(file_path, dependency_graph)
        validators = self._extract_validators(ast_data)
        api_config = self._extract_api_config(ast_data)

        return IRComponent(
            name=name,
            component_type=component_type,
            state=state,
            actions=actions,
            view=view,
            dependencies=dependencies,
            validators=validators,
            api_config=api_config,
            raw_source=ast_data.get('raw_content', '')[:5000]  # First 5000 chars
        )

    def _derive_name(self, file_path: str) -> str:
        # Handle both forward and backward slashes
        path_parts = file_path.replace('\\', '/').split("/")
        return path_parts[-1].split(".")[0]

    def _infer_component_type(self, language: str) -> str:
        if language in ("XHTML", "HTML"):
            return "view"
        return "service"

    def _extract_state(self, ast_data):
        """Extract state/fields from parsed AST data."""
        state = []
        
        # Get fields from parsed data
        fields = ast_data.get('fields', [])
        
        if fields:
            for field in fields:
                state.append(IRState(
                    name=field.get('name', 'unknown'),
                    type=field.get('type'),
                    source="local",
                    default_value=field.get('default_value'),
                    required=field.get('required', False)
                ))
        else:
            # Fallback for non-model files
            state.append(IRState(
                name="data",
                type=None,
                source="local"
            ))
        
        return state

    def _extract_actions(self, ast_data):
        """Extract actions/methods from parsed AST data."""
        actions = []
        
        # Get methods from parsed data
        methods = ast_data.get('methods', [])
        
        if methods:
            for method in methods:
                actions.append(IRAction(
                    name=method.get('name', 'unknown'),
                    kind="async" if method.get('is_async') else "sync",
                    effects=[],  # Could be enhanced to analyze implementation
                    params=method.get('params', []),
                    implementation=method.get('implementation', ''),
                    has_api_call=method.get('has_api_call', False)
                ))
        else:
            # Fallback
            actions.append(IRAction(
                name="init",
                kind="sync",
                effects=["initialize_state"]
            ))
        
        return actions

    def _extract_view(self, source_ast, ast_data):
        """Extract view configuration."""
        if source_ast.language in ("XHTML", "HTML"):
            # Could parse XHTML to get actual structure
            return IRView(
                kind="template",
                fields=[]
            )
        return None

    def _extract_dependencies(self, file_path, dependency_graph):
        """Extract dependencies."""
        deps = []
        for dep in dependency_graph.get(file_path, []):
            dep_name = dep.replace('\\', '/').split("/")[-1].split(".")[0]
            deps.append(
                IRDependency(
                    name=dep_name,
                    type="service"
                )
            )
        return deps
    
    def _extract_validators(self, ast_data):
        """Extract validators from parsed data."""
        validators = []
        
        parsed_validators = ast_data.get('validators', [])
        
        for validator in parsed_validators:
            validators.append(IRValidator(
                field=validator.get('field', 'unknown'),
                type=validator.get('type', 'rule'),
                implementation=validator.get('implementation')
            ))
        
        return validators
    
    def _extract_api_config(self, ast_data):
        """Extract API configuration from parsed data."""
        config_data = ast_data.get('config', {})
        
        # Check store config
        store_config = config_data.get('store')
        if store_config and store_config.get('proxy'):
            proxy = store_config['proxy']
            api_methods = proxy.get('api', {})
            
            # Handle case where api is a string (raw text from parser)
            if isinstance(api_methods, str):
                # Store as empty dict if we can't parse it
                # The raw text will be in the prompt via raw_source
                api_methods = {}
            
            return IRApiConfig(
                url=proxy.get('url'),
                methods=api_methods if isinstance(api_methods, dict) else {}
            )
        
        # Check service config
        service_config = config_data.get('service')
        if service_config:
            return IRApiConfig(
                url=None,
                methods={}  # Could extract from api_methods
            )
        
        return None
