"""
TypeScript script runner using Deno.

Executes automation scripts in a sandboxed Deno environment.
"""

from __future__ import annotations
import subprocess
import json
import tempfile
import shutil
import re
from pathlib import Path
from typing import Any


def to_camel_case(snake_str: str) -> str:
    """Convert snake_case to camelCase."""
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def convert_keys_to_camel(obj: Any) -> Any:
    """Recursively convert dict keys from snake_case to camelCase."""
    if isinstance(obj, dict):
        return {to_camel_case(k): convert_keys_to_camel(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_keys_to_camel(item) for item in obj]
    return obj


class ScriptRunner:
    """
    Run TypeScript automation scripts using Deno.
    
    Scripts are executed in a sandboxed environment with:
    - No network access (by default)
    - No filesystem access outside scripts dir
    - Timeout protection
    - JSON input/output
    """
    
    def __init__(self, project_root: Path):
        """
        Initialize script runner.
        
        Args:
            project_root: Root of the planecompose project
        """
        self.project_root = Path(project_root)
        self.automations_dir = self.project_root / "automations"
        self.scripts_dir = self.automations_dir / "scripts"
        
        # Check if Deno is available
        self._deno_available: bool | None = None
    
    @property
    def deno_available(self) -> bool:
        """Check if Deno is installed."""
        if self._deno_available is None:
            self._deno_available = shutil.which("deno") is not None
        return self._deno_available
    
    def resolve_script_path(self, script_ref: str) -> Path:
        """
        Resolve script path from reference.
        
        Args:
            script_ref: Script reference like "./scripts/my.ts" or "my.ts"
            
        Returns:
            Absolute path to script
        """
        if script_ref.startswith("./"):
            # Relative to automations dir
            return self.automations_dir / script_ref[2:]
        elif script_ref.startswith("../"):
            # Relative path
            return self.automations_dir / script_ref
        else:
            # Just filename, assume in scripts/
            return self.scripts_dir / script_ref
    
    async def run(
        self,
        script_path: str,
        context: dict[str, Any],
        timeout: int = 30,
        allow_net: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Run a TypeScript script and return actions.
        
        Args:
            script_path: Path to the script (relative or absolute)
            context: Execution context to pass to script
            timeout: Maximum execution time in seconds
            allow_net: Whether to allow network access
            
        Returns:
            List of action dicts returned by script
            
        Raises:
            FileNotFoundError: Script doesn't exist
            RuntimeError: Script execution failed
            TimeoutError: Script exceeded timeout
            ValueError: Script returned invalid data
        """
        if not self.deno_available:
            raise RuntimeError(
                "Deno is not installed. Install from https://deno.land/\n"
                "  curl -fsSL https://deno.land/install.sh | sh"
            )
        
        # Resolve script path
        full_path = self.resolve_script_path(script_path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"Script not found: {full_path}")
        
        # Create wrapper script
        wrapper_path = self._create_wrapper(full_path)
        
        try:
            # Build Deno command
            cmd = [
                "deno", "run",
                "--no-prompt",
                f"--allow-read={full_path.parent}",
            ]
            
            if allow_net:
                cmd.append("--allow-net")
            
            cmd.append(str(wrapper_path))
            
            # Convert context keys to camelCase for JavaScript
            js_context = convert_keys_to_camel(context)
            
            # Run with context as stdin
            result = subprocess.run(
                cmd,
                input=json.dumps(js_context),
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.project_root),
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() or "Unknown error"
                raise RuntimeError(f"Script failed: {error_msg}")
            
            # Parse output
            output = result.stdout.strip()
            if not output:
                return []
            
            try:
                actions = json.loads(output)
            except json.JSONDecodeError as e:
                raise ValueError(f"Script returned invalid JSON: {e}\nOutput: {output[:200]}")
            
            if not isinstance(actions, list):
                raise ValueError(
                    f"Script must return an array of actions, got: {type(actions).__name__}"
                )
            
            return actions
            
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Script timed out after {timeout}s")
        
        finally:
            # Clean up wrapper
            if wrapper_path.exists():
                wrapper_path.unlink()
    
    def _create_wrapper(self, script_path: Path) -> Path:
        """
        Create a wrapper script that handles I/O.
        
        The wrapper:
        1. Reads JSON context from stdin
        2. Imports and calls the user script
        3. Outputs result as JSON to stdout
        """
        wrapper_content = f'''
// Auto-generated wrapper for {script_path.name}
import automation from "{script_path.as_uri()}";

async function main() {{
    // Read context from stdin
    const decoder = new TextDecoder();
    const chunks: Uint8Array[] = [];
    
    for await (const chunk of Deno.stdin.readable) {{
        chunks.push(chunk);
    }}
    
    const input = decoder.decode(new Uint8Array(
        chunks.reduce((acc, chunk) => [...acc, ...chunk], [] as number[])
    ));
    
    const context = JSON.parse(input || "{{}}");
    
    // Call the automation
    let result;
    if (typeof automation === "function") {{
        result = await automation(context);
    }} else if (typeof automation.default === "function") {{
        result = await automation.default(context);
    }} else if (typeof automation.run === "function") {{
        result = await automation.run(context);
    }} else {{
        throw new Error("Script must export a default function or 'run' function");
    }}
    
    // Output result as JSON
    console.log(JSON.stringify(result ?? []));
}}

main().catch((err) => {{
    console.error(err.message);
    Deno.exit(1);
}});
'''
        
        # Write to temp file
        wrapper_path = Path(tempfile.gettempdir()) / f"plane_wrapper_{script_path.stem}.ts"
        wrapper_path.write_text(wrapper_content)
        
        return wrapper_path
    
    def validate(self, script_path: str) -> list[str]:
        """
        Validate a script (type-check without running).
        
        Args:
            script_path: Path to the script
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        if not self.deno_available:
            return ["Deno is not installed"]
        
        full_path = self.resolve_script_path(script_path)
        
        if not full_path.exists():
            return [f"Script not found: {full_path}"]
        
        # Type check with Deno
        result = subprocess.run(
            ["deno", "check", str(full_path)],
            capture_output=True,
            text=True,
            cwd=str(self.project_root),
        )
        
        if result.returncode != 0:
            errors.append(result.stderr.strip())
        
        return errors
    
    def check_deno(self) -> tuple[bool, str]:
        """
        Check Deno installation and version.
        
        Returns:
            Tuple of (is_available, version_or_error)
        """
        if not self.deno_available:
            return False, "Deno not found. Install from https://deno.land/"
        
        try:
            result = subprocess.run(
                ["deno", "--version"],
                capture_output=True,
                text=True,
            )
            version_line = result.stdout.split("\n")[0]
            return True, version_line
        except Exception as e:
            return False, str(e)

