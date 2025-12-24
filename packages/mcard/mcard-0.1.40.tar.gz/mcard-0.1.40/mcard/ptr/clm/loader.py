"""
CLM Chapter Loader
==================

Loads CLM Chapter specifications from YAML and dynamically imports the associated logic.
"""

import os
import yaml
from typing import Any, Dict, List, Optional
from mcard.model.pcard import PCard
from mcard.model.vcard import VCard

from mcard.ptr.core.clm_template import Chapter, CLMConfiguration, NarrativeMonad

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

CLM_EXTENSIONS = ('.clm', '.yaml', '.yml')
CODE_READABLE_RUNTIMES = ('python', 'javascript')
MODULE_URI_PREFIX = 'module://'
DEFAULT_RUNTIME = 'python'
DEFAULT_TARGET = 'dummy_target'


# ─────────────────────────────────────────────────────────────────────────────
# Path Resolution Utilities
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_path(base_dir: str, path: str) -> str:
    """Resolve a relative path against a base directory."""
    if os.path.isabs(path):
        return path
    return os.path.join(base_dir, path)


def _is_module_uri(path: str) -> bool:
    """Check if path is a module:// URI."""
    return path.startswith(MODULE_URI_PREFIX)


def _resolve_concrete_paths(concrete: Dict, base_dir: str, runtime: str) -> None:
    """
    Resolve all file paths in concrete config relative to base_dir.
    Modifies concrete dict in-place.
    """
    # code_file resolution
    if 'code_file' in concrete and not _is_module_uri(concrete['code_file']):
        code_path = _resolve_path(base_dir, concrete['code_file'])
        concrete['code_file'] = code_path
        # Read code content for runtimes that need it
        if runtime in CODE_READABLE_RUNTIMES and os.path.exists(code_path):
            with open(code_path, 'r') as f:
                concrete['code'] = f.read()
    
    # binary_path resolution
    if 'binary_path' in concrete and not os.path.isabs(concrete['binary_path']):
        concrete['binary_path'] = _resolve_path(base_dir, concrete['binary_path'])
    
    # wasm_module resolution
    if 'wasm_module' in concrete and not os.path.isabs(concrete['wasm_module']):
        concrete['wasm_module'] = _resolve_path(base_dir, concrete['wasm_module'])


def _parse_numeric_result(result: Any) -> Any:
    """Attempt to parse a string result as a number."""
    if isinstance(result, str):
        clean = result.strip()
        # Check if it looks numeric (handles negatives and decimals)
        if clean.lstrip('-').replace('.', '', 1).isdigit():
            try:
                return float(clean) if '.' in clean else int(clean)
            except ValueError:
                pass
    return result


# ─────────────────────────────────────────────────────────────────────────────
# YAML Template Loader
# ─────────────────────────────────────────────────────────────────────────────

