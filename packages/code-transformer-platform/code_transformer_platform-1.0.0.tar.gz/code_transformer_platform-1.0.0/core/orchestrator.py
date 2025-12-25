from typing import List
from core.agent import Agent
from core.context import ExecutionContext
from core.documentation_writer import DocumentationWriter
from rich.console import Console


class Orchestrator:
    """
    Controls agent execution order and lifecycle.
    """

    def __init__(self, agents: List[Agent]):
        self.agents = agents
        self.console = Console()

    def run(self, context: ExecutionContext):
        # Initialize documentation writer
        output_path = context.config.get("output_path", "./output")
        context.doc_writer = DocumentationWriter(output_path)
        
        self.console.rule("[bold blue]Starting Code Transformation Pipeline")
        self.console.print(f"[cyan]Documentation: {context.doc_writer.get_file_path()}[/cyan]\n")

        for agent in self.agents:
            self.console.print(f"[bold green]Running agent:[/bold green] {agent.name}")
            agent.run(context)

        self.console.rule("[bold blue]Pipeline Completed")
