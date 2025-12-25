from typing import Dict, Any

class ExecutionContext:
    def __init__(self, config=None, llm_config=None, policy_config=None):
        self.artifacts: Dict[str, Any] = {}
        self.documentation: Dict[str, Any] = {}
        self.config: Dict[str, Any] = config
        self.doc_writer = None  # Will be set by orchestrator

    def add_artifact(self, key: str, value: Any):
        self.artifacts[key] = value

    def get_artifact(self, key: str) -> Any:
        return self.artifacts.get(key)

    def add_doc(self, key: str, value: Any):
        self.documentation.setdefault(key, []).append(value)
    
    def log_agent_execution(self, agent_name: str, data: Dict[str, Any]):
        """Log agent execution details to the documentation file."""
        if self.doc_writer:
            self.doc_writer.add_agent_section(agent_name, data)
