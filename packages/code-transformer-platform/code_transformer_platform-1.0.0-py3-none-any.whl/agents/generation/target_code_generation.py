from core.agent import Agent
from core.context import ExecutionContext
from config.config_loader import ConfigLoader
from typing import Dict
import os
import json
import re
from openai import AzureOpenAI
from dotenv import load_dotenv
from pathlib import Path


class TargetCodeGenerationAgent(Agent):
    name = "target-code-generation-agent"

    def __init__(self):
        super().__init__()
        self.llm_config = None
        self.policy_config = None
        self.client = None

    def run(self, context: ExecutionContext) -> None:
        # Load configurations
        llm_config_path = context.config.get("llm_config")
        policy_config_path = context.config.get("policy_config")
        
        self.llm_config = ConfigLoader.load(llm_config_path)
        self.policy_config = ConfigLoader.load(policy_config_path)
        
        # Initialize Azure OpenAI client
        self._initialize_llm_client()
        
        # Store output path for logging
        self.output_path = Path(context.config.get("output_path", "./output"))
        
        normalized_ir = context.get_artifact("normalized_ir")
        migration_plan = context.get_artifact("migration_plan")

        generated_files = {}

        for step in migration_plan.steps:
            component_ir = self._find_component(normalized_ir, step.component)

            prompt = self._build_prompt(component_ir, step, context)

            print(f"\nGenerating code for component: {step.component}")
            code = self._call_llm(prompt, component_ir.name)

            generated_files.update(code)

        context.add_artifact("generated_code", generated_files)
        
        # Log detailed information to migration analysis document
        self._log_migration_summary(context, migration_plan, generated_files)
        
        # Write generated files to disk
        if not context.config.get("dry_run"):
            self._write_files_to_disk(generated_files, context)

    def _find_component(self, ir, name):
        return next(c for c in ir.components if c.name == name)

    def _to_kebab_case(self, text: str) -> str:
        """Convert text to kebab-case for filenames."""
        # Replace non-alphanumeric characters with hyphens
        text = re.sub(r'[^a-zA-Z0-9]+', '-', text)
        # Convert camelCase to kebab-case
        text = re.sub(r'([a-z])([A-Z])', r'\1-\2', text)
        # Convert to lowercase and remove leading/trailing hyphens
        return text.lower().strip('-')

    def _write_files_to_disk(self, generated_files: Dict[str, str], context: ExecutionContext) -> None:
        """Write generated code files to the output directory."""
        output_path = Path(context.config.get("output_path", "./output"))
        output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"\nWriting {len(generated_files)} file(s) to {output_path.absolute()}...")
        
        for relative_path, code_content in generated_files.items():
            file_path = output_path / relative_path
            
            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code_content)
            
            print(f"  ✓ {relative_path}")
        
        print(f"\nAll files written successfully to {output_path.absolute()}")

    def _build_prompt(self, component_ir, step, context: ExecutionContext) -> str:
        """Build comprehensive prompt with original source code and context."""
        
        # Get original source code
        original_code = self._get_original_source(component_ir.name, context)
        
        # Get related dependency files
        related_files = self._get_related_files(component_ir, context)
        
        # Get migration patterns for this component type
        patterns = self._get_migration_patterns(component_ir.component_type)
        
        # Format the IR for better readability (Pydantic v2)
        ir_json = component_ir.model_dump_json(indent=2)
        
        print(f"\n{'='*80}")
        print(f"BUILDING PROMPT FOR: {component_ir.name}")
        print(f"{'='*80}")
        print(f"Component Type: {component_ir.component_type}")
        print(f"Dependencies: {[dep.name for dep in component_ir.dependencies]}")
        print(f"Original Source Length: {len(original_code)} characters")
        print(f"Related Files: {len(related_files)}")
        print(f"{'='*80}\n")
        
        prompt = f"""ROLE: Expert Angular 18 architect specializing in ExtJS to Angular migrations

TASK: Migrate the following ExtJS component to Angular 18, preserving ALL business logic and functionality

{'='*80}
ORIGINAL SOURCE CODE
{'='*80}
Component: {component_ir.name}
Type: {component_ir.component_type}

```javascript
{original_code}
```

{'='*80}
RELATED DEPENDENCY FILES
{'='*80}
{self._format_related_files(related_files)}

{'='*80}
CANONICAL IR (Extracted Structure)
{'='*80}
{ir_json}

{'='*80}
MIGRATION REQUIREMENTS
{'='*80}
1. **Preserve ALL Business Logic**: Every method, calculation, validation, and transformation must be migrated exactly
2. **Maintain Data Structures**: Keep the same field names, types, and relationships
3. **Keep Validation Rules**: All validators, formatters, and error messages must be preserved
4. **Replicate User Interactions**: All event handlers and UI logic must work identically
5. **Maintain API Integration**: All service calls and data transformations must be preserved

{'='*80}
ANGULAR 18 TECHNICAL REQUIREMENTS
{'='*80}
- Use standalone components (no NgModule)
- Apply TypeScript strict mode with proper typing
- Use reactive forms for data binding
- Implement RxJS for async operations (Observables, BehaviorSubject)
- Use HttpClient for API calls with proper typing
- Follow Angular style guide and naming conventions
- Use signals for state management where appropriate
- Implement proper error handling with catchError and throwError

{'='*80}
MIGRATION PATTERNS TO FOLLOW
{'='*80}
{patterns}

{'='*80}
MIGRATION CONTEXT
{'='*80}
Component Name: {step.component}
Dependencies: {', '.join(step.depends_on) if step.depends_on else 'None'}
Risk Level: {step.risk_level}

{'='*80}
EXPECTED OUTPUT FORMAT
{'='*80}
Return a JSON object where keys are file paths and values are the complete file contents.

Example structure:
{{
  "{self._to_kebab_case(component_ir.name)}.component.ts": "import {{ Component }} from '@angular/core';\\n\\n@Component({{...}})",
  "{self._to_kebab_case(component_ir.name)}.component.html": "<div>...</div>",
  "{self._to_kebab_case(component_ir.name)}.component.css": ".container {{ ... }}",
  "{self._to_kebab_case(component_ir.name)}.service.ts": "import {{ Injectable }} from '@angular/core';\\n..." (if needed)
}}

CRITICAL INSTRUCTIONS:
1. Return ONLY valid JSON - no markdown, no explanations, no code blocks
2. Preserve EVERY method implementation from the original code
3. Keep ALL validation logic, calculations, and business rules
4. Maintain the same API endpoints and data flow
5. Include comprehensive TypeScript interfaces matching the original data structures
6. Add proper error handling and logging
7. Include comments explaining complex business logic
8. Generate separate files for component, template, styles, and services
"""
        
        return prompt

    def _call_llm(self, prompt: str, component_name: str = None) -> Dict[str, str]:
        """
        Call Azure OpenAI to generate code based on the prompt.
        Returns a dictionary mapping file paths to generated code.
        """
        # Save the prompt to a log file for debugging
        self._log_prompt(prompt, component_name)
        
        try:
            response = self.client.chat.completions.create(
                model=self.llm_config.get("deployment"),
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert code migration assistant. Generate clean, production-ready code following best practices."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.llm_config.get("max_tokens", 3000),
                )
            
            content = response.choices[0].message.content
            
            # Log the raw LLM response
            self._log_llm_response(content, component_name, response)
            
            # Parse the response to extract file mappings
            # Expected format: JSON with file paths as keys and code as values
            # Or fallback to single file generation
            generated_files = {}
            
            try:
                generated_code = json.loads(content)
                if isinstance(generated_code, dict):
                    generated_files = generated_code
                else:
                    # Not a dict, treat as single file
                    raise json.JSONDecodeError("Not a dict", content, 0)
            except json.JSONDecodeError:
                # If not JSON, treat as single file content
                # Clean up markdown code blocks if present
                cleaned_content = content
                if content.startswith("```"):
                    lines = content.split("\n")
                    # Remove first line (```typescript or similar)
                    lines = lines[1:]
                    # Remove last line if it's ```
                    if lines and lines[-1].strip() == "```":
                        lines = lines[:-1]
                    cleaned_content = "\n".join(lines)
                
                # Generate filename from component name
                if component_name:
                    # Convert component name to kebab-case for filename
                    filename = self._to_kebab_case(component_name)
                    generated_files = {f"{filename}.component.ts": cleaned_content}
                else:
                    # Default: return as single component file
                    generated_files = {"component.ts": cleaned_content}
            
            # Save each generated file individually in the output directory
            self._save_generated_files(generated_files, component_name)
            
            return generated_files
            
        except Exception as e:
            print(f"Error calling LLM: {e}")
            # Implement retry logic based on config
            retry_config = self.llm_config.get("retry", {})
            attempts = retry_config.get("attempts", 1)
            
            if attempts > 1:
                print(f"Retrying... (attempts left: {attempts - 1})")
                # Could implement backoff here
            
            raise

    def _initialize_llm_client(self):
        """Initialize Azure OpenAI client with credentials from environment."""
        # Load .env file from project root
        env_path = Path(__file__).parent.parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            print(f"Loaded environment variables from {env_path}")
        
        provider = self.llm_config.get("provider")
        
        if provider == "azure_openai":
            # Get credentials from environment variables
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            
            if not api_key or not endpoint:
                raise ValueError(
                    "Azure OpenAI credentials not found. "
                    "Please set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT environment variables."
                )
            
            self.client = AzureOpenAI(
                api_key=api_key,
                api_version=self.llm_config.get("api_version", "2024-02-15-preview"),
                azure_endpoint=endpoint
            )
        else:
            raise NotImplementedError(f"Provider '{provider}' is not yet supported")

    def _get_original_source(self, component_name: str, context: ExecutionContext) -> str:
        """
        Retrieve the original source code for a component from the scanned files.
        """
        try:
            # Get file inventory and scan index from context
            file_metadata = context.get_artifact("file_metadata")
            
            if not file_metadata:
                return f"// Original source code not available for {component_name}"
            
            # Find the file that matches the component name
            component_file = None
            for metadata in file_metadata:
                filename = os.path.basename(metadata.path)
                # Match component name (without extension)
                if component_name in filename:
                    component_file = metadata.path
                    break
            
            if not component_file:
                return f"// Original source file not found for {component_name}"
            
            # Read the file content
            with open(component_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            return content
            
        except Exception as e:
            print(f"Warning: Could not load original source for {component_name}: {e}")
            return f"// Error loading original source: {str(e)}"

    def _get_related_files(self, component_ir, context: ExecutionContext) -> Dict[str, str]:
        """
        Get the source code of related dependency files.
        """
        related_files = {}
        
        try:
            file_metadata = context.get_artifact("file_metadata")
            
            if not file_metadata:
                return related_files
            
            # Get dependencies from the component IR
            for dep in component_ir.dependencies:
                dep_name = dep.name
                
                # Find the file for this dependency
                for metadata in file_metadata:
                    filename = os.path.basename(metadata.path)
                    if dep_name in filename:
                        try:
                            with open(metadata.path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                related_files[dep_name] = {
                                    'path': metadata.path,
                                    'type': dep.type,
                                    'content': content
                                }
                        except Exception as e:
                            print(f"Warning: Could not load dependency {dep_name}: {e}")
                        break
            
        except Exception as e:
            print(f"Warning: Error loading related files: {e}")
        
        return related_files

    def _format_related_files(self, related_files: Dict[str, dict]) -> str:
        """
        Format related files for inclusion in the prompt.
        """
        if not related_files:
            return "No related dependency files available."
        
        formatted = []
        for name, file_info in related_files.items():
            content = file_info['content']
            file_type = file_info['type']
            
            # Truncate very large files
            max_length = 3000
            if len(content) > max_length:
                content = content[:max_length] + f"\n\n... (truncated, {len(content) - max_length} characters omitted) ..."
            
            formatted.append(f"""
--- {name} ({file_type}) ---
File: {file_info['path']}

```javascript
{content}
```
""")
        
        return "\n".join(formatted)

    def _get_migration_patterns(self, component_type: str) -> str:
        """
        Get specific migration patterns based on component type.
        """
        patterns = {
            "model": """
**ExtJS Model → Angular Interface + Validation**
- Ext.define('Model', {fields: [...]}) → TypeScript interface
- Validators → Use Angular validators or custom validator functions
- Default values → Initialize in constructor or use default parameters
- Computed properties → Use TypeScript getters

Example:
```typescript
// Interface
export interface Account {
  accountId: number;
  username: string;
  email: string;
  // ... all fields
}

// Validation
export class AccountValidators {
  static validateEmail(email: string): boolean {
    return /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email);
  }
}
```
""",
            "store": """
**ExtJS Store → Angular Service with RxJS**
- Ext.data.Store → Injectable Service with BehaviorSubject
- Store.load() → HttpClient.get() with Observable
- Store.add/remove → BehaviorSubject.next() with updated array
- Store.filter() → RxJS operators (map, filter)
- Store events → RxJS Subjects for change notifications

Example:
```typescript
@Injectable({providedIn: 'root'})
export class AccountService {
  private dataSubject = new BehaviorSubject<Account[]>([]);
  public data$ = this.dataSubject.asObservable();

  constructor(private http: HttpClient) {}

  loadAccounts(): Observable<Account[]> {
    return this.http.get<Account[]>('/api/accounts').pipe(
      tap(data => this.dataSubject.next(data))
    );
  }
}
```
""",
            "controller": """
**ExtJS Controller → Angular Component**
- Controller actions → Component methods
- refs → @ViewChild or template references
- Control config → Event bindings in template
- Store access → Inject service and subscribe to observables
- Event handlers → (click), (change) template bindings

Example:
```typescript
@Component({
  selector: 'app-account-grid',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './account-grid.component.html'
})
export class AccountGridComponent {
  accounts$ = this.accountService.data$;

  constructor(private accountService: AccountService) {}

  onEdit(account: Account): void {
    // Handle edit action
  }
}
```
""",
            "view": """
**XHTML Template → Angular Template**
- Ext.grid.Panel → Angular Material Table or custom table
- Ext.form.Panel → Angular Reactive Forms
- Ext.button → <button> with (click) binding
- Ext.window → Angular Material Dialog
- xtype configs → Component composition
- Tpl (XTemplate) → *ngFor with interpolation

Example:
```html
<table>
  <tr *ngFor="let account of accounts$ | async">
    <td>{{ account.username }}</td>
    <td>{{ account.email }}</td>
    <td>
      <button (click)="onEdit(account)">Edit</button>
    </td>
  </tr>
</table>
```
""",
            "service": """
**ExtJS Service → Angular Service**
- Singleton pattern → @Injectable({providedIn: 'root'})
- Ajax calls → HttpClient with typed responses
- Callbacks → Observables with subscribe/async pipe
- Error handling → catchError operator

Example:
```typescript
@Injectable({providedIn: 'root'})
export class AccountService {
  private apiUrl = '/api/accounts';

  constructor(private http: HttpClient) {}

  getAccount(id: number): Observable<Account> {
    return this.http.get<Account>(`${this.apiUrl}/${id}`).pipe(
      catchError(error => {
        console.error('Error loading account:', error);
        return throwError(() => error);
      })
    );
  }
}
```
""",
            "utility": """
**ExtJS Utility → TypeScript Utility Module**
- Singleton class → Regular TypeScript class or pure functions
- Ext.util → Separate utility files
- Formatters → Pure functions or Angular pipes
- Validators → Validator functions

Example:
```typescript
export class Formatter {
  static formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  }
}

// Or as a pipe
@Pipe({name: 'currency', standalone: true})
export class CurrencyPipe implements PipeTransform {
  transform(value: number): string {
    return Formatter.formatCurrency(value);
  }
}
```
"""
        }
        
        return patterns.get(component_type, """
**General Migration Pattern**
- Preserve all business logic exactly as implemented
- Convert ExtJS patterns to equivalent Angular patterns
- Use TypeScript interfaces for type safety
- Implement reactive programming with RxJS
- Follow Angular style guide conventions
""")

    def _log_prompt(self, prompt: str, component_name: str = None) -> None:
        """
        Log the prompt being sent to LLM for debugging and analysis.
        Includes detailed statistics about the prompt.
        """
        try:
            from datetime import datetime
            
            # Create prompts directory in output path
            prompts_dir = self.output_path / 'prompts_log'
            prompts_dir.mkdir(parents=True, exist_ok=True)
            
            # Sanitize component name for filename (remove path separators)
            safe_component_name = (component_name or 'unknown').replace('\\', '_').replace('/', '_').replace(':', '_')
            
            # Generate filename with timestamp
            timestamp = datetime.now()
            timestamp_str = timestamp.strftime('%Y%m%d_%H%M%S')
            filename = f"prompt_{safe_component_name}_{timestamp_str}.txt"
            filepath = prompts_dir / filename
            
            # Calculate statistics
            lines = prompt.split('\n')
            char_count = len(prompt)
            word_count = len(prompt.split())
            
            # Count sections
            sections = prompt.count('='*80)
            has_original_code = 'ORIGINAL SOURCE CODE' in prompt
            has_dependencies = 'RELATED DEPENDENCY FILES' in prompt
            has_ir = 'CANONICAL IR' in prompt
            
            # Write prompt to file with detailed header
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"{'='*80}\n")
                f.write(f"PROMPT LOG FOR: {component_name or 'Unknown Component'}\n")
                f.write(f"Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"{'='*80}\n\n")
                f.write(f"PROMPT STATISTICS:\n")
                f.write(f"  - Total Characters: {char_count:,}\n")
                f.write(f"  - Total Words: {word_count:,}\n")
                f.write(f"  - Total Lines: {len(lines):,}\n")
                f.write(f"  - Sections: {sections}\n")
                f.write(f"  - Contains Original Source: {'Yes' if has_original_code else 'No'}\n")
                f.write(f"  - Contains Dependencies: {'Yes' if has_dependencies else 'No'}\n")
                f.write(f"  - Contains IR: {'Yes' if has_ir else 'No'}\n")
                f.write(f"\n{'='*80}\n\n")
                f.write(prompt)
                f.write(f"\n\n{'='*80}\n")
                f.write(f"END OF PROMPT\n")
                f.write(f"Total Size: {char_count:,} characters\n")
                f.write(f"{'='*80}\n")
            
            print(f"  → Prompt logged: {filepath.name} ({char_count:,} chars)")
            
        except Exception as e:
            print(f"Warning: Could not log prompt: {e}")

    def _log_llm_response(self, content: str, component_name: str = None, response_obj = None) -> None:
        """
        Log the LLM response for debugging and analysis.
        Includes detailed statistics and metadata.
        """
        try:
            from datetime import datetime
            
            # Create responses directory in output path
            responses_dir = self.output_path / 'prompts_log' / 'responses'
            responses_dir.mkdir(parents=True, exist_ok=True)
            
            # Sanitize component name for filename (remove path separators)
            safe_component_name = (component_name or 'unknown').replace('\\', '_').replace('/', '_').replace(':', '_')
            
            # Generate filename with timestamp
            timestamp = datetime.now()
            timestamp_str = timestamp.strftime('%Y%m%d_%H%M%S')
            filename = f"response_{safe_component_name}_{timestamp_str}.txt"
            filepath = responses_dir / filename
            
            # Calculate statistics
            char_count = len(content)
            word_count = len(content.split())
            lines = content.split('\n')
            
            # Try to detect response format
            is_json = content.strip().startswith('{')
            is_markdown = content.strip().startswith('```')
            
            # Count files in response (if JSON)
            file_count = 0
            if is_json:
                try:
                    import json
                    parsed = json.loads(content)
                    if isinstance(parsed, dict):
                        file_count = len(parsed)
                except:
                    pass
            
            # Write response to file with detailed metadata
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"{'='*80}\n")
                f.write(f"LLM RESPONSE FOR: {component_name or 'Unknown Component'}\n")
                f.write(f"Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"{'='*80}\n\n")
                
                # Response metadata
                f.write(f"RESPONSE METADATA:\n")
                if response_obj:
                    f.write(f"  - Model: {response_obj.model}\n")
                    f.write(f"  - Finish Reason: {response_obj.choices[0].finish_reason}\n")
                    if hasattr(response_obj, 'usage'):
                        f.write(f"  - Prompt Tokens: {response_obj.usage.prompt_tokens}\n")
                        f.write(f"  - Completion Tokens: {response_obj.usage.completion_tokens}\n")
                        f.write(f"  - Total Tokens: {response_obj.usage.total_tokens}\n")
                
                # Response statistics
                f.write(f"\nRESPONSE STATISTICS:\n")
                f.write(f"  - Total Characters: {char_count:,}\n")
                f.write(f"  - Total Words: {word_count:,}\n")
                f.write(f"  - Total Lines: {len(lines):,}\n")
                f.write(f"  - Format: {'JSON' if is_json else 'Markdown' if is_markdown else 'Plain Text'}\n")
                if file_count > 0:
                    f.write(f"  - Files in Response: {file_count}\n")
                
                f.write(f"\n{'='*80}\n\n")
                f.write(content)
                f.write(f"\n\n{'='*80}\n")
                f.write(f"END OF RESPONSE\n")
                f.write(f"Total Size: {char_count:,} characters\n")
                f.write(f"{'='*80}\n")
            
            print(f"  → Response logged: {filepath.name} ({char_count:,} chars, {file_count} files)")
            
        except Exception as e:
            print(f"Warning: Could not log response: {e}")

    def _save_generated_files(self, generated_files: Dict[str, str], component_name: str = None) -> None:
        """
        Save generated files immediately to the output directory with proper formatting.
        This creates a preview of the generated code separate from the response log.
        Each file is saved separately in its own location with proper indentation.
        """
        try:
            # Create a 'generated' subdirectory for clean separation
            generated_dir = self.output_path / 'generated'
            generated_dir.mkdir(parents=True, exist_ok=True)
            
            # If component name is provided, create a subdirectory for it
            if component_name:
                safe_component_name = component_name.replace('\\', '_').replace('/', '_').replace(':', '_')
                component_dir = generated_dir / safe_component_name
                component_dir.mkdir(parents=True, exist_ok=True)
                base_dir = component_dir
            else:
                base_dir = generated_dir
            
            print(f"\n  Saving {len(generated_files)} file(s) to {base_dir.relative_to(self.output_path)}...")
            
            # Save each file separately
            for file_path, content in generated_files.items():
                # Ensure content is properly decoded (handle escaped strings)
                # If content still has literal \n, decode it
                if isinstance(content, str) and '\\n' in content and '\n' not in content:
                    # Content has escaped newlines, need to decode
                    try:
                        content = content.encode().decode('unicode_escape')
                    except:
                        pass  # Keep original if decode fails
                
                # Remove any leading/trailing whitespace but preserve internal formatting
                content = content.strip()
                
                # Create the full file path
                full_path = base_dir / file_path
                
                # Create parent directories if needed
                full_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write the file with proper formatting
                with open(full_path, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(content)
                    # Ensure file ends with newline
                    if content and not content.endswith('\n'):
                        f.write('\n')
                
                # Count actual lines for better reporting
                line_count = content.count('\n') + 1
                print(f"    ✓ {file_path} ({line_count} lines, {len(content)} chars)")
                
        except Exception as e:
            print(f"Warning: Could not save generated files: {e}")
            import traceback
            traceback.print_exc()

    def _log_migration_summary(self, context: ExecutionContext, migration_plan, generated_files: Dict[str, str]) -> None:
        """
        Log comprehensive migration summary to the migration analysis document.
        """
        # Calculate statistics
        total_files = sum(len(files) for files in generated_files.values() if isinstance(files, dict))
        if total_files == 0:
            total_files = len(generated_files)
        
        file_types = {}
        for filename in generated_files.keys():
            ext = filename.split('.')[-1] if '.' in filename else 'unknown'
            file_types[ext] = file_types.get(ext, 0) + 1
        
        # Prepare detailed summary
        summary_data = {
            "Migration Overview": {
                "Total Components": len(migration_plan.steps),
                "Total Files Generated": total_files,
                "Unique File Types": list(file_types.keys())
            },
            "LLM Configuration": {
                "Provider": self.llm_config.get("provider"),
                "Model": self.llm_config.get("deployment"),
                "Temperature": self.llm_config.get("temperature"),
                "Max Tokens": self.llm_config.get("max_tokens"),
                "API Version": self.llm_config.get("api_version")
            },
            "Components Migrated": [],
            "Files Generated by Type": file_types,
            "Output Structure": {
                "Generated Code": str(self.output_path / 'generated'),
                "Prompt Logs": str(self.output_path / 'prompts_log'),
                "Response Logs": str(self.output_path / 'prompts_log' / 'responses')
            }
        }
        
        # Add details for each component
        for step in migration_plan.steps:
            component_files = [f for f in generated_files.keys() if step.component.lower() in f.lower()]
            summary_data["Components Migrated"].append({
                "Component": step.component,
                "Type": step.migration_type if hasattr(step, 'migration_type') else 'unknown',
                "Risk Level": step.risk_level,
                "Dependencies": step.depends_on if step.depends_on else [],
                "Files Generated": component_files if component_files else list(generated_files.keys())
            })
        
        context.log_agent_execution("Target Code Generation Agent", summary_data)


