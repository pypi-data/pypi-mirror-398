# PyEuclid

[![Release](https://img.shields.io/github/v/release/KellyJDavis/PyEuclid)](https://github.com/KellyJDavis/PyEuclid/releases)
[![Build status](https://img.shields.io/github/actions/workflow/status/KellyJDavis/PyEuclid/main.yml?branch=main)](https://github.com/KellyJDavis/PyEuclid/actions/workflows/main.yml?query=branch%3Amain)
[![License](https://img.shields.io/github/license/KellyJDavis/PyEuclid)](https://github.com/KellyJDavis/PyEuclid/blob/main/LICENSE)

> *A versatile formal plane geometry system in Python*

PyEuclid provides reasoning, deduction, and proof generation over plane geometry problems. It is derived from the upstream project by Zhaoyu Li and maintained here by Kelly J Davis.

For full source and issues, see the [repository](https://github.com/KellyJDavis/PyEuclid).

![Architecture](images/pyeuclid-architecture.png)

## Installation

```bash
pip install pyeuclid
```

Datasets (`data/`) and cached artifacts (`cache/`, `cache.tar.gz`) are **not** bundled with the PyPI package. Install from source if you need the benchmark data for experiments.

## Quickstart

Minimal example to load a geometry problem and attempt a proof:

```python
from pyeuclid.formalization.state import State
from pyeuclid.formalization.relation import NotCollinear, Between
from pyeuclid.engine.inference_rule import inference_rule_sets
from pyeuclid.engine.deductive_database import DeductiveDatabase
from pyeuclid.engine.algebraic_system import AlgebraicSystem
from pyeuclid.engine.proof_generator import ProofGenerator
from pyeuclid.engine.engine import Engine

# Define a tiny synthetic problem
state = State()
state.load_problem(
    conditions=[NotCollinear("A", "B", "C"), Between("A", "B", "C")],
    goal=None,
)

deductive_database = DeductiveDatabase(state, outer_theorems=inference_rule_sets["basic"])
algebraic_system = AlgebraicSystem(state)
proof_generator = ProofGenerator(state)
engine = Engine(state, deductive_database, algebraic_system)

engine.search()
if state.complete():
    proof_generator.generate_proof()
    proof_generator.show_proof()
else:
    print("No proof found in this quick example.")
```

## Publishing

See [PUBLISHING.md](https://github.com/KellyJDavis/PyEuclid/blob/main/PUBLISHING.md) for tagging and automated PyPI release instructions. Docs are published via GitHub Pages from the `gh-pages` branch.

## License

MIT License. See [LICENSE](https://github.com/KellyJDavis/PyEuclid/blob/main/LICENSE).

