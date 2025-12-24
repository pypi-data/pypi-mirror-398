"""
MCard Storage - Storage interface for PTR using MCard Collections

Provides a high-level storage interface for PTR components,
leveraging MCard's content-addressable storage for immutability
and versioning.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

import yaml

from mcard import CardCollection, MCard


@dataclass
class StorageResult:
    """Result of a storage operation"""
    success: bool
    hash: Optional[str] = None
    error_message: Optional[str] = None
    metadata: dict[str, Any] = None


@dataclass
class RetrievalResult:
    """Result of a retrieval operation"""
    success: bool
    content: Optional[Any] = None
    metadata: dict[str, Any] = None
    error_message: Optional[str] = None


class MCardStorage:
    """
    High-level storage interface for PTR using MCard Collections.

    This class provides:
    - Content-addressable storage with automatic hashing
    - Metadata management and indexing
    - Search and retrieval capabilities
    - Version tracking and history
    """

    def __init__(self, collection: CardCollection = None):
        self.logger = logging.getLogger(__name__)
        self.collection = collection or CardCollection()
        self.metadata_cache = {}  # Cache for metadata lookups

        self.logger.info("MCard Storage initialized")

    def store_pcard(self, pcard_data: dict[str, Any], metadata: dict[str, Any] = None) -> StorageResult:
        """
        Store a PCard with its CLM dimensions.

        Args:
            pcard_data: PCard content with abstract, concrete, balanced dimensions
            metadata: Additional metadata for the PCard

        Returns:
            StorageResult with hash and metadata
        """
        try:
            # Validate PCard structure
            validation_result = self._validate_pcard_structure(pcard_data)
            if not validation_result['valid']:
                return StorageResult(
                    success=False,
                    error_message=f"Invalid PCard structure: {validation_result['errors']}"
                )

            # Create PCard metadata
            pcard_metadata = {
                "type": "PCard",
                "version": "1.0.0",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "clm_dimensions": {
                    "has_abstract": "abstract" in pcard_data,
                    "has_concrete": "concrete" in pcard_data,
                    "has_balanced": "balanced" in pcard_data
                }
            }

            # Merge with provided metadata
            if metadata:
                pcard_metadata.update(metadata)

            # Combine metadata and content
            storage_data = {
                "metadata": pcard_metadata,
                "content": pcard_data
            }

            # Store as MCard
            storage_yaml = yaml.safe_dump(storage_data, default_flow_style=False)
            pcard_mcard = MCard(storage_yaml)
            pcard_hash = self.collection.add(pcard_mcard)

            # Cache metadata
            self.metadata_cache[pcard_hash] = pcard_metadata

            self.logger.info(f"Stored PCard with hash: {pcard_hash}")

            return StorageResult(
                success=True,
                hash=pcard_hash,
                metadata=pcard_metadata
            )

        except Exception as e:
            self.logger.error(f"Failed to store PCard: {str(e)}")
            return StorageResult(
                success=False,
                error_message=str(e)
            )

    def retrieve_pcard(self, pcard_hash: str) -> RetrievalResult:
        """
        Retrieve a PCard by its hash.

        Args:
            pcard_hash: Hash of the PCard to retrieve

        Returns:
            RetrievalResult with PCard content and metadata
        """
        try:
            # Retrieve MCard
            pcard_mcard = self.collection.get(pcard_hash)
            if not pcard_mcard:
                return RetrievalResult(
                    success=False,
                    error_message=f"PCard not found: {pcard_hash}"
                )

            # Parse PCard data
            pcard_yaml = pcard_mcard.get_content().decode('utf-8')
            pcard_data = yaml.safe_load(pcard_yaml)

            # Extract metadata and content
            metadata = pcard_data.get('metadata', {})
            content = pcard_data.get('content', pcard_data)

            # Validate it's a PCard
            if metadata.get('type') != 'PCard':
                return RetrievalResult(
                    success=False,
                    error_message=f"Not a PCard: {pcard_hash}"
                )

            # Cache metadata
            self.metadata_cache[pcard_hash] = metadata

            self.logger.info(f"Retrieved PCard: {pcard_hash}")

            return RetrievalResult(
                success=True,
                content=content,
                metadata=metadata
            )

        except Exception as e:
            self.logger.error(f"Failed to retrieve PCard {pcard_hash}: {str(e)}")
            return RetrievalResult(
                success=False,
                error_message=str(e)
            )

    def store_vcard(self, vcard_data: dict[str, Any], metadata: dict[str, Any] = None) -> StorageResult:
        """
        Store a VCard (verification card) with audit evidence.

        Args:
            vcard_data: VCard content with verification evidence
            metadata: Additional metadata for the VCard

        Returns:
            StorageResult with hash and metadata
        """
        try:
            # Create VCard metadata
            vcard_metadata = {
                "type": "VCard",
                "version": "1.0.0",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "verification_type": vcard_data.get("type", "unknown")
            }

            # Merge with provided metadata
            if metadata:
                vcard_metadata.update(metadata)

            # Combine metadata and content
            storage_data = {
                "metadata": vcard_metadata,
                "content": vcard_data
            }

            # Store as MCard
            storage_yaml = yaml.safe_dump(storage_data, default_flow_style=False)
            vcard_mcard = MCard(storage_yaml)
            vcard_hash = self.collection.add(vcard_mcard)

            # Cache metadata
            self.metadata_cache[vcard_hash] = vcard_metadata

            self.logger.info(f"Stored VCard with hash: {vcard_hash}")

            return StorageResult(
                success=True,
                hash=vcard_hash,
                metadata=vcard_metadata
            )

        except Exception as e:
            self.logger.error(f"Failed to store VCard: {str(e)}")
            return StorageResult(
                success=False,
                error_message=str(e)
            )

    def retrieve_vcard(self, vcard_hash: str) -> RetrievalResult:
        """
        Retrieve a VCard by its hash.

        Args:
            vcard_hash: Hash of the VCard to retrieve

        Returns:
            RetrievalResult with VCard content and metadata
        """
        try:
            # Retrieve MCard
            vcard_mcard = self.collection.get(vcard_hash)
            if not vcard_mcard:
                return RetrievalResult(
                    success=False,
                    error_message=f"VCard not found: {vcard_hash}"
                )

            # Parse VCard data
            vcard_yaml = vcard_mcard.get_content().decode('utf-8')
            vcard_data = yaml.safe_load(vcard_yaml)

            # Extract metadata and content
            metadata = vcard_data.get('metadata', {})
            content = vcard_data.get('content', vcard_data)

            # Validate it's a VCard
            if metadata.get('type') != 'VCard':
                return RetrievalResult(
                    success=False,
                    error_message=f"Not a VCard: {vcard_hash}"
                )

            # Cache metadata
            self.metadata_cache[vcard_hash] = metadata

            self.logger.info(f"Retrieved VCard: {vcard_hash}")

            return RetrievalResult(
                success=True,
                content=content,
                metadata=metadata
            )

        except Exception as e:
            self.logger.error(f"Failed to retrieve VCard {vcard_hash}: {str(e)}")
            return RetrievalResult(
                success=False,
                error_message=str(e)
            )

    def search_pcards(self, query: str, filters: dict[str, Any] = None) -> list[RetrievalResult]:
        """
        Search for PCards using text search and filters.

        Args:
            query: Search query string
            filters: Optional filters to apply

        Returns:
            List of RetrievalResult objects
        """
        try:
            # Perform text search
            found_cards = self.collection.search_by_string(query)
            results = []

            for card in found_cards.items:
                try:
                    # Retrieve and validate it's a PCard
                    retrieval = self.retrieve_pcard(card.hash)
                    if retrieval.success:
                        # Apply filters
                        if filters:
                            match = True
                            metadata = retrieval.metadata

                            for key, value in filters.items():
                                if key == 'type' and metadata.get('verification_type') != value:
                                    match = False
                                    break
                                elif key == 'created_after' and metadata.get('created_at'):
                                    created_at = datetime.fromisoformat(metadata['created_at'])
                                    filter_date = datetime.fromisoformat(value)
                                    if created_at < filter_date:
                                        match = False
                                        break

                            if not match:
                                continue

                        results.append(retrieval)

                except Exception as e:
                    self.logger.warning(f"Failed to process search result {card.hash}: {str(e)}")
                    continue

            self.logger.info(f"Found {len(results)} PCards matching query: {query}")

            return results

        except Exception as e:
            self.logger.error(f"Failed to search PCards: {str(e)}")
            return []

    def search_vcards(self, query: str, filters: dict[str, Any] = None) -> list[RetrievalResult]:
        """
        Search for VCards using text search and filters.

        Args:
            query: Search query string
            filters: Optional filters to apply

        Returns:
            List of RetrievalResult objects
        """
        try:
            # Perform text search
            found_cards = self.collection.search_by_string(query)
            results = []

            for card in found_cards.items:
                try:
                    # Retrieve and validate it's a VCard
                    retrieval = self.retrieve_vcard(card.hash)
                    if retrieval.success:
                        # Apply filters
                        if filters:
                            match = True
                            metadata = retrieval.metadata

                            for key, value in filters.items():
                                if key == 'verification_type' and metadata.get('verification_type') != value:
                                    match = False
                                    break
                                elif key == 'created_after' and metadata.get('created_at'):
                                    created_at = datetime.fromisoformat(metadata['created_at'])
                                    filter_date = datetime.fromisoformat(value)
                                    if created_at < filter_date:
                                        match = False
                                        break

                            if not match:
                                continue

                        results.append(retrieval)

                except Exception as e:
                    self.logger.warning(f"Failed to process search result {card.hash}: {str(e)}")
                    continue

            self.logger.info(f"Found {len(results)} VCards matching query: {query}")

            return results

        except Exception as e:
            self.logger.error(f"Failed to search VCards: {str(e)}")
            return []

    def get_storage_statistics(self) -> dict[str, Any]:
        """
        Get storage statistics and metrics.

        Returns:
            Dictionary with storage statistics
        """
        try:
            total_cards = self.collection.count()

            # Count by type (using search)
            pcard_count = len(self.collection.search_by_string("PCard").items)
            vcard_count = len(self.collection.search_by_string("VCard").items)
            other_count = total_cards - pcard_count - vcard_count

            # Cache statistics
            cache_size = len(self.metadata_cache)

            statistics = {
                "total_cards": total_cards,
                "by_type": {
                    "pcard": pcard_count,
                    "vcard": vcard_count,
                    "other": other_count
                },
                "cache": {
                    "entries": cache_size,
                    "hit_rate": "N/A"  # Would need tracking implementation
                },
                "collection_path": getattr(self.collection.engine.connection, 'db_path', 'in-memory')
            }

            return statistics

        except Exception as e:
            self.logger.error(f"Failed to get storage statistics: {str(e)}")
            return {"error": str(e)}

    def _validate_pcard_structure(self, pcard_data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate the structure of a PCard.

        Args:
            pcard_data: PCard data to validate

        Returns:
            Dictionary with validation result and errors
        """
        errors = []

        if not isinstance(pcard_data, dict):
            errors.append("PCard content must be a dictionary")
            return {"valid": False, "errors": errors}

        # Check for at least one CLM dimension
        clm_dimensions = ['abstract', 'concrete', 'balanced']
        has_dimensions = any(dim in pcard_data for dim in clm_dimensions)

        if not has_dimensions:
            errors.append("PCard must contain at least one CLM dimension (abstract, concrete, or balanced)")

        return {"valid": len(errors) == 0, "errors": errors}

    def clear_cache(self) -> None:
        """Clear the metadata cache."""
        self.metadata_cache.clear()
        self.logger.info("Metadata cache cleared")
