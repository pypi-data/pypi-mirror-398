"""PCard Model (Control Plane) - Implementation of LENS/CHART values.

This module defines the PCard, which represents the execution unit in the DOTS framework.
PCards are MCards that contain a valid CLM (Cubical Logic Model) specification.
"""

from typing import Optional, Dict, List, Any, Union
import yaml
from mcard.model.card import MCard
from mcard.model.dots import create_pcard_dots_metadata, DOTSMetadata

class PCard(MCard):
    """PCard - The Control Plane unit (Lens + Chart).
    
    A PCard is an MCard whose content is a valid CLM specification.
    
    Categorical Role:
        - Petri Net (UPTV): Transition (Process). Consumes VCards, produces VCards.
        - Category Theory: Functor (`fmap`). Maps pure logic over MCard containers.
    
    DOTS Role:
        - LENS: When viewed as a tight morphism (Abstract <-> Concrete).
        - CHART: When viewed as a loose morphism (Interaction Pattern).
        
    CLM Triad Structure:
        - Abstract (A): Specification (Thesis)
        - Concrete (C): Implementation (Antithesis)
        - Balanced (B): Evidence/Tests (Synthesis)
    """
    
    def __init__(self, content: Union[str, bytes], hash_function: Union[str, Any] = "sha256"):
        """Initialize a PCard.
        
        Args:
            content: The CLM YAML string.
            hash_function: Hash function to use.
            
        Raises:
            ValueError: If content is not valid YAML or valid CLM structure.
        """
        super().__init__(content, hash_function)
        self._parsed_clm = self._validate_and_parse()
        
    def _validate_and_parse(self) -> Dict[str, Any]:
        """Validate content is valid YAML CLM and return parsed dict."""
        try:
            content_str = self.get_content(as_text=True)
            clm = yaml.safe_load(content_str)
            
            if not isinstance(clm, dict):
                raise ValueError("PCard content must be a YAML dictionary")
                
            return clm
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML content for PCard: {e}")
            
    def get_dots_metadata(self) -> DOTSMetadata:
        """Get DOTS metadata for this PCard."""
        tight_refs = []
        loose_refs = []
        
        # Extract dependencies if they exist in standard CLM fields
        for key in ['tight_deps', 'dependencies']:
            if key in self._parsed_clm and isinstance(self._parsed_clm[key], list):
                tight_refs.extend(self._parsed_clm[key])
                
        for key in ['loose_deps', 'alternatives']:
            if key in self._parsed_clm and isinstance(self._parsed_clm[key], list):
                loose_refs.extend(self._parsed_clm[key])
        
        return create_pcard_dots_metadata(
            spec_hash=self.hash,
            tight_refs=tight_refs if tight_refs else None,
            loose_refs=loose_refs if loose_refs else None
        )
    
    @property
    def clm(self) -> Dict[str, Any]:
        """Get the parsed CLM dictionary."""
        return self._parsed_clm
    
    # -------------------------------------------------------------------------
    # UPTV CLM Triad Accessors (A x C x B)
    # -------------------------------------------------------------------------

    @property
    def abstract(self) -> Optional[Dict[str, Any]]:
        """Get the Abstract (A) section."""
        # Check standard UPTV key first, then legacy aliases
        return (self._parsed_clm.get('abstract') or 
                self._parsed_clm.get('abstract_spec'))
        
    @property
    def concrete(self) -> Optional[Dict[str, Any]]:
        """Get the Concrete (C) section."""
        return (self._parsed_clm.get('concrete') or 
                self._parsed_clm.get('concrete_impl') or 
                self._parsed_clm.get('impl'))

    @property
    def balanced(self) -> Optional[Dict[str, Any]]:
        """Get the Balanced (B) section."""
        return (self._parsed_clm.get('balanced') or 
                self._parsed_clm.get('balanced_expectations') or 
                self._parsed_clm.get('expectations'))

    # -------------------------------------------------------------------------
    # Legacy Aliases (Strict Backward Compatibility)
    # -------------------------------------------------------------------------

    @property
    def abstract_spec(self) -> Optional[Dict[str, Any]]:
        """Legacy alias for abstract."""
        return self.abstract

    @property
    def concrete_impl(self) -> Optional[Dict[str, Any]]:
        """Legacy alias for concrete."""
        return self.concrete

    @property
    def balanced_expectations(self) -> Optional[Dict[str, Any]]:
        """Legacy alias for balanced."""
        return self.balanced

    # =========================================================================
    # Petri Net Transition Semantics
    # =========================================================================

    def get_input_vcard_refs(self) -> List[Dict[str, Any]]:
        """Get input VCard references (Pre-set: •t).

        These represent the preconditions that must be satisfied before
        this PCard (Transition) can fire.

        Returns:
            List of input VCard references from CLM specification
        """
        refs = []
        clm = self._parsed_clm

        # Check for explicit input_vcards in CLM
        input_vcards = (clm.get('input_vcards') or
                        clm.get('preconditions') or
                        clm.get('requires'))

        if isinstance(input_vcards, list):
            for ref in input_vcards:
                if isinstance(ref, str):
                    refs.append({'handle': ref})
                elif isinstance(ref, dict) and 'handle' in ref:
                    refs.append({
                        'handle': ref['handle'],
                        'expected_hash': ref.get('hash') or ref.get('expected_hash'),
                        'purpose': ref.get('purpose')
                    })

        # Also check verification.pcard_refs for authentication requirements
        verification = clm.get('clm', {}).get('verification') or clm.get('verification')
        if verification:
            pcard_refs = verification.get('pcard_refs', [])
            for ref in pcard_refs:
                if isinstance(ref, str):
                    refs.append({
                        'handle': f"auth://{ref}",
                        'purpose': 'authenticate'
                    })
                elif isinstance(ref, dict) and 'hash' in ref:
                    refs.append({
                        'handle': f"auth://{ref['hash']}",
                        'expected_hash': ref['hash'],
                        'purpose': ref.get('purpose', 'authenticate')
                    })
        
        return refs

    def get_output_vcard_specs(self) -> List[Dict[str, Any]]:
        """Get output VCard specifications (Post-set: t•).

        These define what VCards (Tokens) this PCard produces when fired.

        Returns:
            List of output VCard specifications
        """
        specs = []
        clm = self._parsed_clm

        # Check for explicit output_vcards in CLM
        output_vcards = (clm.get('output_vcards') or
                         clm.get('postconditions') or
                         clm.get('produces'))

        if isinstance(output_vcards, list):
            for spec in output_vcards:
                if isinstance(spec, str):
                    specs.append({'handle': spec, 'type': 'result'})
                elif isinstance(spec, dict) and 'handle' in spec:
                    specs.append({
                        'handle': spec['handle'],
                        'type': spec.get('type', 'result'),
                        'metadata': spec.get('metadata')
                    })

        # Default: produce a verification VCard at balanced handle
        if not specs:
            chapter = clm.get('chapter')
            if chapter and isinstance(chapter, dict) and chapter.get('title'):
                import re
                safe_name = re.sub(r'[^a-z0-9]', '_', chapter['title'].lower())
                specs.append({
                    'handle': f"clm://{safe_name}/balanced",
                    'type': 'verification'
                })

        return specs

    def get_transition_handle(self) -> str:
        """Get the canonical handle for this PCard (Transition).

        Returns:
            Handle string in form `clm://{module}/{function}/spec`
        """
        chapter = self._parsed_clm.get('chapter')
        if chapter and isinstance(chapter, dict) and 'id' in chapter:
            title = chapter.get('title')
            if title:
                import re
                safe_name = re.sub(r'[^a-z0-9]', '_', title.lower())
            else:
                safe_name = f"chapter_{chapter['id']}"
            return f"clm://{safe_name}/spec"
        
        # Fallback to hash-based handle
        return f"clm://hash/{self.hash[:16]}/spec"

    def get_balanced_handle(self) -> str:
        """Get the balanced expectations handle for this PCard.

        This is where verification history is tracked in handle_history.

        Returns:
            Handle string for balanced expectations
        """
        spec_handle = self.get_transition_handle()
        return spec_handle.replace('/spec', '/balanced')

    def can_fire(self, available_vcards: Dict[str, str]) -> Dict[str, Any]:
        """Check if this PCard (Transition) can fire given the available VCards.

        A transition can fire when all input VCards (preconditions) are present.

        Args:
            available_vcards: Dict of handle -> VCard hash

        Returns:
            Dict containing 'can_fire' (bool) and 'missing' (list of handles)
        """
        input_refs = self.get_input_vcard_refs()
        missing = []

        for ref in input_refs:
            handle = ref['handle']
            expected_hash = ref.get('expected_hash')
            
            vcard_hash = available_vcards.get(handle)
            if not vcard_hash:
                missing.append(handle)
            elif expected_hash and vcard_hash != expected_hash:
                missing.append(f"{handle} (hash mismatch)")

        return {
            'can_fire': len(missing) == 0,
            'missing': missing
        }

    def get_runtime(self) -> str:
        """Get the runtime required for this PCard.

        Returns:
            Runtime name (e.g., 'javascript', 'python', 'lean')
        """
        clm_config = self._parsed_clm.get('clm', {}).get('concrete')
        concrete = self._parsed_clm.get('concrete')
        
        if clm_config and 'runtime' in clm_config:
            return clm_config['runtime']
        if concrete and 'runtime' in concrete:
            return concrete['runtime']
        
        # Default or try logic_source detection?
        return 'javascript' # Default in JS implementation too

    def is_multi_runtime(self) -> bool:
        """Check if this is a multi-runtime PCard.

        Returns:
            True if this PCard supports multiple runtimes
        """
        clm_config = self._parsed_clm.get('clm', {}).get('concrete')
        concrete = self._parsed_clm.get('concrete')
        
        config = clm_config or concrete
        return config and isinstance(config.get('runtimes_config'), list) and len(config['runtimes_config']) > 1
