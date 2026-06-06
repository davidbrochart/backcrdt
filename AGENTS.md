# AGENTS.md

## Setup commands
- In the `src` directory, the only file you are allowed to change is `src/lib_backcrdt.rs`.
- After every modification of `src/lib_backcrdt.rs`, rebuild the Rust library with: `cat src/lib_backcrdt.rs src/lib_original.rs > /tmp/lib.rs && mv /tmp/lib.rs src/ && maturin develop`.
- Run tests: `pytest -v`.
