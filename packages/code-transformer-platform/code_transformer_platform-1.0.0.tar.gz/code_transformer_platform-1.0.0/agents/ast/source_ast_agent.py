from core.agent import Agent
from core.context import ExecutionContext
from core.artifacts import ASTIndex, SourceAST, ParseReport
from adapters.source.js_adapter import JavaScriptParserAdapter
from adapters.source.xhtml_adapter import XHTMLParserAdapter


class SourceASTAgent(Agent):
    name = "source-ast-agent"

    def __init__(self):
        self.adapters = {
            "JavaScript": JavaScriptParserAdapter(),
            "TypeScript": JavaScriptParserAdapter(),
            "XHTML": XHTMLParserAdapter(),
            "HTML": XHTMLParserAdapter()
        }

    def run(self, context: ExecutionContext) -> None:
        metadata = context.get_artifact("file_metadata")

        asts = {}
        parsed = []
        failed = {}

        for file_meta in metadata:
            adapter = self.adapters.get(file_meta.language)
            if not adapter:
                continue

            try:
                ast = adapter.parse(file_meta.path)
                asts[file_meta.path] = SourceAST(
                    file_path=file_meta.path,
                    language=file_meta.language,
                    ast=ast
                )
                parsed.append(file_meta.path)

            except Exception as e:
                failed[file_meta.path] = str(e)

        context.add_artifact(
            "ast_index",
            ASTIndex(asts=asts)
        )

        context.add_artifact(
            "parse_report",
            ParseReport(
                parsed_files=parsed,
                failed_files=failed
            )
        )

        context.add_doc("ast", {
            "parsed_files": len(parsed),
            "failed_files": failed
        })
        
        # Log to migration analysis document
        context.log_agent_execution("Source AST Agent", {
            "Files Parsed Successfully": len(parsed),
            "Files Failed to Parse": len(failed),
            "Failed Files": list(failed.keys()) if failed else ["None"],
            "Supported Languages": list(self.adapters.keys())
        })
