"""
CLM Runner - Unified execution mechanism for CLM/YAML specifications.

Provides a consistent API to execute CLM Chapters and PCards efficiently,
abstracting away the details of Loading, Assembly, and Runtime orchestration.
"""

import os
import yaml
import json
import logging
from typing import Dict, Any, Optional, Tuple, Union

# from .core.engine import PTREngine
from .clm.loader import CLMChapterLoader
# from .clm.assembler import CLMAssembler # Future use

class CLMRunner:
    """
    Unified Runner for CLM execution.
    
    Supports:
    1. Chapter Mode: Executing full Narrative Chapters (.yaml with 'chapter' key)
    2. PCard Mode: Executing raw PCards (Future)
    """
    
    def __init__(self, collection=None):
        self.logger = logging.getLogger(__name__)
        # Engine could be used for lower-level PCard execution
        # self.engine = PTREngine()  # Currently unused in CLMRunner flow
        self.collection = collection

    def run_file(self, file_path: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a CLM specification from a file.
        
        Args:
            file_path: Path to the YAML file.
            context: Execution context (inputs).
            
        Returns:
            Dict containing the execution report/result.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # 1. Peek at file content to determine type
        with open(file_path, 'r') as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML file: {e}")
                
        context = context or {}
        
        # 2. Dispatch based on type
        if 'chapter' in data or 'clm' in data or ('abstract' in data and 'concrete' in data):
            # Treat all capable CLMs as chapters for uniform execution
            return self._run_chapter(file_path, data, context)
        else:
             raise ValueError("Unknown file format. Expected 'chapter', 'clm', or 'abstract'/'concrete' keys.")

    def _run_chapter(self, file_path: str, data: Dict, context: Dict) -> Dict[str, Any]:
        """Execute a CLM Chapter."""
        self.logger.info(f"Executing Chapter from: {file_path}")
        
        # Load Chapter
        chapter = CLMChapterLoader.load_from_yaml(file_path)
        
        # Prepare Context
        # Merge YAML-defined balanced/concrete configs into run context
        # This mirrors the logic we wrote in 'run_advanced_check.py'
        
        clm_section = data.get('clm', None)
        if clm_section:
            concrete_config = clm_section.get('concrete', {})
            balanced_config = clm_section.get('balanced', {})
        else:
            # Raw PCard format (root)
            concrete_config = data.get('concrete', {})
            balanced_config = data.get('balanced', {})
        
        run_ctx = {
            "runtimes_config": concrete_config.get("runtimes_config", []),
            "balanced": balanced_config,
            "examples": data.get("examples", [])
        }
        
        # Mix in provided runtime context (overrides)
        run_ctx.update(context)
        
        # Also include other concrete props
        for k, v in concrete_config.items():
            if k not in run_ctx:
                run_ctx[k] = v
                
        # Execute Monadic Action
        result, new_state, logs = chapter.run(run_ctx, {'collection': self.collection})
        
        if isinstance(result, dict):
            # Check for standard status keys
            if "consensus" in result:
                is_success = result["consensus"]
            elif "success" in result:
                is_success = result["success"]
            else:
                # If just a data payload, assume success unless it contains "error" key
                is_success = "error" not in result
        else:
            # If result is not a dict (e.g. primitive int/str), consider it success if it exists
            # This supports simple chapters like the Prologue counter
            is_success = result is not None
        report = {
            "status": "success" if is_success else "failure",
            "result": result,
            "logs": logs,
            "chapter_id": chapter.id,
            "chapter_title": chapter.title
        }
        
        return report
