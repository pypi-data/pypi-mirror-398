"""
DEPRECATED: This module is deprecated in favor of `mcard.ptr.cli`.

The PTR CLI has been consolidated into mcard/ptr/cli.py.

New usage:
    python -m mcard.ptr.cli run <file.yaml>
    python -m mcard.ptr.cli status
    python -m mcard.ptr.cli list

This module will be removed in a future release.
"""

import warnings
import sys

# Issue deprecation warning on import
warnings.warn(
    "mcard.cli is deprecated. Use 'python -m mcard.ptr.cli' instead.",
    DeprecationWarning,
    stacklevel=2
)


def main():
    """Deprecated entry point - redirects to new CLI."""
    print("⚠️  WARNING: 'ptr' command is deprecated.")
    print("   Please use: python -m mcard.ptr.cli <command>")
    print()
    print("Examples:")
    print("   python -m mcard.ptr.cli run my_file.yaml")
    print("   python -m mcard.ptr.cli status")
    print("   python -m mcard.ptr.cli list")
    print()
    print("Redirecting to new CLI...")
    print()
    
    # Import and call the new CLI
    from mcard.ptr.cli import main as ptr_main
    
    # Transform old-style args to new-style
    # Old: ptr file.yaml  ->  New: python -m mcard.ptr.cli run file.yaml
    # Old: ptr --status   ->  New: python -m mcard.ptr.cli status
    # Old: ptr --list     ->  New: python -m mcard.ptr.cli list
    
    args = sys.argv[1:]
    new_args = ['mcard.ptr.cli']  # Program name placeholder
    
    if '--status' in args:
        new_args.append('status')
        if '-v' in args or '--verbose' in args:
            new_args.append('--verbose')
    elif '--list' in args:
        new_args.append('list')
    elif args:
        # Assume first non-flag arg is a file
        new_args.append('run')
        for arg in args:
            if arg in ['--test', '-v', '--verbose']:
                new_args.append(arg)
            elif not arg.startswith('--'):
                new_args.append(arg)
    else:
        new_args.append('--help')
    
    sys.argv = new_args
    ptr_main()


if __name__ == '__main__':
    main()
