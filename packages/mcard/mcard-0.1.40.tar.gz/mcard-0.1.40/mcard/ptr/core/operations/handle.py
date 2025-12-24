"""
Handle versioning and pruning operations.
"""

from typing import Any, Dict

from mcard import MCard

from .base import ExampleRunnerMixin


def op_handle_version(impl: Dict, target: MCard, ctx: Dict) -> Any:
    """Handle versioning builtin: update a handle through multiple versions."""
    # Check for examples list (batch mode)
    examples = ctx.get('examples', [])
    if examples:
        return _run_version_examples(examples)
    
    # Single execution mode
    input_data = ctx.get('input', ctx)
    handle = input_data.get('handle', ctx.get('handle', ''))
    versions = input_data.get('versions', ctx.get('versions', []))
    
    if not handle:
        return {'success': False, 'error': 'handle is required'}
    if not versions:
        return {'success': False, 'error': 'versions list is required'}
    
    return _execute_version_single(handle, versions)


def op_handle_prune(impl: Dict, target: MCard, ctx: Dict) -> Any:
    """Handle pruning builtin: prune handle history."""
    # Check for examples list (batch mode)
    examples = ctx.get('examples', [])
    if examples:
        return _run_prune_examples(examples)
    
    # Single execution mode
    input_data = ctx.get('input', ctx)
    handle = input_data.get('handle', ctx.get('handle', ''))
    versions = input_data.get('versions', ctx.get('versions', []))
    prune_type = input_data.get('prune_type', ctx.get('prune_type', 'all'))
    older_than_seconds = input_data.get('older_than_seconds', ctx.get('older_than_seconds'))
    
    if not handle:
        return {'success': False, 'error': 'handle is required'}
    
    return _execute_prune_single(handle, versions, prune_type, older_than_seconds)


# ─────────────────────────────────────────────────────────────────────────────
# Version Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _run_version_examples(examples: list) -> Dict[str, Any]:
    """Run all versioning examples and return aggregated results."""
    
    def executor(input_data: dict) -> Dict[str, Any]:
        handle = input_data.get('handle', '')
        versions = input_data.get('versions', [])
        if not handle or not versions:
            return {'success': False, 'error': 'handle and versions required'}
        return _execute_version_single(handle, versions)
    
    def validator(result: dict, expected: dict) -> bool:
        expected_len = expected.get('history_length')
        if expected_len is not None:
            return result.get('history_length') == expected_len
        return result.get('success', False)
    
    return ExampleRunnerMixin.run_examples(examples, executor, validator)


def _execute_version_single(handle: str, versions: list) -> Dict[str, Any]:
    """Execute a single versioning operation."""
    from mcard.model.card_collection import CardCollection
    collection = CardCollection(db_path=":memory:")
    
    try:
        # Add first version
        first_content = versions[0].get('content', '') if isinstance(versions[0], dict) else versions[0]
        card = MCard(first_content)
        collection.add_with_handle(card, handle)
        
        # Apply subsequent updates
        for version in versions[1:]:
            content = version.get('content', '') if isinstance(version, dict) else version
            new_card = MCard(content)
            collection.update_handle(handle, new_card)
        
        # Get final state
        final_card = collection.get_by_handle(handle)
        history = collection.get_handle_history(handle)
        
        return {
            'success': True,
            'handle': handle,
            'final_hash': final_card.hash if final_card else None,
            'final_content': final_card.get_content(as_text=True) if final_card else None,
            'history_length': len(history),
            'history': history
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# Prune Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _run_prune_examples(examples: list) -> Dict[str, Any]:
    """Run all pruning examples and return aggregated results."""
    
    def executor(input_data: dict) -> Dict[str, Any]:
        handle = input_data.get('handle', '')
        versions = input_data.get('versions', [])
        prune_type = input_data.get('prune_type', 'all')
        older_than_seconds = input_data.get('older_than_seconds')
        if not handle:
            return {'success': False, 'error': 'handle is required'}
        return _execute_prune_single(handle, versions, prune_type, older_than_seconds)
    
    def validator(result: dict, expected: dict) -> bool:
        expected_after = expected.get('history_after')
        expected_deleted = expected.get('deleted')
        if expected_after is not None:
            return result.get('history_after') == expected_after
        if expected_deleted is not None:
            return result.get('deleted') == expected_deleted
        return result.get('success', False)
    
    return ExampleRunnerMixin.run_examples(examples, executor, validator)


def _execute_prune_single(handle: str, versions: list, prune_type: str, older_than_seconds) -> Dict[str, Any]:
    """Execute a single pruning operation."""
    from mcard.model.card_collection import CardCollection
    collection = CardCollection(db_path=":memory:")
    
    try:
        # Setup handle with versions if provided
        if versions:
            first_content = versions[0].get('content', '') if isinstance(versions[0], dict) else versions[0]
            card = MCard(first_content)
            collection.add_with_handle(card, handle)
            
            for version in versions[1:]:
                content = version.get('content', '') if isinstance(version, dict) else version
                new_card = MCard(content)
                collection.update_handle(handle, new_card)
        
        history_before = len(collection.get_handle_history(handle))
        deleted = 0
        
        if prune_type == 'all':
            deleted = collection.prune_handle_history(handle, delete_all=True)
        elif prune_type == 'older_than' and older_than_seconds is not None:
            from datetime import timedelta
            deleted = collection.prune_handle_history(handle, older_than=timedelta(seconds=older_than_seconds))
        
        history_after = len(collection.get_handle_history(handle))
        
        return {
            'success': True,
            'handle': handle,
            'history_before': history_before,
            'deleted': deleted,
            'history_after': history_after
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}
