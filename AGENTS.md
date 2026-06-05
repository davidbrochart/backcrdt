# AGENTS.md

## Setup commands
- Don't change `src/lib.rs` because this file is auto-generated. Instead, change `src/lib_backcrdt.rs` (but not `src/lib_original.rs`).
- After every modification of the Rust code: `cat src/lib_backcrdt.rs src/lib_original.rs > /tmp/lib.rs && mv /tmp/lib.rs src/ && maturin develop`.
- Run tests: `pytest -v`.
