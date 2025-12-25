from core.agent import Agent
from core.context import ExecutionContext
from config.config_loader import ConfigLoader
from core.artifacts import TargetMapping


class TargetMappingAgent(Agent):
    name = "target-mapping-agent"

    def run(self, context: ExecutionContext) -> None:
        migration_plan = context.get_artifact("migration_plan")
        if migration_plan is None:
            raise RuntimeError("migration_plan missing for TargetMappingAgent")

        target_cfg_path = context.config.get("target_config")
        if not target_cfg_path:
            raise RuntimeError("target_config not provided in config")

        target_cfg = ConfigLoader.load(target_cfg_path)

        mappings = []

        for step in migration_plan.steps:
            mapping = TargetMapping(
                component=step.component,
                target_framework=target_cfg["framework"],
                ui_pattern=target_cfg.get("ui_pattern", "component"),
                state_management=target_cfg.get("state_management", "local"),
                strategy="rewrite"
            )
            mappings.append(mapping)

        context.add_artifact("target_mapping", mappings)

        context.add_doc("target_mapping_summary", {
            "target_framework": target_cfg["framework"],
            "total_components": len(mappings)
        })
        
        # Log to migration analysis document
        context.log_agent_execution("Target Mapping Agent", {
            "Target Framework": target_cfg["framework"],
            "UI Pattern": target_cfg.get("ui_pattern", "component"),
            "State Management": target_cfg.get("state_management", "local"),
            "Components Mapped": len(mappings),
            "Component List": [m.component for m in mappings],
            "Migration Strategy": "rewrite"
        })

        print(
            f"[TargetMappingAgent] Mapped {len(mappings)} components "
            f"to {target_cfg['framework']}"
        )