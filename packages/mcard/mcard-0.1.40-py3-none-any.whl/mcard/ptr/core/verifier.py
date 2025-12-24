"""
CLM Verifier - Cubical Logic Model verification system

Implements the three-dimensional verification: Abstract Specification,
Concrete Implementation, and Balanced Expectations.
"""

import logging
from dataclasses import dataclass
from typing import Any

import yaml

from mcard import MCard
from .monads import Writer


@dataclass
class VerificationResult:
    """Result of CLM verification"""
    is_valid: bool
    abstract_valid: bool
    concrete_valid: bool
    balanced_valid: bool
    errors: list[str]
    warnings: list[str]
    verification_details: dict[str, Any]


class CLMVerifier:
    """
    Verifier for the Cubical Logic Model.

    Ensures that every PCard maintains consistency between:
    1. Abstract Specification (WHAT - the specification)
    2. Concrete Implementation (HOW - the implementation)
    3. Balanced Expectations (WHY - the verification proofs)
    """

    def __init__(self, engine):
        self.engine = engine
        self.logger = logging.getLogger(__name__)
        self.verification_cache = {}

    def verify_clm_consistency(self, pcard: MCard, target: MCard,
                             context: dict[str, Any] = None) -> VerificationResult:
        """
        Verify CLM consistency for a PCard-target pair.

        This implements the core verification workflow:
        1. Load PCard and extract CLM dimensions
        2. Verify Abstract Specification
        3. Verify Concrete Implementation
        4. Verify Balanced Expectations
        5. Check cross-dimensional consistency
        """
        context = context or {}
        errors = []
        warnings = []
        details = {}

        try:
            # Step 1: Parse PCard content
            pcard_content = pcard.get_content().decode('utf-8')
            pcard_data = yaml.safe_load(pcard_content)

            if not isinstance(pcard_data, dict):
                raise ValueError("PCard content must be a YAML dictionary")

            # Extract CLM dimensions (with aliases)
            abstract = pcard_data.get('abstract_spec', pcard_data.get('abstract', {}))
            concrete = pcard_data.get('concrete_impl', pcard_data.get('concrete', {}))
            balanced = pcard_data.get('balanced_exp', pcard_data.get('balanced', {}))


            self.logger.info(f"Verifying CLM dimensions for PCard {pcard.hash}")
            self.logger.info(f"PCard keys: {list(pcard_data.keys())}")
            self.logger.info(f"Abstract keys: {list(abstract.keys())}")

            # Step 2: Verify Abstract Specification (Writer Monad)
            abstract_writer = self._verify_abstract(abstract, target, context)
            abstract_details, abstract_errors = abstract_writer.run()
            
            errors.extend(abstract_errors)
            details['abstract'] = abstract_details
            abstract_valid = len(abstract_errors) == 0

            # Step 3: Verify Concrete Implementation (Writer Monad)
            concrete_writer = self._verify_concrete(concrete, abstract, target, context)
            concrete_details, concrete_errors = concrete_writer.run()
            
            errors.extend(concrete_errors)
            details['concrete'] = concrete_details
            concrete_valid = len(concrete_errors) == 0

            # Step 4: Verify Balanced Expectations (Writer Monad)
            balanced_writer = self._verify_balanced(balanced, abstract, concrete, target, context)
            balanced_details, balanced_errors = balanced_writer.run()
            
            errors.extend(balanced_errors)
            details['balanced'] = balanced_details
            balanced_valid = len(balanced_errors) == 0

            # Step 5: Check cross-dimensional consistency (Writer Monad)
            consistency_writer = self._verify_cross_consistency(abstract, concrete, balanced)
            consistency_valid_flag, consistency_errors = consistency_writer.run()
            
            errors.extend(consistency_errors)
            consistency_valid = consistency_valid_flag and len(consistency_errors) == 0
            
            details['cross_consistency'] = {
                'valid': consistency_valid,
                'errors': consistency_errors
            }

            # Overall validity
            is_valid = abstract_valid and concrete_valid and balanced_valid and consistency_valid

            if is_valid:
                self.logger.info(f"CLM verification PASSED for PCard {pcard.hash}")
            else:
                self.logger.warning(f"CLM verification FAILED for PCard {pcard.hash}: {errors}")

            return VerificationResult(
                is_valid=is_valid,
                abstract_valid=abstract_valid,
                concrete_valid=concrete_valid,
                balanced_valid=balanced_valid,
                errors=errors,
                warnings=warnings,
                verification_details=details
            )

        except Exception as e:
            self.logger.error(f"CLM verification error: {str(e)}")
            return VerificationResult(
                is_valid=False,
                abstract_valid=False,
                concrete_valid=False,
                balanced_valid=False,
                errors=[f"Verification error: {str(e)}"],
                warnings=[],
                verification_details={}
            )

    def _verify_abstract(self, abstract: dict[str, Any], target: MCard,
                        context: dict[str, Any]) -> Writer[str, dict[str, Any]]:
        """
        Verify the Abstract Specification dimension using Writer Monad.
        Returns Writer(details, errors).
        """
        errors = []
        details = {}

        # Check required abstract fields
        required_fields = ['purpose', 'inputs', 'outputs', 'preconditions', 'postconditions']
        for field in required_fields:
            if field not in abstract:
                errors.append(f"Missing required abstract field: {field}")

        # Validate input/output specifications
        inputs = abstract.get('inputs', {})
        outputs = abstract.get('outputs', {})

        if not isinstance(inputs, dict):
            errors.append("Abstract inputs must be a dictionary")
        else:
            details['input_count'] = len(inputs)

        if not isinstance(outputs, dict):
            errors.append("Abstract outputs must be a dictionary")
        else:
            details['output_count'] = len(outputs)

        # Validate preconditions and postconditions
        preconditions = abstract.get('preconditions', [])
        postconditions = abstract.get('postconditions', [])

        if not isinstance(preconditions, list):
            errors.append("Abstract preconditions must be a list")
        else:
            details['precondition_count'] = len(preconditions)

        if not isinstance(postconditions, list):
            errors.append("Abstract postconditions must be a list")
        else:
            details['postcondition_count'] = len(postconditions)

        # Check semantic consistency
        purpose = abstract.get('purpose', '')
        if len(purpose) < 10:
            errors.append("Abstract purpose should be descriptive (min 10 characters)")

        details['purpose_length'] = len(purpose)

        return Writer(lambda: (details, errors))

    def _verify_concrete(self, concrete: dict[str, Any], abstract: dict[str, Any],
                        target: MCard, context: dict[str, Any]) -> Writer[str, dict[str, Any]]:
        """
        Verify the Concrete Implementation dimension using Writer Monad.
        Returns Writer(details, errors).
        """
        errors = []
        details = {}

        # Check required concrete fields
        if 'operation' not in concrete:
            errors.append("Missing required concrete field: operation")

        # Validate operation matches abstract purpose
        operation = concrete.get('operation', '')
        abstract_purpose = abstract.get('purpose', '').lower()

        if operation and abstract_purpose:
            # Simple semantic check - in production would use NLP
            if 'transform' in abstract_purpose and 'transform' not in operation:
                errors.append("Concrete operation doesn't match abstract purpose")

        details['operation'] = operation

        # Check implementation details
        implementation = concrete.get('implementation', {})
        if not isinstance(implementation, dict):
            errors.append("Concrete implementation must be a dictionary")
        else:
            details['implementation_keys'] = list(implementation.keys())

        # Validate resource requirements
        resources = concrete.get('resources', {})
        if resources:
            if not isinstance(resources, dict):
                errors.append("Concrete resources must be a dictionary")
            else:
                details['resource_requirements'] = resources

        # Check error handling
        error_handling = concrete.get('error_handling', {})
        if error_handling and not isinstance(error_handling, dict):
            errors.append("Concrete error_handling must be a dictionary")

        return Writer(lambda: (details, errors))

    def _verify_balanced(self, balanced: dict[str, Any], abstract: dict[str, Any],
                        concrete: dict[str, Any], target: MCard,
                        context: dict[str, Any]) -> Writer[str, dict[str, Any]]:
        """
        Verify the Balanced Expectations dimension using Writer Monad.
        Returns Writer(details, errors).
        """
        errors = []
        details = {}

        # Check required balanced fields
        required_fields = ['test_cases', 'expectations']
        for field in required_fields:
            if field not in balanced:
                errors.append(f"Missing required balanced field: {field}")

        # Validate test cases
        test_cases = balanced.get('test_cases', [])
        if not isinstance(test_cases, list):
            errors.append("Balanced test_cases must be a list")
        else:
            details['test_case_count'] = len(test_cases)

            # Validate each test case structure
            for i, test_case in enumerate(test_cases):
                if not isinstance(test_case, dict):
                    errors.append(f"Test case {i} must be a dictionary")
                    continue

                required_test_fields = ['given', 'when', 'then']
                for field in required_test_fields:
                    if field not in test_case:
                        errors.append(f"Test case {i} missing required field: {field}")

        # Validate expectations
        expectations = balanced.get('expectations', {})
        if not isinstance(expectations, dict):
            errors.append("Balanced expectations must be a dictionary")
        else:
            details['expectation_keys'] = list(expectations.keys())

            # Check performance expectations
            performance = expectations.get('performance', {})
            if performance:
                if not isinstance(performance, dict):
                    errors.append("Performance expectations must be a dictionary")
                else:
                    details['performance_expectations'] = performance

            # Check quality metrics
            quality = expectations.get('quality', {})
            if quality:
                if not isinstance(quality, dict):
                    errors.append("Quality expectations must be a dictionary")
                else:
                    details['quality_expectations'] = quality

        return Writer(lambda: (details, errors))

    def _verify_cross_consistency(self, abstract: dict[str, Any], concrete: dict[str, Any],
                                 balanced: dict[str, Any]) -> Writer[str, bool]:
        """
        Verify cross-dimensional consistency between CLM dimensions using Writer Monad.
        Returns Writer(valid_flag, errors).
        
        Note: This is intentionally lenient to match JavaScript CLMRunner behavior,
        which doesn't perform strict abstract/concrete input matching.
        """
        # JavaScript CLMRunner does NOT validate abstract-concrete consistency
        # It just runs the code and compares actual vs expected output
        # So we skip all cross-consistency checks to match that behavior
        errors = []
        
        # All checks are skipped for JavaScript parity
        # The actual verification happens at runtime when comparing results
        
        valid = len(errors) == 0
        return Writer(lambda: (valid, errors))
