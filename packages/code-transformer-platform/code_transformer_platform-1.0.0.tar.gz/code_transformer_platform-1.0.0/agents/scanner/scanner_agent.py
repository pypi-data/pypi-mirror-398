import os
import re
from collections import defaultdict
from core.agent import Agent
from core.context import ExecutionContext
from core.artifacts import (
    FileInventory,
    FileMetadata,
    DependencyGraph,
    LanguageSummary,
    ScanIndex
)


class ScannerAgent(Agent):
    name = "scanner-agent"

    SUPPORTED_EXTENSIONS = {
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".py": "Python",
        ".java": "Java",
        ".html": "HTML",
        ".xhtml": "XHTML",
        ".css": "CSS"
    }

    IMPORT_PATTERNS = [
        re.compile(r"import\s+.*?from\s+['\"](.*?)['\"]"),
        re.compile(r"require\(['\"](.*?)['\"]\)"),
        re.compile(r"#include\s+['\"](.*?)['\"]")
    ]

    def run(self, context: ExecutionContext) -> None:
        print(context.config.keys())
        root = context.config.get("input_path")
        if not root:
            raise RuntimeError("ScannerAgent requires config.input_path")

        files = []
        metadata = []
        dependency_graph = defaultdict(list)
        language_count = defaultdict(int)
        component_to_files = defaultdict(list)

        for dirpath, _, filenames in os.walk(root):
            component = os.path.basename(dirpath)

            for filename in filenames:
                ext = os.path.splitext(filename)[1]
                if ext not in self.SUPPORTED_EXTENSIONS:
                    continue

                full_path = os.path.join(dirpath, filename)
                files.append(full_path)
                component_to_files[component].append(full_path)

                language = self.SUPPORTED_EXTENSIONS[ext]
                language_count[language] += 1

                metadata.append(
                    FileMetadata(
                        path=full_path,
                        extension=ext,
                        language=language,
                        role=self._infer_role(filename)
                    )
                )

                dependency_graph[full_path] = self._extract_dependencies(full_path)

        # === Artifacts ===
        context.add_artifact("file_inventory", FileInventory(files=files))
        context.add_artifact("file_metadata", metadata)
        context.add_artifact(
            "dependency_graph",
            DependencyGraph(graph=dict(dependency_graph))
        )
        context.add_artifact(
            "language_summary",
            LanguageSummary(languages=dict(language_count))
        )
        context.add_artifact(
            "scan_index",
            ScanIndex(component_to_files=dict(component_to_files))
        )

        # === Documentation ===
        context.add_doc("scanner", {
            "total_files": len(files),
            "components": list(component_to_files.keys()),
            "languages": dict(language_count),
            "root_path": root
        })
        
        # Log to migration analysis document
        context.log_agent_execution("Scanner Agent", {
            "Root Path": root,
            "Total Files Scanned": len(files),
            "Components Discovered": list(component_to_files.keys()),
            "Languages Detected": dict(language_count),
            "Files by Component": {k: len(v) for k, v in component_to_files.items()}
        })

        print(f"[ScannerAgent] Components discovered: {list(component_to_files.keys())}")

    def _infer_role(self, filename: str) -> str:
        name = filename.lower()
        if "test" in name:
            return "test"
        if "service" in name or "api" in name:
            return "service"
        if "util" in name or "helper" in name:
            return "utility"
        if name.endswith((".html", ".xhtml")):
            return "template"
        return "source"

    def _extract_dependencies(self, file_path: str):
        deps = set()
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                for pattern in self.IMPORT_PATTERNS:
                    deps.update(pattern.findall(content))
        except Exception:
            pass
        return list(deps)
