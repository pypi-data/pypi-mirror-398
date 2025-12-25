# Code Transformer Platform

## Prerequisites

### Environment Variables

Before running the platform, set the following environment variables for Azure OpenAI:

```powershell
$env:AZURE_OPENAI_API_KEY = "your-api-key-here"
$env:AZURE_OPENAI_ENDPOINT = "https://your-endpoint.openai.azure.com/"
```

Or in bash:
```bash
export AZURE_OPENAI_API_KEY="your-api-key-here"
export AZURE_OPENAI_ENDPOINT="https://your-endpoint.openai.azure.com/"
```

## Features

- **Multi-Agent Pipeline**: Orchestrates 8 specialized agents for code transformation
- **Automated Documentation**: Every agent logs its analysis to `migration_analysis.md`
- **Dependency Analysis**: Detects cycles, entry points, and external dependencies
- **Risk Assessment**: Categorizes components by migration risk level
- **LLM-Powered Generation**: Uses Azure OpenAI for intelligent code generation
- **Separate File Output**: Each component generates its own file

## Usage

### Basic Command

```bash
python -m cli.main --input-path ./legacy --output-path ./output --target-config config/targets/angular18.yaml --source-stack extjs+xhtml --target-stack angular18 --llm-config config/llm/azure_openai.yaml --policy-config config/llm/generation_policy.yaml
```

### With Custom Output Directory

```bash
python -m cli.main --input-path ./legacy --output-path ./migrated-code --target-config config/targets/angular18.yaml --llm-config config/llm/azure_openai.yaml --policy-config config/llm/generation_policy.yaml
```

### Alternative Command

```bash
python -m cli.main ./legacy --target-config config/target/angular18.yaml --llm-config config/llm/azure_openai.yaml --policy-config config/llm/generation_policy.yaml
```

## Output Files

After running the pipeline, you'll find in your output directory:

### Directory Structure
```
output/
├── generated/                    # Clean, formatted generated code
│   ├── ComponentName1/
│   │   ├── component.component.ts
│   │   ├── component.component.html
│   │   ├── component.component.css
│   │   └── component.service.ts
│   └── ComponentName2/
│       └── ...
├── prompts_log/                  # LLM interaction logs
│   ├── prompt_Component1_*.txt   # Prompts sent to LLM
│   ├── prompt_Component2_*.txt
│   └── responses/                # Raw LLM responses
│       ├── response_Component1_*.txt
│       └── response_Component2_*.txt
└── migration_analysis.md         # Comprehensive migration report

```

### Files Explained

1. **generated/** - Production-ready migrated code files
   - Each component in its own subdirectory
   - Properly formatted TypeScript/HTML/CSS
   - Ready for integration into your Angular project

2. **prompts_log/** - Debugging and analysis
   - Shows exactly what was sent to the LLM
   - Contains original source code, dependencies, and instructions
   - Helps understand and improve the migration process

3. **prompts_log/responses/** - Raw LLM output
   - Unprocessed responses from Azure OpenAI
   - Useful for debugging parsing issues
   - Contains metadata like token usage

4. **migration_analysis.md** - Complete audit trail documenting:
   - Files scanned and components discovered
   - Dependency resolution and cycles detected
   - AST parsing results
   - IR transformation details
   - Migration plan with risk assessment
   - Code generation metadata

This comprehensive output provides full traceability and easy access to both the migrated code and the migration process details.

**Note:** If `--output-path` is not specified, the default output directory is `./output`
