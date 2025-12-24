"""
PTR CLI - Polynomial Type Runtime Command Line Interface

This is the canonical CLI for executing CLM (Cubical Logic Model) specifications.

Usage:
    python -m mcard.ptr.cli run <file.yaml> [--context '{"a": 1}']
    python -m mcard.ptr.cli run <file.yaml> --test
    python -m mcard.ptr.cli status
    python -m mcard.ptr.cli list

Examples:
    python -m mcard.ptr.cli run chapters/chapter_01_arithmetic/advanced_comparison.yaml
    python -m mcard.ptr.cli run my_clm.yaml --context '{"debug": true}'
    python -m mcard.ptr.cli run my_clm.yaml --test
    python -m mcard.ptr.cli status
"""

import argparse
import json
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from .runner import CLMRunner
from .core.runtime import RuntimeFactory


# ─────────────────────────────────────────────────────────────────────────────
# Setup and Utilities
# ─────────────────────────────────────────────────────────────────────────────

def setup_logging(level: int = logging.INFO) -> None:
    """Configure basic logging for CLI output."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def parse_context(ctx_str: str) -> Dict[str, Any]:
    """Parse JSON context string into dictionary."""
    if not ctx_str or ctx_str == "{}":
        return {}
    try:
        return json.loads(ctx_str)
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing context JSON: {e}", file=sys.stderr)
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────────────────────────────────────

def run_command(args: argparse.Namespace) -> None:
    """Execute a CLM/PCard file."""
    runner = CLMRunner()
    context = parse_context(args.context)
    
    # Add file directory to context for relative path resolution
    file_path = Path(args.file)
    if file_path.exists():
        context['pcard_dir'] = str(file_path.parent.absolute())
    
    try:
        print(f"📄 Loading CLM from: {args.file}")
        report = runner.run_file(args.file, context=context)
        
        if args.test:
            # Display test results in human-readable format
            _display_test_results(report)
        else:
            # Pretty print JSON result
            print(json.dumps(report, indent=2, default=str))
        
        if report["status"] != "success":
            sys.exit(1)
            
    except FileNotFoundError as e:
        print(f"❌ File not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Execution failed: {str(e)}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _display_test_results(report: Dict[str, Any]) -> None:
    """Display test results in human-readable format."""
    result = report.get("result", {})
    
    print(f"\n{'='*60}")
    print(f"📊 Test Results: {report.get('chapter_title', 'Unknown')}")
    print(f"{'='*60}")
    
    # Handle various result structures
    if isinstance(result, dict):
        # Check for examples in result
        examples = result.get("examples", [])
        if examples:
            passed = sum(1 for ex in examples if ex.get("consensus", False))
            total = len(examples)
            
            for i, ex in enumerate(examples, 1):
                status = "✅" if ex.get("consensus", False) else "❌"
                desc = ex.get("description", f"Example #{i}")
                print(f"{status} {desc}")
                
                if not ex.get("consensus", False):
                    if "error" in ex:
                        print(f"   Error: {ex['error']}")
                    if "results" in ex:
                        print(f"   Results: {ex['results']}")
            
            print(f"\n{'='*60}")
            print(f"Summary: {passed}/{total} PASSED")
        else:
            # Single result
            success = result.get("consensus", result.get("success", False))
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"Result: {status}")
            if "output" in result:
                print(f"Output: {result['output']}")
    else:
        # Primitive result
        print(f"Result: {result}")
    
    print()


def status_command(args: argparse.Namespace) -> None:
    """Display polyglot runtime status."""
    print("\n🌐 Polyglot Runtime Status")
    print("=" * 60)
    RuntimeFactory.print_status(verbose=args.verbose)
    print()


def list_command(args: argparse.Namespace) -> None:
    """List available CLM files."""
    print("\n📚 Available CLM Files")
    print("=" * 60)
    
    # Search paths
    search_paths = [
        Path('sample_pcards'),
        Path('chapters'),
    ]
    
    found = False
    for search_dir in search_paths:
        if search_dir.exists():
            # Find all YAML/CLM files
            files = sorted(
                list(search_dir.rglob('*.yaml')) + 
                list(search_dir.rglob('*.clm')) +
                list(search_dir.rglob('*.yml'))
            )
            
            if files:
                print(f"\n📁 {search_dir}/")
                for f in files:
                    rel_path = f.relative_to(search_dir.parent) if search_dir.parent != Path('.') else f
                    print(f"   • {rel_path}")
                found = True
    
    if not found:
        print("❌ No CLM files found in sample_pcards/ or chapters/")
    
    print(f"\n💡 Usage: python -m mcard.ptr.cli run <file>")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# Main Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MCard PTR - Polynomial Type Runtime CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m mcard.ptr.cli run my_clm.yaml
  python -m mcard.ptr.cli run my_clm.yaml --context '{"a": 1}'
  python -m mcard.ptr.cli run my_clm.yaml --test --verbose
  python -m mcard.ptr.cli status --verbose
  python -m mcard.ptr.cli list
"""
    )
    
    # Global options
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # ─────────────────────────────────────────────────────────────────────────
    # Run Command
    # ─────────────────────────────────────────────────────────────────────────
    run_parser = subparsers.add_parser(
        'run',
        help='Execute a CLM Chapter/PCard',
        description='Execute a CLM specification from a YAML file.'
    )
    run_parser.add_argument(
        'file',
        help='Path to the CLM/YAML file'
    )
    run_parser.add_argument(
        '--context', '-c',
        default='{}',
        help='JSON string for execution context (default: {})'
    )
    run_parser.add_argument(
        '--test', '-t',
        action='store_true',
        help='Display results in test format'
    )
    run_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    # ─────────────────────────────────────────────────────────────────────────
    # Status Command
    # ─────────────────────────────────────────────────────────────────────────
    status_parser = subparsers.add_parser(
        'status',
        help='Show polyglot runtime status',
        description='Display the status of all polyglot runtimes (Python, JS, Rust, etc.)'
    )
    status_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed status'
    )
    
    # ─────────────────────────────────────────────────────────────────────────
    # List Command
    # ─────────────────────────────────────────────────────────────────────────
    list_parser = subparsers.add_parser(
        'list',
        help='List available CLM files',
        description='List CLM files in sample_pcards/ and chapters/ directories.'
    )
    list_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed listing'
    )
    
    # Parse args
    args = parser.parse_args()
    
    # Setup logging based on verbosity
    if hasattr(args, 'verbose') and args.verbose:
        setup_logging(logging.DEBUG)
    else:
        setup_logging(logging.WARNING)  # Quiet by default for CLI
    
    # Dispatch command
    if args.command == 'run':
        run_command(args)
    elif args.command == 'status':
        status_command(args)
    elif args.command == 'list':
        list_command(args)
    else:
        parser.print_help()
        print("\n💡 Try: python -m mcard.ptr.cli run --help")
        sys.exit(1)


if __name__ == "__main__":
    main()