class YAMLTemplateLoader:
    """Loads CLM YAML templates from a templates directory."""
    
    def __init__(self, templates_dir: Optional[str] = None):
        if templates_dir:
            self.templates_dir = templates_dir
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.templates_dir = os.path.join(current_dir, "templates")

    def load_template(self, template_name: str) -> Dict[str, Any]:
        """Load a specific YAML template by name."""
        for ext in CLM_EXTENSIONS:
            file_path = os.path.join(self.templates_dir, f"{template_name}{ext}")
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return yaml.safe_load(f)
        raise FileNotFoundError(f"Template not found: {template_name}")

    def load_all_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load all templates in the directory."""
        templates = {}
        if not os.path.exists(self.templates_dir):
            return templates
        
        for filename in os.listdir(self.templates_dir):
            if filename.endswith(CLM_EXTENSIONS):
                name = os.path.splitext(filename)[0]
                with open(os.path.join(self.templates_dir, filename), 'r') as f:
                    templates[name] = yaml.safe_load(f)
        return templates


# ─────────────────────────────────────────────────────────────────────────────
# CLM Chapter Loader
# ─────────────────────────────────────────────────────────────────────────────

class CLMChapterLoader:
    """Loads Chapter objects from YAML specifications."""

    @staticmethod
    def _parse_clm_data(data: Dict, yaml_path: str) -> tuple:
        """
        Parse CLM data and return (chapter_data, clm_data, clm_config).
        Handles both 'chapter' format and raw PCard format.
        """
        if 'chapter' in data:
            chapter_data = data['chapter']
            # Provide defaults for optional fields
            chapter_data.setdefault('mvp_card', 'CLM Execution')
            chapter_data.setdefault('pkc_task', 'Runtime Execution')
            clm_data = data['clm']
            
            # Support aliases for dimensions
            abstract = clm_data.get('abstract_spec', clm_data.get('abstract', {}))
            concrete = clm_data.get('concrete_impl', clm_data.get('concrete', {}))
            balanced = clm_data.get('balanced_exp', clm_data.get('balanced', {}))
            
            # Update clm_data for internal use
            clm_data['abstract'] = abstract
            clm_data['concrete'] = concrete
            clm_data['balanced'] = balanced

            # Default to lambda runtime
            if 'runtime' not in clm_data['concrete']:
                clm_data['concrete']['runtime'] = 'lambda'
            
            clm = CLMConfiguration(
                abstract=abstract.get('concept', abstract.get('purpose', 'Unknown')),
                concrete=concrete.get('manifestation', concrete.get('description', 'Unknown')),
                balanced=balanced.get('expectation', balanced.get('description', 'Unknown'))
            )
        else:
            # Fallback for raw PCards
            metadata = data.get('metadata', {})
            chapter_data = {
                'id': 0,
                'title': metadata.get('name', os.path.basename(yaml_path)),
                'mvp_card': 'Raw PCard',
                'pkc_task': 'Execution'
            }
            clm_data = data.get('clm', data)
            
            # Support aliases for dimensions
            abstract = clm_data.get('abstract_spec', clm_data.get('abstract', {}))
            concrete = clm_data.get('concrete_impl', clm_data.get('concrete', {}))
            balanced = clm_data.get('balanced_exp', clm_data.get('balanced', {}))
            
            clm = CLMConfiguration(
                abstract=abstract.get('concept', abstract.get('purpose', 'Unknown')),
                concrete=concrete.get('manifestation', concrete.get('operation', 'Unknown')),
                balanced=balanced.get('expectation', balanced.get('description', 'Unknown'))
            )
            
            # Ensure clm_data has normalized keys for the rest of the loader
            clm_data['abstract'] = abstract
            clm_data['concrete'] = concrete
            clm_data['balanced'] = balanced

            # Default to lambda runtime
            if 'runtime' not in clm_data['concrete']:
                clm_data['concrete']['runtime'] = 'lambda'
        
        return chapter_data, clm_data, clm

    @staticmethod
    def _is_clm_runtime(runtime: str) -> bool:
        """Check if runtime is a CLM file reference."""
        return any(runtime.endswith(ext) for ext in CLM_EXTENSIONS)

    @staticmethod
    def _create_recursive_executor(yaml_path: str, runtime: str, chapter_data: Dict, clm_data: Dict):
        """Create an executor for recursive CLM runtime."""
        base_dir = os.path.dirname(yaml_path)
        runtime_path = _resolve_path(base_dir, runtime)
        
        def execute(concrete, target, ctx):
            if not os.path.exists(runtime_path):
                return f"Error: Recursive runtime file not found: {runtime_path}"
            
            # Prepare meta-context
            meta_context = ctx.copy()
            meta_context['source_pcard_title'] = chapter_data.get('title', 'Unknown')
            meta_context['concrete'] = concrete
            meta_context['abstract'] = clm_data.get('abstract', {})
            meta_context['__input_content__'] = target.get_content()
            meta_context['__skip_tests__'] = True
            
            # Load and execute recursively
            meta_chapter = CLMChapterLoader.load_from_yaml(runtime_path)
            result_tuple = meta_chapter.action.execute(meta_context, {"collection": None})
            return result_tuple[0]
        
        class RecursiveExecutor:
            def execute(self, concrete, target, ctx):
                return execute(concrete, target, ctx)
        
        return RecursiveExecutor()

    @staticmethod
    def _execute_single_run(executor, concrete: Dict, config_ctx: Dict, runtime: str) -> NarrativeMonad:
        """Execute a single run (no test cases)."""
        from mcard import MCard
        
        target_content = config_ctx.get('__input_content__', DEFAULT_TARGET)
        
        try:
            target = MCard(target_content)
            result = executor.execute(concrete, target, config_ctx)
            
            # Handle NarrativeMonad result
            if isinstance(result, NarrativeMonad):
                def run_with_config(_, state):
                    return result.run(config_ctx, state)
                return NarrativeMonad(run_with_config)
            
            # Parse numeric result
            result = _parse_numeric_result(result)
            
            return NarrativeMonad.log(f"Executed {runtime} (Single): {result}").bind(
                lambda _: NarrativeMonad.unit(result)
            )
        except Exception as e:
            return NarrativeMonad.log(f"Execution failed: {e}").bind(
                lambda _: NarrativeMonad.unit(None)
            )

    @staticmethod
    def _execute_test_cases(executor, concrete: Dict, config_ctx: Dict, test_cases: List[Dict]) -> NarrativeMonad:
        """Execute all test cases and return a report."""
        from mcard import MCard
        
        results = []
        log_entries = [f"Running {len(test_cases)} test cases..."]
        all_passed = True
        
        try:
            for i, case in enumerate(test_cases):
                given_raw = case.get('given', '')
                given_ctx = {}
                if isinstance(given_raw, dict):
                    ctx = given_raw.get('context', {})
                    cond = given_raw.get('condition', {})
                    if isinstance(ctx, dict) and isinstance(cond, dict):
                        given_ctx = {**ctx, **cond}
                    elif isinstance(cond, dict):
                        given_ctx = cond
                    elif isinstance(ctx, dict):
                        given_ctx = ctx
                    if 'description' in given_raw:
                        given = str(given_raw.get('description', ''))
                    elif 'name' in given_raw:
                        given = str(given_raw.get('name', ''))
                    else:
                        given = str(given_raw)
                else:
                    given = str(given_raw)
                when = case.get('when', {})
                then = case.get('then', {})
                
                # Construct test context
                test_ctx = config_ctx.copy()
                if isinstance(given_ctx, dict):
                    test_ctx.update(given_ctx)
                test_ctx.update(when)
                # Preserve params as nested dict for ${params.xxx} interpolation
                if 'params' in when and isinstance(when['params'], dict):
                    test_ctx['params'] = when['params']
                    # Also merge into top-level for backwards compatibility
                    test_ctx.update(when['params'])
                
                # Support both 'arguments' and 'context' (deprecating context)
                args = when.get('arguments', when.get('context', {}))
                if isinstance(args, dict):
                    test_ctx.update(args)
                
                # Execute
                test_target = MCard(given)
                res = executor.execute(concrete, test_target, test_ctx)
                
                # Compare results - support both exact match and contains
                expected = then.get('result')
                result_contains = then.get('result_contains')
                
                if result_contains:
                    match = CLMChapterLoader._compare_contains(res, result_contains)
                    expected = f"contains '{result_contains}'"
                else:
                    match = CLMChapterLoader._compare_results(res, expected, then.get('epsilon'))
                
                if not match:
                    all_passed = False
                
                status = "✅" if match else "❌"
                log_entries.append(f"Test {i+1} [{given}]: {status} Got {res} (Expected {expected})")
                
                results.append({
                    'case': i + 1,
                    'input': given,
                    'result': res,
                    'expected': expected,
                    'match': match
                })
            
            report = {
                'success': all_passed,
                'total': len(results),
                'passed_count': sum(1 for r in results if r['match']),
                'results': results
            }
            
            return NarrativeMonad.log("\n".join(log_entries)).bind(
                lambda _: NarrativeMonad.unit(report)
            )
            
        except Exception as e:
            return NarrativeMonad.log(f"Test Execution Failed: {e}").bind(
                lambda _: NarrativeMonad.unit(None)
            )

    @staticmethod
    def _compare_results(actual: Any, expected: Any, epsilon: Optional[float] = None) -> bool:
        """Compare actual vs expected results with optional epsilon for floats."""
        if expected is None:
            return not (isinstance(actual, str) and actual.startswith("Error:"))
        
        try:
            # Try to parse actual as number if expected is number and actual is string
            if isinstance(expected, (int, float)) and isinstance(actual, str):
                actual_parsed = _parse_numeric_result(actual)
                if isinstance(actual_parsed, (int, float)):
                    actual = actual_parsed

            if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
                if epsilon:
                    return abs(actual - expected) < float(epsilon)
                return actual == expected
            
            # Handle boolean comparison (case-insensitive)
            # Lean outputs "true"/"false", Python booleans are True/False
            actual_str = str(actual).lower().strip()
            expected_str = str(expected).lower().strip()
            
            # Check if both are boolean-like values
            if actual_str in ('true', 'false') and expected_str in ('true', 'false'):
                return actual_str == expected_str
            
            return str(actual) == str(expected)
        except Exception:
            return str(actual) == str(expected)

    @staticmethod
    def _compare_contains(actual: Any, substring: str) -> bool:
        """Check if actual result contains the expected substring."""
        try:
            return substring in str(actual)
        except Exception:
            return False

    @staticmethod
    def load_from_yaml(yaml_path: str) -> Chapter:
        """
        Load a Chapter from a YAML file.
        
        Args:
            yaml_path: Path to the YAML specification file.
            
        Returns:
            Chapter: The constructed Chapter object with loaded logic.
        """
        # Read content for PCard creation
        with open(yaml_path, 'r') as f:
            raw_content = f.read()
            data = yaml.safe_load(raw_content)
        
        # Create PCard (Transition)
        pcard = PCard(raw_content)
        
        base_dir = os.path.dirname(yaml_path)
        chapter_data, clm_data, clm = CLMChapterLoader._parse_clm_data(data, yaml_path)
        
        concrete = clm_data['concrete']
        runtime = concrete.get('runtime', DEFAULT_RUNTIME)
        builtin = concrete.get('builtin')  # Check for network builtins
        
        def logic_func(_: Any) -> NarrativeMonad:
            return NarrativeMonad.get_context().bind(
                lambda ctx: NarrativeMonad.get_state().bind(
                    lambda state: process_with_petri_net(ctx, state)
                )
            )

        def process_with_petri_net(ctx: Dict, state: Dict) -> NarrativeMonad:
            collection = state.get('collection')
            
            # 1. Petri Net Transition: Persist PCard
            if collection:
                try:
                    collection.add(pcard)
                    handle = pcard.get_transition_handle()
                    try:
                        collection.update_handle(handle, pcard)
                    except Exception:
                        try:
                            collection.add_with_handle(pcard, handle)
                        except Exception:
                            pass
                except Exception:
                    pass

            from mcard.ptr.core.runtime import RuntimeFactory
            
            # Build config context
            config_ctx = ctx.copy()
            config_ctx.update({k: v for k, v in concrete.items() if k != 'logic_source'})
            config_ctx['balanced'] = clm_data.get('balanced', {})
            config_ctx['pcard_dir'] = base_dir  # Ensure pcard_dir is available for path resolution
            
            # Resolve paths
            _resolve_concrete_paths(concrete, base_dir, runtime)
            
            execution_monad = _execute_core_logic(
                ctx=ctx,
                config_ctx=config_ctx,
                concrete=concrete,
                clm_data=clm_data,
                chapter_data=chapter_data,
                runtime=runtime,
                builtin=builtin,
                yaml_path=yaml_path
            )
            
            # 3. Petri Net Token: Produce VCard
            def handle_result(result_tuple):
                # result_tuple can be just result if monad returns result, 
                # but wait, existing logic returns NarrativeMonad which wraps IO returning (val, s, log).
                # bind passes just 'val'.
                result = result_tuple
                
                if collection:
                    try:
                        verified = True
                        if isinstance(result, dict) and result.get('success') is False:
                            verified = False
                        
                        # Provenance: Link to previous VCard if available
                        previous_vcard = None
                        previous_hash = ctx.get('previous_hash') or ctx.get('previousHash')
                        if previous_hash:
                            try:
                                prev_card = collection.get(previous_hash)
                                if prev_card:
                                    # Try to wrap as VCard
                                    from mcard.model.vcard import VCard as VCardCls
                                    previous_vcard = VCardCls(prev_card.get_content(as_text=True))
                            except Exception:
                                pass

                        vcard = VCard.create_verification_vcard(
                            pcard=pcard,
                            execution_result=result if isinstance(result, (dict, list, str, int, float, bool)) else str(result),
                            previous_vcard=previous_vcard,
                            verified=verified
                        )
                        
                        collection.add(vcard)
                        b_handle = pcard.get_balanced_handle()
                        try:
                            collection.update_handle(b_handle, vcard)
                        except Exception:
                            try:
                                collection.add_with_handle(vcard, b_handle)
                            except Exception:
                                pass
                                
                        # Visibility: Attach Petri Net metadata to result (Parity with JS)
                        if isinstance(result, dict):
                            result['petriNet'] = {
                                'pcardHash': pcard.hash,
                                'vcardHash': vcard.hash,
                                'handle': vcard.get_token_handle()
                            }
                            
                    except Exception:
                        pass
                
                return NarrativeMonad.unit(result)

            return execution_monad.bind(handle_result)

        def _execute_core_logic(
            ctx, config_ctx, concrete, clm_data, chapter_data, runtime, builtin, yaml_path
        ) -> NarrativeMonad:
            from mcard.ptr.core.runtime import RuntimeFactory
            # Check if this is a handle builtin (handle_version, handle_prune)
            handle_builtins = ('handle_version', 'handle_prune')
            if builtin in handle_builtins:
                # Use PythonRuntime for handle builtins (they work natively)
                executor = RuntimeFactory.get_executor('python')
                if not executor:
                    return NarrativeMonad.log("Error: Python runtime not available").bind(
                        lambda _: NarrativeMonad.unit({"success": False, "error": "Python runtime not available"})
                    )
                
                # Execute builtin directly
                try:
                    from mcard import MCard
                    target = MCard(ctx.get('__input_content__', DEFAULT_TARGET))
                    result = executor.execute(concrete, target, config_ctx)
                    return NarrativeMonad.log(f"Executed builtin {builtin}").bind(
                        lambda _, r=result: NarrativeMonad.unit(r)
                    )
                except Exception as exc:
                    error_msg = str(exc)
                    return NarrativeMonad.log(f"Builtin execution failed: {error_msg}").bind(
                        lambda _, err=error_msg: NarrativeMonad.unit({"success": False, "error": err})
                    )
            
            # Check if this is a builtin (network) operation
            if builtin and (not runtime or runtime == 'network'):
                # Use NetworkRuntime for builtins
                executor = RuntimeFactory.get_executor('network')
                if not executor:
                    return NarrativeMonad.log("Error: Network runtime not available").bind(
                        lambda _: NarrativeMonad.unit({"success": False, "error": "Network runtime not available"})
                    )
                
                # Check for test cases
                test_cases = clm_data.get('balanced', {}).get('test_cases', [])
                
                # Skip test cases if:
                # 1. __skip_tests__ is set, OR
                # 2. Context has explicit input values (e.g. signaling_url from orchestrator)
                has_explicit_input = ctx.get('signaling_url') or ctx.get('params')
                
                if test_cases and not ctx.get('__skip_tests__') and not has_explicit_input:
                    # Execute using test cases (which properly populates params)
                    return CLMChapterLoader._execute_test_cases(executor, concrete, config_ctx, test_cases)
                else:
                    # Execute builtin directly (single run)
                    try:
                        from mcard import MCard
                        target = MCard(ctx.get('__input_content__', DEFAULT_TARGET))
                        result = executor.execute(concrete, target, config_ctx)
                        # Capture result in default argument to avoid closure issue
                        return NarrativeMonad.log(f"Executed builtin {builtin}").bind(
                            lambda _, r=result: NarrativeMonad.unit(r)
                        )
                    except Exception as exc:
                        error_msg = str(exc)
                        return NarrativeMonad.log(f"Builtin execution failed: {error_msg}").bind(
                            lambda _, err=error_msg: NarrativeMonad.unit({"success": False, "error": err})
                        )
            
            # Get executor for regular runtimes
            if CLMChapterLoader._is_clm_runtime(runtime):
                executor = CLMChapterLoader._create_recursive_executor(
                    yaml_path, runtime, chapter_data, clm_data
                )
            else:
                executor = RuntimeFactory.get_executor(runtime)
                if not executor:
                    return NarrativeMonad.log(f"Error: Runtime {runtime} not available").bind(
                        lambda _: NarrativeMonad.unit(None)
                    )
            
            # Execute based on test cases
            test_cases = clm_data.get('balanced', {}).get('test_cases', [])
            
            if not test_cases or ctx.get('__skip_tests__'):
                return CLMChapterLoader._execute_single_run(executor, concrete, config_ctx, runtime)
            else:
                return CLMChapterLoader._execute_test_cases(executor, concrete, config_ctx, test_cases)

        
        action = NarrativeMonad.unit(None).bind(logic_func)
        
        return Chapter(
            id=chapter_data['id'],
            title=chapter_data['title'],
            clm=clm,
            mvp_card=chapter_data['mvp_card'],
            pkc_task=chapter_data['pkc_task'],
            action=action
        )
