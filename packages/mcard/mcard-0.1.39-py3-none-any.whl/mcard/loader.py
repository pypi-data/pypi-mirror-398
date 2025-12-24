"""
File loading and storage operations for MCard.

This module handles the high-level logic of processing files and storing them
into a CardCollection. It uses mcard.file_io for low-level file operations.
"""

import logging
from pathlib import Path
from typing import Any, Optional, Union

from mcard.config.settings import settings
from mcard.model.card_collection import CardCollection
from mcard.model.card import MCard
from mcard import file_io
from mcard.model.interpreter import ContentTypeInterpreter

logger = logging.getLogger(__name__)


def process_and_store_file(
    file_path: Union[str, Path],
    collection: CardCollection,
    *,
    root_path: Optional[Path] = None,
    allow_problematic: bool = False,
    max_bytes_on_problem: Optional[int] = None,
    metadata_only: bool = False,
) -> Optional[dict[str, Any]]:
    """Process a file, create an MCard, and store it in the collection."""
    # Convert to Path object for consistency
    file_path = Path(file_path) if isinstance(file_path, str) else file_path

    try:
        # Check if the file is problematic before processing
        if file_io.is_problematic_file(file_path):
            if not allow_problematic:
                logger.warning(f"Skipping problematic file: {file_path}")
                return None
            # Resolve environment-configured parameters
            if max_bytes_on_problem is None:
                max_bytes_on_problem = settings.file_processing.max_problem_text_bytes
            
            is_known_type = ContentTypeInterpreter._is_known_long_line_extension(
                file_path.suffix.lower()
            )
            wrap_width = (
                settings.file_processing.wrap_width_known
                if is_known_type
                else settings.file_processing.wrap_width_default
            )
            # Process as safe text via streaming normalization
            logger.warning(
                f"Problematic file detected, processing as safe text with soft-wrap (cap {max_bytes_on_problem} bytes, wrap {wrap_width}): {file_path}"
            )
            try:
                streamed = file_io.stream_read_normalized_text(
                    file_path, byte_cap=max_bytes_on_problem, wrap_width=wrap_width
                )
                text = streamed["text"]
                file_info = {
                    "content": text,
                    "filename": Path(file_path).name,
                    "mime_type": "text/plain",
                    "extension": Path(file_path).suffix.lower(),
                    "is_binary": False,
                    "size": len(text),
                    "original_size": streamed["original_size"],
                    "original_sha256_prefix": streamed["original_sha256_prefix"],
                    "normalized": True,
                    "wrap_width": wrap_width,
                }
            except Exception as _e:
                # Last-resort fallback: capped binary
                logger.warning(
                    f"Safe text processing failed, falling back to capped binary ({max_bytes_on_problem} bytes): {file_path}"
                )
                file_info = file_io.process_file_content(
                    file_path,
                    force_binary=True,
                    allow_pathological=True,
                    max_bytes=max_bytes_on_problem,
                )
        else:
            logger.info(f"PROCESSING FILE: {file_path}")
            # Process the file
            logger.info(f"Reading file content: {file_path}")
            file_info = file_io.process_file_content(file_path)
            if not file_info:
                logger.warning(f"No file info returned for: {file_path}")
                return None
            logger.info(
                f"File processed - Type: {file_info.get('mime_type')}, Size: {file_info.get('size')} bytes"
            )

        mcard = None
        # Optionally skip storing content for problematic files if metadata_only is requested
        if metadata_only and file_io.is_problematic_file(file_path):
            pass
        else:
            # Check for empty content (e.g., empty __init__.py files)
            content = file_info.get("content")
            if not content or (isinstance(content, (bytes, str)) and len(content) == 0):
                logger.debug(
                    f"Skipping empty file: {file_path} (empty files cannot be stored as MCards)"
                )
                return {
                    "hash": None,
                    "content_type": file_info.get("mime_type"),
                    "is_binary": file_info.get("is_binary"),
                    "filename": file_info.get("filename"),
                    "size": 0,
                    "file_path": str(file_path),
                    "skipped": True,
                    "skip_reason": "empty_file"
                }
            
            # Create MCard with just the content bytes
            try:
                logger.info(f"Creating MCard for: {file_path}")
                mcard = MCard(content=content)
                logger.info(f"Created MCard with hash: {mcard.get_hash()}")
            except ValueError as e:
                if "empty" in str(e).lower():
                    logger.debug(f"Skipping file with empty content: {file_path}")
                    return None
                logger.error(f"Failed to create MCard for {file_path}: {e}")
                return None
            except Exception as _e:
                logger.error(
                    f"Failed to create MCard for {file_path}", exc_info=True
                )
                return None
            # Add to collection and Handle Registration
            try:
                logger.info(f"Adding MCard to collection for: {file_path}")
                added_hash = collection.add(mcard)
                
                # --- Handle Registration Logic ---
                # 1. Try filename handle
                handle = file_path.name
                try:
                    collection.engine.register_handle(handle, added_hash)
                    logger.info(f"Registered handle '{handle}' for {file_path.name}")
                except ValueError:
                    # 2. Name taken: Try relative path handle
                    if root_path:
                        try:
                            rel_path = str(file_path.relative_to(root_path))
                            collection.engine.register_handle(rel_path, added_hash)
                            logger.info(f"Registered handle '{rel_path}' (fallback) for {file_path.name}")
                        except ValueError:
                            # Both name and path already registered - content still stored by hash
                            logger.debug(
                                f"Handle name '{handle}' already in use (common for files like README.md, LICENSE). "
                                f"MCard stored successfully with hash {added_hash[:8]}... (accessible by hash, not by handle)"
                            )
                    else:
                        logger.debug(
                            f"Handle name '{handle}' already in use. "
                            f"MCard stored successfully with hash {added_hash[:8]}... (accessible by hash, not by handle)"
                        )
                # ---------------------------------

                logger.info(
                    f"Successfully added MCard to collection for: {file_path}"
                )
            except Exception as _e:
                logger.error(
                    f"Failed to add MCard to collection for {file_path}",
                    exc_info=True,
                )
                return None

        # Prepare and return processing info
        result = {
            "hash": mcard.get_hash() if mcard else None,
            "content_type": file_info.get("mime_type"),
            "is_binary": file_info.get("is_binary"),
            "filename": file_info.get("filename"),
            "size": file_info.get("size"),
            "file_path": str(file_path),
        }
        # Surface original bytes metadata if present
        if "original_size" in file_info:
            result["original_size"] = file_info["original_size"]
        if "original_sha256_prefix" in file_info:
            result["original_sha256_prefix"] = file_info["original_sha256_prefix"]
        if metadata_only and file_io.is_problematic_file(file_path):
            result["metadata_only"] = True

        logger.info(f"COMPLETED processing file: {file_path}")
        return result

    except (TimeoutError, ValueError) as e:
        logger.warning(f"Skipping problematic file {file_path}: {e}")
        return None
    except Exception as _e:
        logger.error(f"Error processing {file_path}", exc_info=True)
        return None


