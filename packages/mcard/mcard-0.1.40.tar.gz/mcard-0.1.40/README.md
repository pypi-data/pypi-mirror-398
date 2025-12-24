<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python 3.10+" /></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License" /></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/badge/code%20style-ruff-000000.svg" alt="ruff" /></a>
  <a href="https://github.com/xlp0/MCard_TDD/actions/workflows/ci.yml"><img src="https://github.com/xlp0/MCard_TDD/actions/workflows/ci.yml/badge.svg" alt="Build Status" /></a>
</p>

# MCard

MCard is a local-first, content-addressable storage platform with cryptographic integrity, temporal ordering, and a Polynomial Type Runtime (PTR) that orchestrates polyglot execution. It gives teams a verifiable data backbone without sacrificing developer ergonomics or observability.

---

## Highlights
- 🔐 **Hash-verifiable storage**: Unified network of relationships via SHA-256 hashing across content, handles, and history.
- ♾️ **Universal Substrate**: Emulates the Turing Machine "Infinitely Long Tape" via relational queries for computable DSLs.
- ♻️ **Deterministic execution**: PTR mediates **8 polyglot runtimes** (Python, JavaScript, Rust, C, WASM, Lean, R, Julia).
- 📊 **Enterprise ready**: Structured logging, CI/CD pipeline, security auditing, 99%+ automated test coverage.
- 🧠 **AI-native extensions**: GraphRAG engine, optional LLM runtime, and optimized multimodal vision (`moondream`).
- ⚛️ **Quantum NLP**: Optional `lambeq` + PyTorch integration for pregroup grammar and quantum circuit compilation.
- 🧰 **Developer friendly**: Rich Python API, TypeScript SDK, BMAD-driven TDD workflow, numerous examples.
- 📐 **Algorithm Benchmarks**: Sine comparison (Taylor vs Chebyshev) across Python, C, and Rust.
- ⚡ **High Performance**: Optimized test suite (~37s) with runtime caching and session-scoped fixtures.

For the long-form narrative and chapter roadmap, see **[docs/Narrative_Roadmap.md](docs/Narrative_Roadmap.md)**. Architectural philosophy is captured in **[docs/architecture/Monadic_Duality.md](docs/architecture/Monadic_Duality.md)**.

---

## Quick Start (Python)
```bash
git clone https://github.com/xlp0/MCard_TDD.git
cd MCard_TDD
./activate_venv.sh          # installs uv & dependencies
uv run pytest -q -m "not slow"  # run the fast Python test suite
uv run python -m mcard.ptr.cli run chapters/chapter_01_arithmetic/addition.yaml
```

Create and retrieve a card:
```python
from mcard import MCard, default_collection

card = MCard("Hello MCard")
hash_value = default_collection.add(card)
retrieved = default_collection.get(hash_value)
print(retrieved.get_content(as_text=True))
```

### Quick Start (JavaScript / WASM)
See **[mcard-js/README.md](mcard-js/README.md)** for build, testing, and npm publishing instructions for the TypeScript implementation.

