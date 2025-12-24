# co2e (Carbon Ops Guardrails placeholder)

This repository now publishes a minimal ``co2e`` package to reserve the PyPI name for the future Carbon Ops Guardrails distribution. The placeholder release ships lightweight scaffolding only; real functionality will arrive in later versions.

## What you can expect
- **Signed telemetry ledger** – every emission estimate will be ed25519 signed and anchored via Merkle proofs.
- **Energy-to-carbon estimation** – ingestion jobs will convert runtime metrics into kWh and CO₂e using grid intensity APIs.
- **Evidence exports** – repeatable audit packages with inclusion proofs and configuration snapshots.

## Repository layout
```
carbon-ops/
├── README.md
├── pyproject.toml
├── src/
│   └── carbon_ops/
│       ├── __init__.py
│       ├── config.py
│       ├── ledger.py
│       └── pipeline.py
└── tests/
    └── test_placeholder.py
```

## Quick start
1. Create and activate a Python 3.11 virtual environment.
2. Install the package in editable mode: `pip install -e ".[dev]"`.
3. Run the placeholder tests: `pytest`.

## Next steps
- Implement telemetry ingestion adapters for Vertex AI job logs.
- Flesh out the ledger module with ed25519 signing and Merkle tree anchoring.
- Integrate grid intensity providers (e.g., WattTime) and unit tests around estimation logic.

## Licensing
Choose an open-source license before publishing a production-ready release (MIT, Apache-2.0, or BUSL-1.1 are all viable depending on release strategy).
