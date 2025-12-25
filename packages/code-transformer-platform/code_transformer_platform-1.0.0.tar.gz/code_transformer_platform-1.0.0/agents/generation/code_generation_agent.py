from core.agent import Agent
from core.context import ExecutionContext
from core.azure_openai_client import AzureOpenAIClient
from config.config_loader import ConfigLoader


class CodeGenerationAgent(Agent):
    name = "code-generation-agent"

    def run(self, context: ExecutionContext) -> None:
        target_cfg = ConfigLoader.load(context.config.target_config)
        llm_cfg = ConfigLoader.load(context.config.llm_config)
        policy_cfg = ConfigLoader.load(context.config.policy_config)

        llm = AzureOpenAIClient(llm_cfg)

        target_ir = context.get_artifact("target_framework_ir")

        for component in target_ir.components:
            messages = self._build_prompt(component, target_cfg, policy_cfg)
            code = llm.generate(messages)
            self._write_files(component, code, context)

    def _build_prompt(self, component, target_cfg, policy_cfg):
        system = (
            "You are a senior software architect.\n"
            f"Target framework: {target_cfg['framework']} {target_cfg['version']}.\n"
            f"Generation mode: {policy_cfg['mode']}.\n"
        )

        user = f"""
Component IR:
{component.model_dump_json(indent=2)}

Rules:
{policy_cfg['constraints']}

Framework Rules:
{target_cfg['coding_rules']}
"""

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
