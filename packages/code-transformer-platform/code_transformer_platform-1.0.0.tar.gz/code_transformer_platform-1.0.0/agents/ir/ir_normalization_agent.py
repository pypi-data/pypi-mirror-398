from core.agent import Agent
from core.context import ExecutionContext
from models.canonical_ir import (
    CanonicalIR,
    IRComponent,
    IRAnnotation,
    IRState,
    IRAction
)


class IRNormalizationAgent(Agent):
    name = "ir-normalization-agent"

    def run(self, context: ExecutionContext) -> None:
        canonical_ir: CanonicalIR = context.get_artifact("canonical_ir")

        normalized_components = []

        for component in canonical_ir.components:
            normalized = self._normalize_component(component)
            normalized_components.append(normalized)

        normalized_ir = CanonicalIR(components=normalized_components)
        context.add_artifact("normalized_ir", normalized_ir)

        context.add_doc("ir_normalization", {
            "components_processed": len(normalized_components)
        })
        
        # Log to migration analysis document
        renamed_components = []
        ambiguous_components = []
        for comp in normalized_components:
            for ann in comp.annotations:
                if ann.key == "renamed":
                    renamed_components.append(ann.value)
                elif ann.key == "ambiguous_component":
                    ambiguous_components.append(comp.name)
        
        context.log_agent_execution("IR Normalization Agent", {
            "Components Processed": len(normalized_components),
            "Renamed Components": renamed_components if renamed_components else ["None"],
            "Ambiguous Components": ambiguous_components if ambiguous_components else ["None"],
            "Normalization Rules Applied": ["Name normalization", "Default action injection", "State name normalization", "Ambiguity detection"]
        })

    def _normalize_component(self, component: IRComponent) -> IRComponent:
        annotations = list(component.annotations)

        # 1️⃣ Normalize component name
        normalized_name = self._normalize_name(component.name)
        if normalized_name != component.name:
            annotations.append(
                IRAnnotation(
                    key="renamed",
                    value=f"{component.name} -> {normalized_name}"
                )
            )

        # 2️⃣ Ensure at least one action
        actions = component.actions
        if not actions:
            actions = [
                IRAction(
                    name="initialize",
                    kind="sync",
                    effects=["initialize_state"]
                )
            ]
            annotations.append(
                IRAnnotation(
                    key="default_action_added",
                    value="initialize"
                )
            )

        # 3️⃣ Normalize state names
        state = []
        for s in component.state:
            normalized_state_name = self._normalize_name(s.name)
            state.append(
                IRState(
                    name=normalized_state_name,
                    type=s.type,
                    source=s.source
                )
            )

        # 4️⃣ Annotate ambiguous components
        if component.component_type == "service" and component.view:
            annotations.append(
                IRAnnotation(
                    key="ambiguous_component",
                    value="service_with_view"
                )
            )

        return IRComponent(
            name=normalized_name,
            component_type=component.component_type,
            state=state,
            actions=actions,
            view=component.view,
            dependencies=component.dependencies,
            annotations=annotations
        )

    def _normalize_name(self, name: str) -> str:
        return (
            name.replace("_", " ")
            .title()
            .replace(" ", "")
        )
