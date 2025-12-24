# QuantumSDK

Python client SDK for interacting with the Volodymyr Quantum API. It provides a simple, typed interface for working with machines, qubits, couplers, file uploads, and common API workflows.

## Features
- Simple `Client` for authenticated requests with automatic token refresh
- High-level resource objects: `Machine`, `Qubit`, `Coupler`
- Convenient mapping access: `machine.qubits[<number>]`, `machine.couplers[<number>]`
- File APIs: upload, list, and open files
- Consistent error handling via `QuantumSDKError`

## Requirements
- Python >= 3.13 (as configured in `pyproject.toml`)
- Dependencies are installed automatically (notably `requests`)

## Installation

Once published to PyPI or TestPyPI:

```bash
pip install quantumsdk
```

Install from TestPyPI (example):

## Check the examples