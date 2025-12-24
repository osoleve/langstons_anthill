# The Quest Board 📜

Herein lies the work that needs doing. Claim a quest by commenting on the relevant issue or opening a PR referencing the quest title.

### Initiate the Iron Bindings

**Tier:** 🥇 Gold
**Posted:** 2025-12-24
**Expires:** 2026-02-24
**Source:** The Ceryneian Hind, visit of 2025-12-24

**The Task:**
The Ceryneian Hind has marked the path for the Great Unification. The Python shell must bind to the Rust core. The first step is configuration.

Set up the `maturin` build system and create the initial PyO3 bindings for the configuration structures found in `anthill-core`. Do not attempt to bind the entire engine yet.

1. Enable the `pyo3` dependency in `anthill-core/Cargo.toml`.
2. Configure `pyproject.toml` (or equivalent) for `maturin`.
3. Create a basic `lib.rs` Python module definition.
4. Verify that `maturin develop` builds the extension.

**Location:**
`anthill-core/Cargo.toml`
`anthill-core/src/lib.rs`

**Guild Interest:**
The Order of the Eternal Refactor sees this as the ultimate form of their craft. The Council of Long-Term Thinking has been waiting for this moment since the First Amendment was written.

**Claim:**
Open a PR referencing "Quest: Iron Bindings - Config".
