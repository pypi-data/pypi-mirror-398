"""
JavaScript runtime executor.

Executes JavaScript code via Node.js or Deno subprocess.
"""

import json
import os
import subprocess
import tempfile
from typing import Any, Dict

from mcard import MCard

from .base import SubprocessRuntime, RUNTIME_CONFIG, DEFAULT_TIMEOUT


class JavaScriptRuntime(SubprocessRuntime):
    """JavaScript runtime executor - executes via Node.js or Deno."""
    
    runtime_name = "JavaScript"
    timeout = DEFAULT_TIMEOUT
    
    def __init__(self, use_deno: bool = False):
        super().__init__()
        runtime_key = 'deno' if use_deno else 'javascript'
        config = RUNTIME_CONFIG.get(runtime_key, RUNTIME_CONFIG.get('javascript', {}))
        self.command = config.get('command', 'node')
        self.eval_flag = config.get('eval_flag', '--eval')
        self.use_deno = use_deno
    
    def execute(self, impl: Dict[str, Any], target: MCard, ctx: Dict[str, Any]) -> Any:
        # Handle run_command builtin
        if impl.get('builtin') == 'run_command':
            config = impl.get('config', {})
            cmd = config.get('command')
            if not cmd:
                return "Error: No command provided"
            
            try:
                res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=self.timeout)
                if res.returncode != 0:
                    return f"Error: Command failed: {res.stderr}"
                return res.stdout.strip()
            except Exception as e:
                return f"Error executing command: {e}"

        # Handle loader builtin via Node.js
        if impl.get('builtin') == 'loader':
            return self._execute_loader_builtin(impl, ctx)

        code = impl.get('code', '')
        if not code and not impl.get('entry_point', {}).get('file'):
            return "Error: No JavaScript code or file provided"
        
        input_data = {
            'target': target.get_content().decode('utf-8', errors='ignore'),
            'context': ctx
        }
        
        # Use IIFE pattern to isolate user code's variable declarations
        # User code can use 'var result', 'let result', or 'const result'
        # The wrapper captures 'result' from the user's scope
        js_code = f"""
        (async () => {{
            const __input__ = {json.dumps(input_data)};
            const target = __input__.target;
            const context = __input__.context;
            let __result__;
            try {{
                // Execute user code in IIFE to capture 'result'
                __result__ = (() => {{
                    {code}
                    return (typeof result !== 'undefined') ? result : undefined;
                }})();
            }} catch (e) {{
                __result__ = {{ error: e.message, stack: e.stack }};
                process.exitCode = 1;
            }}
            console.log(JSON.stringify(__result__));
        }})();
        """
        
        try:
            cmd = self.command
            if isinstance(cmd, str):
                cmd_list = [cmd]
            else:
                cmd_list = list(cmd)
                
            result = subprocess.run(
                cmd_list + [self.eval_flag, js_code],
                capture_output=True, text=True, timeout=self.timeout
            )
            if result.returncode != 0:
                return f"Error: JavaScript execution failed: {result.stderr}"
            output = result.stdout.strip()
            if not output:
                return None
            return json.loads(output)
        except subprocess.TimeoutExpired:
            return "Error: JavaScript execution timed out"
        except json.JSONDecodeError as e:
            # If JSON parsing fails, return the raw output
            return result.stdout.strip() if result.stdout else f"Error: Invalid JSON output: {e}"
        except Exception as e:
            return f"Error executing JavaScript: {e}"

    def _execute_loader_builtin(self, impl: Dict[str, Any], ctx: Dict[str, Any]) -> Any:
        """Execute JS loader builtin via Node.js using mcard-js."""
        # Get parameters
        input_args = impl.get('input_arguments', {})
        source_dir = input_args.get('source_dir') or ctx.get('source_dir', 'docs')
        db_path = input_args.get('db_path') or ctx.get('db_path', 'data/loader_js.db')
        recursive = input_args.get('recursive', True)
        
        # Find mcard-js path
        project_root = os.getcwd()
        mcard_js_path = os.path.join(project_root, 'mcard-js')
        
        # Create inline script to invoke loader
        loader_script = f'''
import {{ SqliteNodeEngine }} from './src/storage/SqliteNodeEngine.js';
import {{ CardCollection }} from './src/model/CardCollection.js';
import {{ loadFileToCollection }} from './src/util/Loader.js';
import * as path from 'path';
import * as fs from 'fs';

const sourceDir = "{source_dir}";
const dbPath = "{db_path}";
const recursive = {str(recursive).lower()};

const projectRoot = path.resolve("{project_root}");
const sourcePath = path.isAbsolute(sourceDir) ? sourceDir : path.join(projectRoot, sourceDir);
const resolvedDbPath = path.isAbsolute(dbPath) ? dbPath : path.join(projectRoot, dbPath);

// Ensure directory
const dbDir = path.dirname(resolvedDbPath);
if (!fs.existsSync(dbDir)) fs.mkdirSync(dbDir, {{ recursive: true }});

// Remove existing DB
if (fs.existsSync(resolvedDbPath)) fs.unlinkSync(resolvedDbPath);

const engine = new SqliteNodeEngine(resolvedDbPath);
const collection = new CardCollection(engine);

loadFileToCollection(sourcePath, collection, {{ recursive, includeProblematic: false }})
  .then(result => {{
    console.log(JSON.stringify({{
      success: true,
      metrics: {{
        total_files: result.metrics.filesCount,
        total_directories: result.metrics.directoriesCount,
        directory_levels: result.metrics.directoryLevels,
        total_size_bytes: result.results.reduce((a, r) => a + (r.size || 0), 0)
      }},
      files: result.results.slice(0, 10).map(r => ({{
        hash: r.hash.substring(0, 8),
        filename: r.filename,
        content_type: r.contentType
      }}))
    }}));
    engine.close();
    process.exit(0);
  }})
  .catch(err => {{
    console.error(JSON.stringify({{ success: false, error: err.message }}));
    process.exit(1);
  }});
'''
        
        # Write temp script
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mjs', dir=mcard_js_path, delete=False) as f:
            f.write(loader_script)
            script_path = f.name
        
        try:
            result = subprocess.run(
                ['npx', 'tsx', script_path],
                capture_output=True, text=True, timeout=120,
                cwd=mcard_js_path
            )
            if result.returncode != 0:
                stderr = result.stderr or ""
                return {"success": False, "error": f"JS loader failed: {stderr}"}
            try:
                # Parse last line that contains JSON (skip debug output)
                stdout = result.stdout.strip()
                lines = stdout.split('\n')
                for line in reversed(lines):
                    line = line.strip()
                    if line.startswith('{') and line.endswith('}'):
                        return json.loads(line)
                return {"success": False, "error": f"No JSON found in output. Stdout: {stdout[:200]}"}
            except json.JSONDecodeError as e:
                return {"success": False, "error": f"JSON parse error: {e}. Stdout: {result.stdout[:500]}"}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "JS loader timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            try:
                os.unlink(script_path)
            except:
                pass
