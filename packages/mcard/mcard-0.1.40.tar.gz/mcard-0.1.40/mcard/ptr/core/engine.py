"""
PTR Engine - Core execution engine for Polynomial Type Runtime

The PTREngine serves as the central coordination point for CLM verification
and execution, implementing the sidecar pattern with correctness guarantees
through Object-Process Network principles and computable certificates.

THEORETICAL FOUNDATION:
- Object-Process Network (OPN): Models objects and processes as interacting components
- Correctness Theory: Safety/liveness properties, temporal flow guarantees
- MVP+CLM Integration: Three-dimensional verification with mathematical measures
- Arithmetic of Identity: MCard as Prime Number (Atomic Identity)
- Algebra of Composition: PCard as Polynomial Operator (Structure)

ARCHITECTURAL PRINCIPLES:
1. Separates trust (simple verifier) from complexity (generator)
2. Provides directional alignment measurement (cosine similarity)
3. Ensures invariant preservation (Jacobian determinant check)
4. Implements experimental-operational symmetry (content-addressing)
5. Realizes Efficiency Theorem: Compactness, Computability, Composability
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional, Dict, List, Tuple

from mcard import default_collection

from .lens_protocol import LensProtocol
from .verifier import CLMVerifier
from .common_types import ExecutionResult, VerificationStatus
from .sandbox import SandboxExecutor
from .correctness import CorrectnessTracker
from .certifier import CertificateGenerator
from .monads import IO, Either, Left, Right


class PTREngine:
    """
    Core PTR Engine implementing correctness through Object-Process Network.
    
    CORRECTNESS GUARANTEES:
    1. Safety Properties: Never enters invalid states (enforced by CLM verification)
    2. Liveness Properties: Always makes forward progress (timeout + caching)
    3. Computable Certificates: Verifiable audit trail (VCard generation)
    4. Directional Alignment: Measured alignment with specification (cosine similarity)
    5. Invariant Preservation: Transformations are reversible (|J| != 0)
    
    OBJECT-PROCESS NETWORK DESIGN:
    - Objects: PCards, Target MCards, VCards (entities with state)
    - Processes: Verification, Execution, Certificate Generation (behaviors/actions)
    - Channels: Collection storage, Cache communication
    - Concurrency: Multiple PCard executions can be verified in parallel
    """

    def __init__(self, storage_collection=None, enable_alignment_scoring=False):
        """Initialize PTREngine with correctness tracking.
        
        Args:
            storage_collection: MCard collection for content-addressable storage
            enable_alignment_scoring: Enable directional alignment measurement (requires embeddings)
        """
        self.logger = logging.getLogger(__name__)
        self.collection = storage_collection or default_collection
        
        # Components
        self.verifier = CLMVerifier(self)
        self.lens_protocol = LensProtocol(self)
        self.sandbox = SandboxExecutor(self.collection)
        self.correctness_tracker = CorrectnessTracker(enable_alignment_scoring)
        self.certifier = CertificateGenerator(self.collection)
        
        # Execution Cache (implements Liveness through memoization)
        self.execution_cache: Dict[str, ExecutionResult] = {}

    def execute_pcard(
        self, 
        pcard_hash: str, 
        target_hash: str, 
        context: dict[str, Any] = None,
        specification_embedding: Optional[List[float]] = None
    ) -> ExecutionResult:
        """
        Execute a PCard with full correctness verification.
        
        Implements the complete CLM verification flow with correctness guarantees:
        1. Safety Checking: Verify preconditions (never enter invalid states)
        2. Temporal Progression: Execute with forward progress guarantee
        3. Liveness Verification: Ensure postconditions achieved
        4. Certificate Generation: Create immutable audit evidence
        5. Alignment Measurement: Calculate directional alignment score
        
        Args:
            pcard_hash: Hash of the PCard to execute
            target_hash: Hash of the target MCard/VCard
            context: Execution context parameters
            specification_embedding: Optional embedding vector for alignment scoring
            
        Returns:
            ExecutionResult with verification evidence and correctness measures
        """
        start_time = datetime.now(timezone.utc)
        
        # Execute the monadic pipeline
        result_either = self.execute_pcard_monad(
            pcard_hash, target_hash, context, specification_embedding, start_time
        ).unsafe_run()
        
        if result_either.is_left():
            # Construct failure result
            end_time = datetime.now(timezone.utc)
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return ExecutionResult(
                success=False,
                output=None,
                verification_vcard=None,
                execution_time_ms=execution_time_ms,
                alignment_score=None,
                invariants_preserved=False,
                safety_violations=self.correctness_tracker.safety_violations.copy(),
                liveness_metrics=self.correctness_tracker.liveness_metrics.copy(),
                error_message=result_either.value
            )
            
        return result_either.value

    def execute_pcard_monad(
        self, 
        pcard_hash: str, 
        target_hash: str, 
        context: dict[str, Any],
        specification_embedding: Optional[List[float]],
        start_time: datetime
    ) -> IO[Either[str, ExecutionResult]]:
        """
        Monadic execution pipeline returning IO[Either[Error, ExecutionResult]].
        """
        context = context or {}
        
        def run() -> Either[str, ExecutionResult]:
            try:
                # PHASE 1: SAFETY PRECONDITION CHECKING
                artifacts_res = self._load_artifacts(pcard_hash, target_hash).unsafe_run()
                if artifacts_res.is_left(): return artifacts_res
                
                pcard, target = artifacts_res.value
                self.logger.info(f"Loading PCard {pcard_hash} and target {target_hash}")

                # PHASE 2: CLM VERIFICATION
                verification_res = self._verify_clm(pcard, target, context).unsafe_run()
                if verification_res.is_left(): return verification_res
                
                verification_result = verification_res.value
                self.logger.info(f"CLM verification passed for {pcard_hash}")

                # PHASE 3: LIVENESS CHECK (Caching)
                cache_key = f"{pcard_hash}:{target_hash}:{hash(frozenset(context.items()))}"
                if cache_key in self.execution_cache:
                    self.logger.info(f"Using cached execution result for {cache_key}")
                    self.correctness_tracker.record_liveness_metric("cached_execution", 1.0)
                    return Right(self.execution_cache[cache_key])

                # PHASE 4: TEMPORAL PROGRESSION (Execution)
                # Use SandboxExecutor's monadic interface
                exec_res = self.sandbox.execute_monad(pcard, target, context).unsafe_run()
                if exec_res.is_left(): return exec_res
                
                execution_output = exec_res.value
                self.correctness_tracker.record_liveness_metric("execution_completed", 1.0)

                # PHASE 5: POSTCONDITION VERIFICATION
                alignment_score = self.correctness_tracker.calculate_alignment(
                    execution_output, specification_embedding
                )

                # PHASE 6: INVARIANT PRESERVATION CHECK
                invariants_preserved = self.correctness_tracker.verify_invariant_preservation(
                    pcard, target, execution_output
                )
                
                if not invariants_preserved:
                    self.correctness_tracker.record_safety_violation(
                        "invariant_preservation", "jacobian_zero", 
                        "Transformation is not reversible (|J| = 0)"
                    )

                # PHASE 7: CERTIFICATE GENERATION
                verification_vcard = self.certifier.generate_verification_vcard(
                    pcard_hash, 
                    target_hash, 
                    verification_result, 
                    execution_output,
                    alignment_score,
                    invariants_preserved
                )

                # PHASE 8: RESULT ASSEMBLY
                end_time = datetime.now(timezone.utc)
                execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

                result = ExecutionResult(
                    success=True,
                    output=execution_output,
                    verification_vcard=verification_vcard,
                    execution_time_ms=execution_time_ms,
                    alignment_score=alignment_score,
                    invariants_preserved=invariants_preserved,
                    safety_violations=[],
                    liveness_metrics=self.correctness_tracker.liveness_metrics.copy()
                )

                # Cache result
                self.execution_cache[cache_key] = result
                self.logger.info(
                    f"PCard {pcard_hash} executed successfully in {execution_time_ms}ms "
                    f"(alignment: {alignment_score}, invariants: {invariants_preserved})"
                )

                return Right(result)
                
            except Exception as e:
                self.logger.error(f"PCard execution failed: {str(e)}")
                return Left(str(e))

        return IO(run)

    def _load_artifacts(self, pcard_hash: str, target_hash: str) -> IO[Either[str, Tuple[Any, Any]]]:
        def run() -> Either[str, Tuple[Any, Any]]:
            pcard = self.collection.get(pcard_hash)
            target = self.collection.get(target_hash)

            if not pcard:
                self.correctness_tracker.record_safety_violation(
                    "pcard_existence", "missing_artifact", f"PCard not found: {pcard_hash}"
                )
                return Left(f"PCard not found: {pcard_hash}")
                
            if not target:
                self.correctness_tracker.record_safety_violation(
                    "target_existence", "missing_artifact", f"Target not found: {target_hash}"
                )
                return Left(f"Target not found: {target_hash}")
                
            return Right((pcard, target))
        return IO(run)

    def _verify_clm(self, pcard, target, context) -> IO[Either[str, Any]]:
        def run() -> Either[str, Any]:
            verification_result = self.verifier.verify_clm_consistency(pcard, target, context)

            if not verification_result.is_valid:
                self.correctness_tracker.record_safety_violation(
                    "clm_consistency", "verification_failure", 
                    f"CLM verification failed: {verification_result.errors}"
                )
                return Left(f"CLM verification failed: {verification_result.errors}")
            
            return Right(verification_result)
        return IO(run)

    def evaluate_polynomial(
        self, 
        polynomial_hash: str, 
        target_hash: str, 
        context: dict[str, Any] = None,
        specification_embedding: Optional[List[float]] = None
    ) -> ExecutionResult:
        """
        Evaluate a PCard as a Polynomial Operator: F(X) = Sum(A_i * X^{B_i})
        
        This method is an alias for `execute_pcard` but emphasizes the theoretical
        view of the PCard as a mathematical operator acting on a target (X).
        
        The evaluation process:
        1. Resolves the Polynomial Structure (PCard) from `polynomial_hash`
        2. Applies the Operator to the Target (X) from `target_hash`
        3. Verifies the result against the Modular Constraints (VCard/Context)
        
        Args:
            polynomial_hash: Hash of the PCard (Polynomial Operator)
            target_hash: Hash of the Target (Prime Value)
            context: Modular Constraints (Ring Context)
            specification_embedding: Optional embedding for alignment
            
        Returns:
            ExecutionResult: The computed value with attached proof (VCard)
        """
        return self.execute_pcard(polynomial_hash, target_hash, context, specification_embedding)

    def get_verification_status(self, pcard_hash: str, target_hash: str) -> dict[str, Any]:
        """Get verification status for a PCard-target pair"""
        cache_key = f"{pcard_hash}:{target_hash}"

        if cache_key in self.execution_cache:
            result = self.execution_cache[cache_key]
            return {
                "verified": result.success,
                "verification_vcard": result.verification_vcard,
                "execution_time_ms": result.execution_time_ms,
                "alignment_score": result.alignment_score,
                "invariants_preserved": result.invariants_preserved,
                "error": result.error_message
            }
        else:
            return {"verified": False, "error": "Not yet verified"}

    def get_safety_violations(self) -> List[Dict[str, Any]]:
        """Get all recorded safety violations"""
        return self.correctness_tracker.get_safety_violations()

    def get_liveness_metrics(self) -> List[Dict[str, Any]]:
        """Get all recorded liveness metrics"""
        return self.correctness_tracker.get_liveness_metrics()

    def get_available_runtimes(self) -> Dict[str, bool]:
        """
        Get list of available language runtimes on this system.
        
        Returns:
            Dict mapping runtime name to availability status
        """
        return self.sandbox.list_available_runtimes()

    def run_balanced_tests(self, pcard_hash: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run all test cases defined in the PCard's balanced dimension.
        
        Args:
            pcard_hash: Hash of the PCard to test
            context: Optional base context (e.g. for infrastructure params)
            
        Returns:
            Dict containing test results
        """
        pcard = self.collection.get(pcard_hash)
        if not pcard:
            raise ValueError(f"PCard not found: {pcard_hash}")
            
        import yaml
        pcard_content = pcard.get_content().decode('utf-8')
        pcard_data = yaml.safe_load(pcard_content)
        
        balanced = pcard_data.get('balanced', {})
        test_cases = balanced.get('test_cases', [])
        
        results = {
            'total': len(test_cases),
            'passed': 0,
            'failed': 0,
            'details': []
        }
        
        for i, test_case in enumerate(test_cases):
            description = test_case.get('description', f"Test Case #{i+1}")
            given = test_case.get('given', {})
            expected = test_case.get('then', {})
            
            # Extract input from 'given'
            # Handle different input formats (string, dict, etc.)
            input_val = given
            if isinstance(given, dict) and 'input' in given:
                input_val = given['input']
            elif isinstance(given, dict) and len(given) == 1:
                # If single key dict, assume value is input
                input_val = list(given.values())[0]
                
            # Extract context params from 'when'
            when = test_case.get('when', {})
            test_context = when.get('params', {})
            
            # Merge with base context
            # Base context (infrastructure) + Test context (logic overrides)
            full_context = (context or {}).copy()
            full_context.update(test_context)
                
            # Create target MCard from input
            if isinstance(input_val, str):
                target_content = input_val.encode('utf-8')
            else:
                import json
                target_content = json.dumps(input_val).encode('utf-8')
                
            from mcard import MCard
            target = MCard(target_content)
            self.collection.add(target)
            
            # Execute
            try:
                result = self.execute_pcard(pcard_hash, target.hash, context=full_context)
                
                # Verify output matches expectation
                # This is a simplified check - ideally we'd use a proper matcher
                passed = True
                failure_reason = ""
                
                actual = result.output
                
                # Check each expected output field
                for key, expected_val in expected.items():
                    if key == 'epsilon': continue # Skip epsilon parameter
                    
                    # Handle nested keys if actual is dict
                    actual_val = actual
                    if isinstance(actual, dict) and key in actual:
                        actual_val = actual[key]
                    elif isinstance(actual, (int, float, str)) and key in ['result', 'sine_value', 'value']:
                        # If actual is scalar, compare directly against expected value
                        actual_val = actual
                    
                    # Numeric comparison with epsilon
                    if isinstance(expected_val, (int, float)) and isinstance(actual_val, (int, float)):
                        epsilon = float(expected.get('epsilon', 0))
                        if abs(actual_val - expected_val) > epsilon:
                            passed = False
                            failure_reason = f"Expected {key}={expected_val} (epsilon={epsilon}), got {actual_val}"
                            break
                    elif isinstance(expected_val, dict) and isinstance(actual_val, dict):
                        # Partial dict match (subset check)
                        # Check if all keys/values in expected_val are present in actual_val
                        def check_subset(exp, act, path=""):
                            for k, v in exp.items():
                                if k not in act:
                                    return False, f"Missing key '{path}{k}'"
                                
                                if isinstance(v, dict) and isinstance(act[k], dict):
                                    sub_ok, sub_reason = check_subset(v, act[k], f"{path}{k}.")
                                    if not sub_ok:
                                        return False, sub_reason
                                elif v != act[k]:
                                    return False, f"Value mismatch at '{path}{k}': expected {v}, got {act[k]}"
                            return True, ""

                        subset_ok, subset_reason = check_subset(expected_val, actual_val)
                        if not subset_ok:
                            passed = False
                            failure_reason = f"Dict mismatch for {key}: {subset_reason}"
                            break
                    elif actual_val != expected_val:
                        passed = False
                        failure_reason = f"Expected {key}={expected_val}, got {actual_val}"
                        break
                
                if passed:
                    results['passed'] += 1
                    status = "PASSED"
                else:
                    results['failed'] += 1
                    status = "FAILED"
                    
                results['details'].append({
                    'id': i + 1,
                    'description': description,
                    'status': status,
                    'input': input_val,
                    'expected': expected,
                    'actual': actual,
                    'reason': failure_reason
                })
                
            except Exception as e:
                results['failed'] += 1
                results['details'].append({
                    'id': i + 1,
                    'description': description,
                    'status': "ERROR",
                    'input': input_val,
                    'error': str(e)
                })
                
        return results
