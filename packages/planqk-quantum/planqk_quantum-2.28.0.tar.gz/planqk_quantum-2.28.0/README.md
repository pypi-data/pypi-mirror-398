# PLANQK Quantum SDK

[![PyPI version](https://badge.fury.io/py/planqk-quantum.svg)](https://badge.fury.io/py/planqk-quantum)

The PLANQK Quantum SDK is for developing quantum circuits using [Qiskit](https://pypi.org/project/qiskit) to be run on
quantum devices provided by the [PLANQK Platform](https://docs.planqk.de).
This library is an **extension** for Qiskit.
This means that you are able to seamlessly integrate and reuse your existing Qiskit code, leveraging the power and
familiarity of a framework you are already accustomed to.

## Getting Started

Check out the following guides on how to get started with PLANQK:

- [PLANQK Quickstart Guide](https://docs.planqk.de/quickstart.html)
- [Using the PLANQK Quantum SDK](https://docs.planqk.de/using-sdk.html)

## Installation

The package is released on PyPI and can be installed via `pip`:

```bash
pip install --upgrade planqk-quantum
```

To install a pre-release version, use the following command:

```bash
pip install --pre --upgrade planqk-quantum
```

## Usage

### Working with Qiskit Backends

You can execute a Qiskit circuit on a selected backend, retrieve its job object, and its results:

```python
from planqk.quantum.sdk import PlanqkQuantumProvider
from qiskit import QuantumCircuit, transpile

# Initialize the provider
provider = PlanqkQuantumProvider()

# Select a backend, full list of backends can be found at https://platform.planqk.de/quantum-backends
backend = provider.get_backend("azure.ionq.simulator")

# Create a Qiskit circuit
circuit = QuantumCircuit(3, 3)
circuit.h(0)
circuit.cx(0, 1)
circuit.cx(1, 2)
circuit.measure(range(3), range(3))

# Transpile the circuit for the selected backend
circuit = transpile(circuit, backend)

# Execute the circuit on the selected backend
job = backend.run(circuit, shots=100)

# Monitor job status and get results
print(f"Status: {job.status()}")
print(f"Result: {job.result()}")
```

### Working with Braket Devices

You can execute a Braket circuit on a selected device, retrieve its task object, and its results:

```python
from braket.circuits import Circuit
from planqk.quantum.sdk import PlanqkBraketProvider

# Select the IonQ Forte device
device = PlanqkBraketProvider().get_device("aws.ionq.forte")

# Create a Braket circuit
circuit = Circuit().h(0).cnot(0, 1).cnot(1, 2)

# Execute the circuit with 100 shots
task = device.run(circuit, 100)

# Monitor task status and get results
print(f"Status: {task.state()}")
print(f"Result: {task.result()}")
```

## Development

To create a new virtual environment, for example, run:

```bash
uv venv
uv sync
```

Then, to activate the environment:

```bash
source .venv/bin/activate
```

Update dependencies and lock files:

```bash
uv sync -U
```
