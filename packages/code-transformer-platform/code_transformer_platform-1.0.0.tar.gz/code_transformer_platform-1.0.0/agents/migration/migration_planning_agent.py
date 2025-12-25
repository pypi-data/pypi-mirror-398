from core.agent import Agent
from core.context import ExecutionContext
from models.migration_plan import MigrationPlan, MigrationStep


class MigrationPlanningAgent(Agent):
    name = "migration-planning-agent"

    def run(self, context: ExecutionContext) -> None:
        ir = context.get_artifact("normalized_ir")
        scan_index = context.get_artifact("scan_index")
        dep_graph_artifact = context.get_artifact("resolved_dependency_graph")

        if ir is None:
            raise RuntimeError("normalized_ir missing for MigrationPlanningAgent")

        if scan_index is None:
            raise RuntimeError("scan_index missing for MigrationPlanningAgent")

        dependency_graph = (
            dep_graph_artifact.internal_graph
            if dep_graph_artifact is not None
            else {}
        )

        steps = []
        step_id = 1

        ordered_components = self._order_components(
            ir.components, dependency_graph
        )

        for component in ordered_components:
            deps = [d.name for d in getattr(component, "dependencies", [])]
            files = scan_index.component_to_files.get(component.name, [])

            step = MigrationStep(
                step_id=step_id,
                component=component.name,
                depends_on=deps,
                files=files,
                risk_level=self._assess_risk(component),
                notes=self._build_notes(component)
            )

            steps.append(step)
            step_id += 1

        plan = MigrationPlan(
            source_stack=context.config.get("source_stack", "unknown"),
            target_stack=context.config.get("target_stack", "unknown"),
            steps=steps
        )

        context.add_artifact("migration_plan", plan)

        context.add_doc("migration_plan_summary", {
            "total_steps": len(steps),
            "high_risk_components": [
                s.component for s in steps if s.risk_level == "high"
            ]
        })
        
        # Log to migration analysis document
        context.log_agent_execution("Migration Planning Agent", {
            "Source Stack": context.config.get("source_stack", "unknown"),
            "Target Stack": context.config.get("target_stack", "unknown"),
            "Total Migration Steps": len(steps),
            "Component Order": [s.component for s in steps],
            "High Risk Components": [s.component for s in steps if s.risk_level == "high"],
            "Medium Risk Components": [s.component for s in steps if s.risk_level == "medium"],
            "Low Risk Components": [s.component for s in steps if s.risk_level == "low"]
        })

        print(f"[MigrationPlanningAgent] Generated {len(steps)} migration steps")

    # -------------------------
    # Internal helpers
    # -------------------------

    def _order_components(self, components, dependency_graph):
        """
        NOTE:
        This is a heuristic fallback ordering.
        Replace with real topo-sort later.
        """
        return sorted(
            components,
            key=lambda c: len(getattr(c, "dependencies", []))
        )

    def _assess_risk(self, component):
        if getattr(component, "annotations", None):
            return "high"
        if len(getattr(component, "dependencies", [])) > 3:
            return "medium"
        return "low"

    def _build_notes(self, component):
        notes = []
        for ann in getattr(component, "annotations", []):
            notes.append(f"{ann.key}: {ann.value}")
        return notes
