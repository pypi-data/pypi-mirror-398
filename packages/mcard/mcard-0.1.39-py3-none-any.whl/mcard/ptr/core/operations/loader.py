"""
File loader operation for ingesting files into CardCollection.
"""

import time
from pathlib import Path
from typing import Any, Dict

from mcard import MCard


def op_loader(impl: Dict, target: MCard, ctx: Dict) -> Any:
    """Built-in loader operation using mcard.loader.
    
    Loads files from a directory into a CardCollection.
    
    Context params:
        source_dir: Directory path to load files from
        db_path: Database path for storage
        recursive: Whether to recursively scan directories (default: True)
        include_problematic: Whether to include problematic files (default: False)
    """
    import os
    from mcard.loader import load_file_to_collection
    from mcard.model.card_collection import CardCollection
    
    # Extract parameters from context (merged balanced + test context)
    params = ctx.get('params', {})
    bal = ctx.get('balanced', {})
    
    # Get input/output args from balanced or context
    input_args = {**bal.get('input_arguments', {}), **ctx.get('input_arguments', {})}
    output_args = {**bal.get('output_arguments', {}), **ctx.get('output_arguments', {})}
    
    # Merge all parameter sources
    all_params = {**input_args, **output_args, **params}
    
    source_dir = all_params.get('source_dir', 'test_data')
    db_path = all_params.get('db_path', 'data/loader.db')
    recursive = all_params.get('recursive', True)
    include_problematic = all_params.get('include_problematic', False)
    
    # Resolve source_dir relative to project root if needed
    source_path = Path(source_dir)
    if not source_path.exists():
        cwd = Path(os.getcwd())
        source_path = cwd / source_dir
        if not source_path.exists():
            return {
                'success': False,
                'error': f'Source directory not found: {source_dir}'
            }
    
    # Ensure db directory exists
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Clean slate - remove existing db
    if db_file.exists():
        try:
            os.remove(db_file)
        except OSError:
            pass
    
    try:
        # Initialize collection
        collection = CardCollection(db_path=str(db_path))
        
        # Load files using built-in loader
        t0 = time.time()
        loader_response = load_file_to_collection(
            source_path,
            collection,
            recursive=recursive,
            include_problematic=include_problematic
        )
        load_time = time.time() - t0
        
        # Unpack response
        if isinstance(loader_response, dict) and "results" in loader_response:
            results = loader_response["results"]
            metrics = loader_response.get("metrics", {})
        else:
            results = loader_response
            metrics = {'files_count': len(results)}

        # Calculate metrics
        total_size = sum(r.get('size', 0) for r in results)
        
        return {
            'success': True,
            'metrics': {
                'total_files': metrics.get('files_count', len(results)),
                'total_directories': metrics.get('directories_count', 0),
                'directory_levels': metrics.get('directory_levels', 0),
                'total_size_bytes': total_size,
                'duration_ms': round(load_time * 1000, 2)
            },
            'files': [{
                'hash': r.get('hash', '')[:8],
                'filename': r.get('filename', ''),
                'content_type': r.get('content_type', '')
            } for r in results[:10]]  # Return first 10 for preview
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
