import argparse
from core.context import ExecutionContext
from core.orchestrator import Orchestrator

# === Agents ===
from agents.scanner.scanner_agent import ScannerAgent
from agents.dependency.dependency_agent import DependencyResolutionAgent
from agents.ast.source_ast_agent import SourceASTAgent
from agents.ir.canonical_ir_agent import CanonicalIRAgent
from agents.ir.ir_normalization_agent import IRNormalizationAgent
from agents.migration.migration_planning_agent import MigrationPlanningAgent
from agents.mapping.target_mapping_agent import TargetMappingAgent
from agents.generation.target_code_generation import TargetCodeGenerationAgent


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Code Transformer Platform (Multi-Agent Migration Tool)"
    )

    # ---- Core Inputs ----
    parser.add_argument(
        "--input-path",
        required=True,
        help="Root folder of legacy source code"
    )

    parser.add_argument(
        "--output-path",
        default="./output",
        help="Output folder for migrated code (default: ./output)"
    )

    # ---- Configs ----
    parser.add_argument(
        "--target-config",
        required=True,
        help="Target framework config YAML (e.g. angular18.yaml)"
    )

    parser.add_argument(
        "--llm-config",
        required=True,
        help="LLM provider config YAML (Azure OpenAI, OpenAI, etc.)"
    )

    parser.add_argument(
        "--policy-config",
        required=True,
        help="Generation & migration policy YAML"
    )

    # ---- Metadata ----
    parser.add_argument(
        "--source-stack",
        default="legacy",
        help="Source technology stack (e.g. extjs+xhtml)"
    )

    parser.add_argument(
        "--target-stack",
        default="angular18",
        help="Target technology stack"
    )

    # ---- Execution Flags ----
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run pipeline without generating code"
    )

    return parser


def main():
    parser = build_arg_parser()
    args = parser.parse_args()


    # === Execution Context ===
    context = ExecutionContext(
        config={
            "input_path": args.input_path,
            "output_path": args.output_path,
            "target_config": args.target_config,
            "llm_config": args.llm_config,
            "policy_config": args.policy_config,
            "source_stack": args.source_stack,
            "target_stack": args.target_stack,
            "dry_run": args.dry_run
        }
    )

    # === Agent Pipeline ===
    orchestrator = Orchestrator(
        agents=[
            ScannerAgent(),
            DependencyResolutionAgent(),
            SourceASTAgent(),
            CanonicalIRAgent(),
            IRNormalizationAgent(),
            MigrationPlanningAgent(),
            TargetMappingAgent(),
            TargetCodeGenerationAgent(),  # ← next step
        ]
    )

    print("\n=== Starting Code Transformation Pipeline ===\n")

    orchestrator.run(context)

    print("\n=== Pipeline Completed Successfully ===\n")

    # ---- Optional summaries ----
    if context.get_artifact("migration_plan"):
        plan = context.get_artifact("migration_plan")
        print(f"Migration steps generated: {len(plan.steps)}")

    if context.get_artifact("target_mapping"):
        print("Target mapping completed")

    if context.get_artifact("generated_code"):
        generated = context.get_artifact("generated_code")
        print(f"\nGenerated {len(generated)} file(s)")
        print(f"Output location: {args.output_path}")
        for file_path in generated.keys():
            print(f"  - {file_path}")

    if args.dry_run:
        print("Dry run enabled — no code generated")
    
    # Show documentation file location
    if context.doc_writer:
        print(f"\n📄 Migration analysis documented in:")
        print(f"   {context.doc_writer.get_file_path()}")


if __name__ == "__main__":
    main()