### Quick Start (Quantum NLP)
MCard optionally integrates with **[lambeq](https://cqcl.github.io/lambeq/)** for quantum natural language processing using pregroup grammar:

```bash
# Install with Quantum NLP support (requires Python 3.10+)
uv pip install -e ".[qnlp]"

# Parse a sentence into a pregroup grammar diagram
uv run python scripts/lambeq_web.py "John gave Mary a flower"
```

**Example output** (pregroup types):
```
John: n    gave: n.r @ s @ n.l @ n.l    Mary: n    a flower: n
Result: s (grammatically valid sentence)
```

The pregroup diagrams can be compiled to quantum circuits for QNLP experiments.

---

## Polyglot Runtime Matrix
| Runtime    | Status | Notes |
| ---------- | ------ | ----- |
| Python     | ✅ | Reference implementation, CLM runner |
| JavaScript | ✅ | Node + browser (WASM) + Full RAG Support |
| Rust       | ✅ | High-performance adapter & WASM target |
| C          | ✅ | Low-level runtime integration |
| WASM       | ✅ | Edge and sandbox execution |
| Lean       | ⚙️ | Formal verification pipeline (requires `lean-toolchain`) |
| R          | ✅ | Statistical computing runtime |
| Julia      | ✅ | High-performance scientific computing |

> **⚠️ Lean Configuration**: A `lean-toolchain` file in the project root is **critical**. Without it, `elan` will attempt to resolve/download toolchain metadata on *every invocation*, causing CLM execution to hang or become unbearably slow.

---

## Project Structure (abridged)
```
MCard_TDD/
├── mcard/            # Python package (engines, models, PTR)
├── mcard-js/         # TypeScript implementation & npm package
├── chapters/         # CLM specifications (polyglot demos)
├── docs/             # Architecture, PRD, guides, reports
├── scripts/          # Automation & demo scripts
├── tests/            # >450 automated tests
└── requirements.txt / pyproject.toml
```

---

## Documentation
- Product requirements: [docs/prd.md](docs/prd.md)
- Architecture overview: [docs/architecture.md](docs/architecture.md)
- **Schema principles**: [schema/README.md](schema/README.md) — Stable Seeding Meta-Language, Turing Tape Analogy, and the Unification Thesis.
- **DOTS vocabulary**: [docs/WorkingNotes/Hub/Theory/Integration/DOTS Vocabulary as Efficient Representation for ABC Curriculum.md](docs/WorkingNotes/Hub/Theory/Integration/DOTS%20Vocabulary%20as%20Efficient%20Representation%20for%20ABC%20Curriculum.md)
- Monad–Polynomial philosophy: [docs/architecture/Monadic_Duality.md](docs/architecture/Monadic_Duality.md)
- Narrative roadmap & chapters: [docs/Narrative_Roadmap.md](docs/Narrative_Roadmap.md)
- Logging system: [docs/LOGGING_GUIDE.md](docs/LOGGING_GUIDE.md)
- PTR & CLM reference: [docs/CLM_Language_Specification.md](docs/CLM_Language_Specification.md), [docs/PCard%20Architecture.md](docs/PCard%20Architecture.md)
- Reports & execution summaries: [docs/reports/](docs/reports/)
- Publishing guide: [docs/PUBLISHING_GUIDE.md](docs/PUBLISHING_GUIDE.md)

---

## Recent Updates (December 2025)

### Version 0.1.39 / 2.1.19 — December 20, 2025

#### Church Numeral Decoding & Meta-Circular CLMs

Added human-readable Church numeral decoding and comprehensive meta-circular programming examples.

**Key Features:**

-   **`church-to-int` Operation**: Decodes Church numerals (λf.λx.f^n(x)) to regular integers for human readability. Returns format: `n (Church: <lambda>)`.
-   **`result_contains` Assertion**: Added substring matching support to Python CLM loader for flexible test assertions.
-   **Meta-Circular CLMs**: Added 4 new CLMs demonstrating self-referential language definition:
    -   `dimension_validator.yaml` - Validates CLM triadic structure using Church booleans
    -   `meta_circular_evaluator.yaml` - SICP-style IF-THEN-ELSE combinator
    -   `combinator_library.yaml` - SKI basis proving Turing completeness (S K K = I)
    -   `fixed_point_combinator.yaml` - Y combinator and recursion theory
-   **Vitest Stability**: Fixed segmentation fault during test cleanup by using `forks` pool isolation for better-sqlite3 native module.

**New CLMs:**

-   `church_decoder.yaml` - Demonstrates Church numeral decoding (0-6, addition, multiplication, successor)
-   `traced_arithmetic.yaml` - Complex arithmetic with IO Monad-like reduction tracing

**Test Results (chapter_09_DSL):**

-   **10 CLMs**, **34 examples** — all passing
-   Python: church_decoder - 5 tests passing
-   JavaScript: church_decoder - 7 tests passing

---

### Version 0.1.38 / 2.1.18 — December 20, 2025

#### CLM v1.1 Specification — JavaScript Runtime Alignment

Aligned the JavaScript (mcard-js) runtime with the CLM v1.1 Specification, ensuring cross-platform consistency for the Architecture of Coherence.

**Key Features:**

-   **CLM v1.1 Structural Keys**: Updated `CLMSpec` interface to support new dimension aliases (`abstract_spec`, `concrete_impl`, `balanced_exp`) and narrative keys (`goal`, `context`, `success_criteria`).
-   **Operation Priority**: `process` and `action` keys are now the primary transformation selectors, with `operation` retained for backward compatibility. Context-provided operations (from test inputs) take precedence over CLM config for test flexibility.
-   **Runtime Defaults**: `runtime` now defaults to `lambda` if not specified; `builtin` auto-detects based on runtime type.
-   **System Built-ins**: Added `check-readiness`, `num-add`, `num-sub`, `num-mul`, `num-div`, and `http-request` operations to the Lambda runtime for environmental and utility operations.
-   **Result Unwrapping**: `LambdaRuntimeResult` objects are now automatically unwrapped to return `prettyPrint` for term-returning operations, simplifying test comparisons.

**Fixes:**

-   Fixed `isNetworkBuiltin`, `isLoaderBuiltin`, and `isHandleBuiltin` to handle boolean `builtin` values correctly.
-   Fixed test case mapping to support `when.arguments` in addition to `when.params` and `when.context`.
-   Updated `expected_output` format in `chapter_00_prologue` CLMs from object (`{prettyPrint: "..."}`) to simple string format.

**Test Results:**

-   **chapter_00_prologue**: 5 CLMs passed, 19 examples passed
-   **chapter_09_DSL**: 10 CLMs passed, 34 examples passed
-   Core CLM unit tests: 14 tests passed

---

### Version 0.1.37 / 2.1.17 — December 20, 2025

#### Stable Seeding Meta-Language & Turing Analogy

Refined the schema documentation to articulate its role as a **stable seeding meta-language** and its computational properties.

**Key Concepts:**
-   **The Unification Thesis**: Leverages cryptographic hashes as universal primitives to unite three distinct namespaces (Content Space, Handle Space, and Version Space) into a single verifiable relational network.
-   **Turing Machine Infinitely Long Tape**: The `card` table emulates the "Infinitely Long Tape" of the Turing Machine formalism. By using relational queries, this tape can be dynamically constructed and traversed for any Domain Specific Language (DSL).
-   **Stability Invariance**: Positioned the schema as an invariant kernel that allows for infinite expansion through data without requiring structural modification.

---

### Version 0.1.36 / 2.1.16 — December 16, 2025

#### Feature Parity & UPTV Alignment

Achieved full feature parity between Python and JavaScript runtimes, aligning with the **Unifying Protocol of Truth Verification (UPTV)**.

**Key Updates:**
-   **VCard & Petri Net Parity**:
    -   Aligned VCard implementation with `vcard://` namespace handles.
    -   Enhanced Petri Net Runner to attach `petriNet` metadata (pcardHash, vcardHash) to execution results for full provenance visibility.
    -   Standardized `success` field and `verification` type in VCards.
-   **Global Time Serialization**: Standardized `GTime` serialization to use UTC (`Z` suffix) across both runtimes for consistent timestamp hashing.
-   **Handle Validation**: Relaxed validation to allow colons (`:`), enabling URI-like handles (e.g., `token:REV-1`) necessary for Petri Net tokens.
-   **Refactoring & Cleanup**:
    -   Consolidated `BinarySignatureDetector` logic in Python and JavaScript for consistent MIME type detection.
    -   Cleaned up `CLMRunner` (Python) to remove unused engine dependencies.
    -   Refactored `FileSystemUtils` (JS) to use the central `ContentTypeInterpreter`.

---

### Version 0.1.35 / 2.1.15 — December 15, 2025

#### JavaScript Loader Fixes & Recursive File Loading

Resolved critical database corruption issues in the JavaScript CLM loader runtime and improved recursive file loading reliability.

**Key Fixes:**
- **Database Corruption Fix**: Fixed `SQLITE_CORRUPT: database disk image is malformed` error in JavaScript loader runtime by ensuring proper database connection handling during recursive CLM execution.
- **Loader Runtime Stability**: Improved `LoaderRuntime` to correctly persist data to the specified `db_path` when running `_load_root.yaml` via the JavaScript CLI.
- **Version Sync**: Synchronized `setup.py` version with `pyproject.toml` (was out of sync at 0.1.25).

---

### Version 0.1.34 / 2.1.14 — December 13, 2025

#### VCard Application Vocabulary — Data-Driven Resource Factory

Refactored the VCard vocabulary to be **fully data-driven** following the Empty Schema principle. All 31 resource types are now defined as pure data in modular extension files (`vcard_ext/`), with a single unified factory (`Resource.create()`).

**New Modular Structure**:
```
mcard/model/vcard_ext/          mcard-js/src/model/vcard_ext/
├── __init__.py                 ├── index.ts
├── core.py    (env, file, dir) ├── core.ts
├── storage.py (5 types)        ├── storage.ts
├── network.py (2 types)        ├── network.ts
├── observability.py (6 types)  ├── observability.ts
└── vendors.py (15 types)       └── vendors.ts
```

**31 Resource Types** across 5 categories:

| Category | Types |
|----------|-------|
| **Core** | `env`, `file`, `directory` |
| **Storage** | `sqlite`, `postgres`, `s3`, `litefs`, `turso` |
| **Network** | `api`, `webhook` |
| **Observability** | `grafana`, `prometheus`, `loki`, `tempo`, `faro`, `otlp` |
| **Vendors** | `google`, `github`, `meta`, `whatsapp`, `telegram`, `line`, `wechat`, `slack`, `trello`, `miro`, `figma`, `linkedin`, `aws`, `azure`, `gcp` |

**Usage** (identical in Python & TypeScript):
```python
from mcard.model.vcard_vocabulary import Resource

# Any resource type via unified factory
ref = Resource.create("github", "xlp0", "MCard_TDD")
ref = Resource.create("slack", "my-workspace", "general")
ref = Resource.create("turso", "my-database", group="us-east")
```

**Code Reduction**:
- Python: `vcard_vocabulary.py` reduced from **922 → 334 lines** (64% reduction)
- TypeScript: `vcard_vocabulary.ts` reduced from **700 → 221 lines** (68% reduction)

---

### Version 0.1.33 / 2.1.13 — December 11, 2025

#### Lean 4.25.2 Support & CLM Test Improvements
- **Lean Runtime Update (JavaScript)**: `LeanRuntime` now uses `elan run leanprover/lean4:v4.25.2` to ensure correct toolchain version regardless of system PATH configuration.
- **Modern Lean Syntax**: Updated `lean_gcd.lean` to use Lean 4.8+ syntax (`termination_by b`, `Nat.pos_of_ne_zero`).
- **CLM Test Case Improvements**: Added missing `test_cases` to `loader_orchestrator.clm` and `then` assertions to `verify_loaders.clm`.

### Version 0.1.32 / 2.1.12 — December 11, 2025

#### Major Modularization Refactoring

**Python Runtime Modules** (`mcard/ptr/core/runtimes/`):
- Extracted `PythonRuntime`, `JavaScriptRuntime`, `BinaryRuntime`, `ScriptRuntime`, `LambdaRuntimeExecutor`, and `RuntimeFactory` into separate modules.
- Reduced `runtime.py` from **~1,400 lines to ~115 lines** (92% reduction).
- New module structure: `base.py`, `python.py`, `javascript.py`, `binary.py`, `script.py`, `lambda_calc.py`, `factory.py`.
- Maintained full backward compatibility via re-exports.

**JavaScript Runtime Modules** (`mcard-js/src/ptr/node/runtimes/`):
- Extracted `JavaScriptRuntime`, `PythonRuntime`, `BinaryRuntime`, `WasmRuntime`, `LeanRuntime`, `LoaderRuntime`, and `RuntimeFactory`.
- Reduced `Runtimes.ts` from **583 lines to 62 lines** (89% reduction).
- New module structure: `base.ts`, `javascript.ts`, `python.ts`, `binary.ts`, `wasm.ts`, `lean.ts`, `loader.ts`, `factory.ts`.

**JavaScript CLM Modules** (`mcard-js/src/ptr/node/clm/`):
- Extracted `CLMLoader`, `CLMRunner`, and multi-runtime consensus logic into modular structure.
- Reduced `CLMRunner.ts` from **863 lines to 55 lines** (94% reduction).
- Handle builtins (`handle_version`, `handle_prune`) moved to `clm/builtins/handle.ts`.
- New module structure: `types.ts`, `utils.ts`, `loader.ts`, `runner.ts`, `multiruntime.ts`, `builtins/`.

**Script Cleanup**:
- Removed 6 redundant scripts from `scripts/` directory (28 → 22 files).
- Consolidated CLM execution into single `run_clms.py` CLI.

**JavaScript Runtime Fix**:
- Fixed variable declaration conflicts in `JavaScriptRuntime` by using IIFE pattern.
- Supports all declaration styles (`var`, `let`, `const`) without conflict.

### Version 0.1.31 / 2.1.11 — December 11, 2025

#### Monadic Core & Lean Verification
- **Schema Split**: Separated intrinsic Monadic Core (`mcard.db`) from extrinsic Vector/Graph data (`mcard_vectors.db`) for cleaner architecture and portability.
- **Lean Toolchain**: Fixed Lean CLM execution hangs by enforcing `lean-toolchain` configuration.
- **Auto-Vector DB**: JavaScript `PersistentIndexer` now automatically derives the sidecar vector DB path from the main collection.

### Version 0.1.30 / 2.1.10 — December 10, 2025

#### Handle Validation Improvements
- **Relaxed Handle Rules**: Handles now support periods (`.`), spaces (` `), and forward slashes (`/`) to accommodate file paths and filenames.
- **Extended Length**: Maximum handle length increased from 63 to 255 characters for better file path compatibility.
- **Cross-Runtime Parity**: Synchronized validation logic between Python (`mcard/model/handle.py`) and JavaScript (`mcard-js/src/model/Handle.ts`).
- **Updated Tests**: All handle validation tests updated across both runtimes to reflect new rules.

#### Loader Return Type Standardization
- **Structured Response**: `load_file_to_collection` now returns `{metrics, results}` instead of a plain array.
- **Metrics Object**: Includes `filesCount`, `directoriesCount`, and `directoryLevels` for better observability.
- **Test Updates**: Updated all loader tests to use `response.metrics.filesCount` and `response.results` array.

#### Python Runtime Wrapper Enhancements
- **Smart Function Invocation**: Python wrapper now tries calling with `context` dict first, then `target`, then no args.
- **Error Discrimination**: Added `_is_arg_error()` helper to distinguish TypeError about function arguments from other TypeErrors (e.g., sorting errors).
- **Proper Scope Resolution**: Fixed entry point lookup using `dir()` and `globals()` instead of `locals()`.
- **Builtin Loader Support**: JavaScript PTR now recognizes `builtin: loader` for Python CLMs.

#### Bug Fixes
- **Reflection Logic Sorting**: Fixed `generate_inventory()` and `weave_narrative()` to handle mixed ID types (int, float, string) during sorting.
- **CLM Loader Detection**: Added support for `builtin: load_files` in addition to existing loader detection methods.

### Session: December 10, 2025 — CLM Execution Refinements

#### CLM Runner & Test Infrastructure
- **Unified Python CLI (`scripts/run_clms.py`)**: Single script to run all CLMs, by directory, or individual files with optional `--context` JSON injection.
- **Fast Test Mode**: Added `@pytest.mark.slow` to Lean-dependent tests; run fast tests with `uv run pytest -m "not slow"` (~20s vs 2+ minutes).
- **Params Interpolation**: Fixed `balanced.test_cases` to properly preserve `when.params` for `${params.xxx}` variable substitution in config.
- **Recursive Interpolation**: Added `_interpolate_recursive()` to NetworkRuntime for nested batch operation configs.

#### Runtime Fixes
- **Unified Execution**: Python and JavaScript runtimes now execute the same set of CLMs with parity in path resolution, context passing, and builtin handling.
- **Python Context Passing**: Fixed `_prepare_argument` to pass context with `operation`/`params` keys to entry point functions—resolves complex arithmetic test failures.
- **JavaScript Path Resolution**: Fixed relative path execution issues in `CLMRunner`; CLMs now correctly resolve recursive calls and legacy formats regardless of execution context.
- **Collection Loader**: Enabled `collection_loader` runtime in JavaScript (`CollectionLoaderRuntime`) and verified with integration tests.
- **Builtin Test Cases**: Builtins (network runtime) now correctly execute `balanced.test_cases` instead of bypassing them.
- **Orchestrator Input Override**: CLMs called via orchestrator with explicit inputs (e.g., `signaling_url`) now skip default test cases.

#### Chapter-Specific Fixes
- **chapter_01_arithmetic**: All 27 CLMs passing across Python and JS runtimes.
- **chapter_07_network**: Fixed `http_fetch.yaml` to use `runtime: network`, enabling cross-platform HTTP execution.
- **chapter_08_P2P**: 13 CLMs passing, 3 skipped (Node.js-only marked as VCard).
  - WebRTC CLMs use `mock://p2p` for standalone testing.
  - Orchestrator overrides `signaling_url` for real connections.
  - Converted `persistence_simulation` and `long_session_simulation` from JavaScript to Python for better stability.

### Previous Updates

#### CLM Test Infrastructure Improvements
- **Execution Timing**: Added timing logs to `run-all-clms.ts` to identify slow CLMs.
- **Floating-Point Tolerance**: Numeric comparisons now use configurable tolerance (1e-6) for floating-point precision.
- **Input Context Handling**: Introduced `__input_content__` key to preserve original `given` values when merging `when` blocks.

#### Runtime Fixes (Prior Sessions)
- **JavaScript Runtime**: Changed `runtime: node` to `runtime: javascript` across CLMs; updated code to use `target` variable.
- **Python Input Parsing**: All Python implementations now handle `bytes`, `str`, and `dict` inputs with robust parsing.
- **Lambda Calculus**: Fixed parser to correctly handle parenthesized applications like `(\\x.x) y`.
- **Orchestrator**: Fixed `run_clm_background` to strip file extensions for proper filter matching.

#### Chapter-Specific Fixes (Prior Sessions)
- **chapter_03_llm**: Replaced LLM-dependent logic with mock implementations for test stability.
- **chapter_05_reflection**: Fixed meta-interpreter and module syntax CLMs.
- **chapter_06_lambda**: Fixed beta reduction and Church numerals parsers.

---

## Testing

> **Note:** All commands below should be run from the project root (`MCard_TDD/`).

### Unit Tests

```bash
# Python
uv run pytest -q                 # Run all tests
uv run pytest -q -m "not slow"   # Fast tests only
uv run pytest -m "not network"   # Skip LLM/Ollama tests

# JavaScript
npm --prefix mcard-js test -- --run
```

### CLM Verification

Both Python and JavaScript CLM runners support three modes: **all**, **directory**, and **single file**.

#### Python

```bash
# Run all CLMs
uv run python scripts/run_clms.py

# Run by directory
uv run python scripts/run_clms.py chapters/chapter_01_arithmetic
uv run python scripts/run_clms.py chapters/chapter_08_P2P

# Run single file
uv run python scripts/run_clms.py chapters/chapter_01_arithmetic/addition.yaml

# Run with custom context
uv run python scripts/run_clms.py chapters/chapter_08_P2P/generic_session.yaml \
    --context '{"sessionId": "my-session"}'
```

#### JavaScript

```bash
# Run all CLMs
npm --prefix mcard-js run clm:all

# Run by directory/filter
npm --prefix mcard-js run clm:all -- chapter_01_arithmetic
npm --prefix mcard-js run clm:all -- chapters/chapter_08_P2P

# Run single file
npm --prefix mcard-js run demo:clm -- chapters/chapter_01_arithmetic/addition_js.yaml
```

### Chapter Directories

| Directory | Description |
|-----------|-------------|
| `chapter_00_prologue` | Lambda calculus and Church encoding — 5 CLMs |
| `chapter_01_arithmetic` | Arithmetic operations (Python, JS, Lean) — 27 CLMs |
| `chapter_03_llm` | LLM integration (requires Ollama) |
| `chapter_04_load_dir` | Filesystem and collection loading |
| `chapter_05_reflection` | Meta-programming and recursive CLMs |
| `chapter_06_lambda` | Lambda calculus runtime |
| `chapter_07_network` | HTTP requests, MCard sync, network I/O — 5 CLMs |
| `chapter_08_P2P` | P2P networking and WebRTC — 16 CLMs (3 VCard) |
| `chapter_09_DSL` | Meta-circular language definition and combinators — 10 CLMs |

---

## Contributing
1. Fork the repository and create a feature branch.
2. Run the tests (`uv run pytest`, `npm test` in `mcard-js`).
3. Submit a pull request describing your change and tests.

We follow the BMAD (Red/Green/Refactor) loop – see [BMAD_GUIDE.md](BMAD_GUIDE.md).

---

## Future Roadmap

### Road to VCard (Design & Implementation)

Based on the **MVP Cards Design Rationale**, a VCard (Value Card) represents a boundary-enforced value exchange unit that often contains sensitive privacy data (identities, private keys, financial claims). Unlike standard MCards which are designed for public distribution and reproducibility, VCards require strict confidentiality.

**Design Requirements & Rationale:**
1.  **Privacy & Encryption**: VCards cannot be stored in the standard `mcard.db` (which is often shared or public) without encryption. They must be stored in a "physically separate" container or be encrypted at rest.
2.  **Authentication Primitive**: A VCard serves as a specialized "Certificate of Authority" — a precondition for executing sensitive PTR actions.
3.  **Audit Certificates**: Execution of a VCard-authorized action must produce a **VerificationVCard** (Certificate of Execution), which proves the action occurred under authorization. This certificate is also sensitive.
4.  **Unified Schema**: While the storage *location* differs, the *data schema* should remain identical to MCard (content addressable, hash-linked) to reuse the rigorous polynomial logic.

**Proposed Architecture:**
*   **Dual-Database Storage**:
    *   `mcard.db` (Public/Shared): Stores standard MCards, Logic (PCards), and Public Keys.
    *   `vcard.db` (Private/Local): Stores VCards, Encrypted Private Keys, and Verification Certificates.
*   **Execution Flow**:
    `execute(pcard_hash, input, vcard_authorization_hash)`
    1.  **Gatekeeper**: PTR checks if `vcard_authorization_hash` exists in the Private Store (`vcard.db`).
    2.  **Zero-Trust Verify**: Runtime validates the VCard's cryptographic integrity and permissions (Security Polynomial).
    3.  **Execute**: If valid, the PCard logic runs.
    4.  **Certify**: A new `VerificationVCard` is generated, signed, and stored in `vcard.db`, linking the Input, Output, and Authority.

**TODOs:**
- [ ] **Infrastructure**: Implement `PrivateCollection` (wrapper around `vcard.db`) in Python and JavaScript factories.
- [ ] **Encryption Middleware**: Add a transparent encryption layer (e.g., AES-GCM) for the Private Collection to ensure Encryption-at-Rest.
- [ ] **CLI Auth**: Update `run_clms.py` to accept `--auth <vcard_hash>` and mount the private keystore.
- [ ] **Certificate Generation**: Implement the `VerificationVCard` schema and generation logic in `CLMRunner`.

---

### Logical Model Certification & Functional Deployment

Use of the **Cubical Logic Model (CLM)** as a "Qualified Logical Model" is strictly governed by principles derived from Eelco Dolstra's *The Purely Functional Software Deployment Model* (the theoretical basis of Nix).

A CLM is not merely source code; it is a candidate for certification. It only becomes a **Qualified Logical Model** when it possesses a valid **Certification**, which is a cryptographic proof of successful execution by a specific version of the Polynomial Type Runtime (PTR).

**The Functional Certification Equation:**
$$
Observation = PTR_{vX.Y.Z}(CLM_{Source})
$$
$$
Certification = Sign_{Authority}(Hash(CLM_{Source}) + Hash(PTR_{vX.Y.Z}) + Hash(Observation))
$$

**Parallels to the Nix Model:**
1.  **Hermetic Inputs**: Just as a Nix derivation hashes all inputs (compiler, libs, source), a CLM Certification depends on the exact **PTR Runtime Version** and **CLM Content Hash**. Changing the runtime version invalidates the certificate, requiring re-qualification (re-execution).
2.  **Deterministic Derivation**: The "build" step is the execution of the CLM's verification logic. If the PTR (the builder) is deterministic, the output (VerificationVCard) is reproducible.
3.  **The "Store"**: The `mcard.db` acts as the Nix Store, holding immutable, content-addressed CLMs. The `vcard.db` acts as the binary cache, holding signed Certifications (outputs) that prove a CLM works for a given runtime configuration.

This ensures that a "Qualified CLM" is not just "code that looks right," but **"code that has logically proven itself"** within a specific, physically identifiable execution environment.

---

## License
This project is licensed under the MIT License – see [LICENSE](LICENSE).

For release notes, check [CHANGELOG.md](CHANGELOG.md).
