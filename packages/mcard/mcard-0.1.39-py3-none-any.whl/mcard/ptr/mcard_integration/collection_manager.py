"""
Collection Manager - Dynamic CLM assembly using MCard Collections

Manages the dynamic assembly of CLM specifications from individual
components stored in MCard Collections, providing a high-level interface
for PTR operations.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from mcard import CardCollection

from ..clm.assembler import AssembledCLM, CLMAssembler
from ..clm.loader import YAMLTemplateLoader
from .storage import MCardStorage


@dataclass
class CollectionStats:
    """Statistics for a managed collection"""
    total_cards: int
    pcard_count: int
    vcard_count: int
    clm_component_count: int
    assembled_clm_count: int
    last_updated: datetime


class CollectionManager:
    """
    High-level manager for PTR operations using MCard Collections.

    This class provides:
    - Dynamic CLM assembly from components
    - PCard and VCard management
    - Template loading and storage
    - Search and discovery capabilities
    - Statistics and monitoring
    """

    def __init__(self, collection: CardCollection = None):
        self.logger = logging.getLogger(__name__)
        self.collection = collection or CardCollection()

        # Initialize sub-components
        self.storage = MCardStorage(self.collection)
        self.template_loader = YAMLTemplateLoader(storage_collection=self.collection)
        self.clm_assembler = CLMAssembler(storage_collection=self.collection,
                                        template_loader=self.template_loader)

        self.logger.info("Collection Manager initialized")

    def create_pcard_from_templates(self, abstract_template: str, concrete_template: str,
                                  balanced_template: str, name: str = None,
                                  metadata: dict[str, Any] = None) -> dict[str, Any]:
        """
        Create a complete PCard from YAML templates.

        Args:
            abstract_template: YAML content for abstract dimension
            concrete_template: YAML content for concrete dimension
            balanced_template: YAML content for balanced dimension
            name: Optional name for the PCard
            metadata: Additional metadata

        Returns:
            Dictionary with creation results and hashes
        """
        try:
            # Parse templates
            import yaml
            abstract_data = yaml.safe_load(abstract_template)
            concrete_data = yaml.safe_load(concrete_template)
            balanced_data = yaml.safe_load(balanced_template)

            # Create PCard content
            pcard_content = {
                "abstract": abstract_data,
                "concrete": concrete_data,
                "balanced": balanced_data
            }

            # Add metadata
            pcard_metadata = {
                "name": name or f"PCard_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                "created_from": "templates",
                "template_count": 3
            }
            if metadata:
                pcard_metadata.update(metadata)

            # Store PCard
            storage_result = self.storage.store_pcard(pcard_content, pcard_metadata)

            if not storage_result.success:
                raise ValueError(f"Failed to store PCard: {storage_result.error_message}")

            self.logger.info(f"Created PCard from templates: {storage_result.hash}")

            return {
                "success": True,
                "pcard_hash": storage_result.hash,
                "metadata": storage_result.metadata,
                "components": {
                    "abstract": abstract_data,
                    "concrete": concrete_data,
                    "balanced": balanced_data
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to create PCard from templates: {str(e)}")
            return {
                "success": False,
                "error_message": str(e)
            }

    def create_pcard_from_clm_assembly(self, assembled_clm: AssembledCLM,
                                     name: str = None, metadata: dict[str, Any] = None) -> dict[str, Any]:
        """
        Create a PCard from an assembled CLM.

        Args:
            assembled_clm: AssembledCLM object
            name: Optional name for the PCard
            metadata: Additional metadata

        Returns:
            Dictionary with creation results
        """
        try:
            # Extract CLM content from assembly
            pcard_content = {
                "abstract": assembled_clm.abstract.content,
                "concrete": assembled_clm.concrete.content,
                "balanced": assembled_clm.balanced.content
            }

            # Create metadata
            pcard_metadata = {
                "name": name or assembled_clm.name,
                "created_from": "clm_assembly",
                "assembly_hash": assembled_clm.assembly_hash,
                "validation": {
                    "is_valid": assembled_clm.validation_result.is_valid,
                    "errors": assembled_clm.validation_result.errors,
                    "warnings": assembled_clm.validation_result.warnings
                }
            }
            if metadata:
                pcard_metadata.update(metadata)

            # Store PCard
            storage_result = self.storage.store_pcard(pcard_content, pcard_metadata)

            if not storage_result.success:
                raise ValueError(f"Failed to store PCard: {storage_result.error_message}")

            self.logger.info(f"Created PCard from CLM assembly: {storage_result.hash}")

            return {
                "success": True,
                "pcard_hash": storage_result.hash,
                "metadata": storage_result.metadata,
                "assembly_hash": assembled_clm.assembly_hash
            }

        except Exception as e:
            self.logger.error(f"Failed to create PCard from CLM assembly: {str(e)}")
            return {
                "success": False,
                "error_message": str(e)
            }

    def assemble_clm_from_components(self, abstract_name: str, concrete_name: str,
                                   balanced_name: str, assembly_name: str = None) -> dict[str, Any]:
        """
        Assemble a complete CLM from individual component templates.

        Args:
            abstract_name: Name of abstract template
            concrete_name: Name of concrete template
            balanced_name: Name of balanced template
            assembly_name: Optional name for the assembled CLM

        Returns:
            Dictionary with assembly results
        """
        try:
            # Load templates
            abstract_template = self.template_loader.get_template('abstract', abstract_name)
            concrete_template = self.template_loader.get_template('concrete', concrete_name)
            balanced_template = self.template_loader.get_template('balanced', balanced_name)

            if not abstract_template:
                raise ValueError(f"Abstract template not found: {abstract_name}")
            if not concrete_template:
                raise ValueError(f"Concrete template not found: {concrete_name}")
            if not balanced_template:
                raise ValueError(f"Balanced template not found: {balanced_name}")

            # Create components from templates
            abstract_component = self.clm_assembler.create_component_from_template(
                'abstract', abstract_name, abstract_template.content
            )
            concrete_component = self.clm_assembler.create_component_from_template(
                'concrete', concrete_name, concrete_template.content
            )
            balanced_component = self.clm_assembler.create_component_from_template(
                'balanced', balanced_name, balanced_template.content
            )

            # Assemble CLM
            assembled_clm = self.clm_assembler.assemble_clm(
                abstract_component.mcard_hash,
                concrete_component.mcard_hash,
                balanced_component.mcard_hash,
                assembly_name
            )

            self.logger.info(f"Assembled CLM: {assembled_clm.name} (valid: {assembled_clm.validation_result.is_valid})")

            return {
                "success": True,
                "assembly_hash": assembled_clm.assembly_hash,
                "assembly_name": assembled_clm.name,
                "validation": {
                    "is_valid": assembled_clm.validation_result.is_valid,
                    "errors": assembled_clm.validation_result.errors,
                    "warnings": assembled_clm.validation_result.warnings
                },
                "components": {
                    "abstract": abstract_component.mcard_hash,
                    "concrete": concrete_component.mcard_hash,
                    "balanced": balanced_component.mcard_hash
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to assemble CLM: {str(e)}")
            return {
                "success": False,
                "error_message": str(e)
            }

    def find_executable_pcards(self, filters: dict[str, Any] = None) -> list[dict[str, Any]]:
        """
        Find PCards that are ready for execution (valid CLM assembly).

        Args:
            filters: Optional filters to apply

        Returns:
            List of executable PCard information
        """
        try:
            # Search for PCards
            search_results = self.storage.search_pcards("PCard", filters)
            executable_pcards = []

            for result in search_results:
                if not result.success:
                    continue

                metadata = result.metadata
                content = result.content

                # Check if it has all CLM dimensions
                has_all_dimensions = (
                    'abstract' in content and
                    'concrete' in content and
                    'balanced' in content
                )

                # Check validation status
                validation = metadata.get('validation', {})
                is_valid = validation.get('is_valid', True)  # Assume valid if not specified

                if has_all_dimensions and is_valid:
                    executable_pcards.append({
                        "hash": result.metadata.get('hash', 'unknown'),
                        "name": metadata.get('name', 'unnamed'),
                        "created_at": metadata.get('created_at'),
                        "validation": validation,
                        "dimensions": list(content.keys())
                    })

            self.logger.info(f"Found {len(executable_pcards)} executable PCards")

            return executable_pcards

        except Exception as e:
            self.logger.error(f"Failed to find executable PCards: {str(e)}")
            return []

    def get_clm_components_by_type(self, dimension: str, filters: dict[str, Any] = None) -> list[dict[str, Any]]:
        """
        Get CLM components by dimension type.

        Args:
            dimension: CLM dimension ('abstract', 'concrete', or 'balanced')
            filters: Optional filters

        Returns:
            List of component information
        """
        try:
            # Find compatible components
            components = self.clm_assembler.find_compatible_components(dimension, filters)

            component_list = []
            for component in components:
                component_list.append({
                    "hash": component.mcard_hash,
                    "name": component.name,
                    "dimension": component.dimension,
                    "version": component.version,
                    "dependencies": component.dependencies
                })

            self.logger.info(f"Found {len(component_list)} {dimension} components")

            return component_list

        except Exception as e:
            self.logger.error(f"Failed to get {dimension} components: {str(e)}")
            return []

    def create_verification_vcard(self, pcard_hash: str, target_hash: str,
                               verification_result: dict[str, Any],
                               execution_output: Any = None) -> dict[str, Any]:
        """
        Create a verification VCard as audit evidence.

        Args:
            pcard_hash: Hash of the executed PCard
            target_hash: Hash of the target MCard/VCard
            verification_result: CLM verification results
            execution_output: Output from execution

        Returns:
            Dictionary with VCard creation results
        """
        try:
            # Create VCard content
            vcard_content = {
                "type": "VerificationVCard",
                "subject": {
                    "pcard_hash": pcard_hash,
                    "target_hash": target_hash
                },
                "verifier": "ptr_collection_manager",
                "evidence": {
                    "clm_verification": verification_result,
                    "execution_output": str(execution_output) if execution_output else None,
                    "verification_timestamp": datetime.now(timezone.utc).isoformat()
                }
            }

            # Create metadata
            vcard_metadata = {
                "verification_type": "execution",
                "pcard_hash": pcard_hash,
                "target_hash": target_hash,
                "created_at": datetime.now(timezone.utc).isoformat()
            }

            # Store VCard
            storage_result = self.storage.store_vcard(vcard_content, vcard_metadata)

            if not storage_result.success:
                raise ValueError(f"Failed to store VCard: {storage_result.error_message}")

            self.logger.info(f"Created VerificationVCard: {storage_result.hash}")

            return {
                "success": True,
                "vcard_hash": storage_result.hash,
                "metadata": storage_result.metadata
            }

        except Exception as e:
            self.logger.error(f"Failed to create VerificationVCard: {str(e)}")
            return {
                "success": False,
                "error_message": str(e)
            }

    def get_collection_statistics(self) -> CollectionStats:
        """
        Get comprehensive statistics for the managed collection.

        Returns:
            CollectionStats object with detailed statistics
        """
        try:
            # Get basic storage statistics
            storage_stats = self.storage.get_storage_statistics()

            # Count CLM components
            clm_component_count = 0
            for dimension in ['abstract', 'concrete', 'balanced']:
                components = self.clm_assembler.find_compatible_components(dimension)
                clm_component_count += len(components)

            # Count assembled CLMs
            assembled_clms = self.clm_assembler.list_assembled_clms()
            assembled_clm_count = len(assembled_clms)

            # Create stats object
            stats = CollectionStats(
                total_cards=storage_stats.get('total_cards', 0),
                pcard_count=storage_stats.get('by_type', {}).get('pcard', 0),
                vcard_count=storage_stats.get('by_type', {}).get('vcard', 0),
                clm_component_count=clm_component_count,
                assembled_clm_count=assembled_clm_count,
                last_updated=datetime.now(timezone.utc)
            )

            return stats

        except Exception as e:
            self.logger.error(f"Failed to get collection statistics: {str(e)}")
            return CollectionStats(
                total_cards=0, pcard_count=0, vcard_count=0,
                clm_component_count=0, assembled_clm_count=0,
                last_updated=datetime.now(timezone.utc)
            )

    def search_collection(self, query: str, card_type: str = "all") -> list[dict[str, Any]]:
        """
        Search across the entire collection.

        Args:
            query: Search query
            card_type: Type of cards to search ('all', 'pcard', 'vcard', 'component')

        Returns:
            List of search results
        """
        try:
            all_results = []

            if card_type in ['all', 'pcard']:
                pcard_results = self.storage.search_pcards(query)
                for result in pcard_results:
                    if result.success:
                        all_results.append({
                            "type": "pcard",
                            "hash": result.metadata.get('hash', 'unknown'),
                            "name": result.metadata.get('name', 'unnamed'),
                            "metadata": result.metadata
                        })

            if card_type in ['all', 'vcard']:
                vcard_results = self.storage.search_vcards(query)
                for result in vcard_results:
                    if result.success:
                        all_results.append({
                            "type": "vcard",
                            "hash": result.metadata.get('hash', 'unknown'),
                            "verification_type": result.metadata.get('verification_type', 'unknown'),
                            "metadata": result.metadata
                        })

            if card_type in ['all', 'component']:
                # Search for CLM components
                for dimension in ['abstract', 'concrete', 'balanced']:
                    components = self.clm_assembler.find_compatible_components(dimension)
                    for component in components:
                        if query.lower() in component.name.lower():
                            all_results.append({
                                "type": "component",
                                "dimension": dimension,
                                "hash": component.mcard_hash,
                                "name": component.name,
                                "version": component.version
                            })

            self.logger.info(f"Search for '{query}' found {len(all_results)} results (type: {card_type})")

            return all_results

        except Exception as e:
            self.logger.error(f"Failed to search collection: {str(e)}")
            return []