def load_file_to_collection(
    path: Union[str, Path],
    collection: CardCollection,
    recursive: bool = False,
    include_problematic: bool = False,
    max_bytes_on_problem: int = 2 * 1024 * 1024,
    metadata_only: bool = False,
) -> dict[str, Any]:
    """
    Load a file or directory of files into the specified collection.

    Returns:
        Dict containing 'metrics' and 'results'.
    """
    path = Path(path).resolve() if isinstance(path, str) else path.resolve()
    results = []
    
    # Identify root for relative path calculation
    root_path = path if path.is_dir() else path.parent
    
    file_paths = []
    if path.is_file():
        file_paths = [path]
    elif path.is_dir():
        file_paths = file_io.list_files(path, recursive=recursive)
    else:
        raise FileNotFoundError(f"Path '{path}' does not exist or is not accessible")

    # Metrics Calculation
    unique_dirs = set()
    max_depth = 0
    
    for fp in file_paths:
        try:
            rel = fp.relative_to(root_path)
            unique_dirs.add(fp.parent)
            # Depth is number of parts in relative path (including filename? No, just dirs usually)
            # "levels of directories" -> usually depth of hierarchy.
            # path parts: 'a/b/c.txt' -> ('a', 'b', 'c.txt') len=3. Depth=2 (folders). 
            # If at root: 'c.txt' -> ('c.txt') len=1. Depth=0.
            current_depth = len(rel.parts) - 1
            if current_depth > max_depth:
                max_depth = current_depth
        except ValueError:
            pass

    metrics = {
        "files_count": len(file_paths),
        "directories_count": len(unique_dirs) if path.is_dir() else 0, # Only count subdirs inside? Or all involved?
        # unique_dirs includes root's subdirs. If path is file, dirs is just parent (which is outside scope usually).
        # Let's count dirs traversed.
        "directory_levels": max_depth
    }
    
    logger.info(f"About to process {len(file_paths)} files")
    for i, file_path in enumerate(file_paths):
        logger.info(f"Processing file {i + 1}/{len(file_paths)}: {file_path}")
        result = process_and_store_file(
            file_path,
            collection,
            root_path=root_path,
            allow_problematic=include_problematic,
            max_bytes_on_problem=max_bytes_on_problem,
            metadata_only=metadata_only,
        )
        if result:
            results.append(result)
        logger.info(f"Completed file {i + 1}/{len(file_paths)}: {file_path}")

    return {
        "metrics": metrics,
        "results": results
    }
