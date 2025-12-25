import os
from collections import defaultdict
from core.agent import Agent
from core.context import ExecutionContext
from core.artifacts import (
    DependencyGraph,
    ResolvedDependencyGraph,
    ExternalDependencies,
    DependencyReport
)


class DependencyResolutionAgent(Agent):
    name = "dependency-resolution-agent"

    def run(self, context: ExecutionContext) -> None:
        raw_graph: DependencyGraph = context.get_artifact("dependency_graph")
        file_inventory = context.get_artifact("file_inventory").files

        file_set = set(file_inventory)

        internal_graph = defaultdict(list)
        external_deps = set()

        # Normalize and classify dependencies
        for src, deps in raw_graph.graph.items():
            for dep in deps:
                resolved = self._resolve_dependency(src, dep)

                if resolved and resolved in file_set:
                    internal_graph[src].append(resolved)
                else:
                    external_deps.add(dep)

        cycles = self._detect_cycles(internal_graph)
        entry_points = self._find_entry_points(internal_graph)

        # Store artifacts
        context.add_artifact(
            "resolved_dependency_graph",
            ResolvedDependencyGraph(internal_graph=dict(internal_graph))
        )
        context.add_artifact(
            "external_dependencies",
            ExternalDependencies(dependencies=sorted(external_deps))
        )
        context.add_artifact(
            "dependency_report",
            DependencyReport(
                cyclic_dependencies=cycles,
                entry_points=entry_points
            )
        )

        # Documentation
        context.add_doc("dependencies", {
            "external_dependencies": sorted(external_deps),
            "cycle_count": len(cycles),
            "entry_points": entry_points
        })
        
        # Log to migration analysis document
        context.log_agent_execution("Dependency Resolution Agent", {
            "Total Internal Dependencies": len(internal_graph),
            "External Dependencies": sorted(external_deps),
            "Cyclic Dependencies Detected": len(cycles),
            "Cycles": [" -> ".join(cycle) for cycle in cycles] if cycles else ["None"],
            "Entry Points": entry_points if entry_points else ["None"]
        })

    def _resolve_dependency(self, src: str, dep: str) -> str | None:
        """
        Try to resolve relative imports to absolute file paths.
        """
        if dep.startswith("."):
            base = os.path.dirname(src)
            candidate = os.path.normpath(os.path.join(base, dep))

            for ext in [".js", ".ts", ".py", ".java"]:
                if os.path.exists(candidate + ext):
                    return candidate + ext

        return None

    def _detect_cycles(self, graph):
        visited = set()
        stack = set()
        cycles = []

        def dfs(node, path):
            if node in stack:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:])
                return
            if node in visited:
                return

            visited.add(node)
            stack.add(node)

            for neighbor in graph.get(node, []):
                dfs(neighbor, path + [neighbor])

            stack.remove(node)

        for node in graph:
            dfs(node, [node])

        return cycles

    def _find_entry_points(self, graph):
        all_nodes = set(graph.keys())
        dependent_nodes = set()

        for deps in graph.values():
            dependent_nodes.update(deps)

        return list(all_nodes - dependent_nodes)

