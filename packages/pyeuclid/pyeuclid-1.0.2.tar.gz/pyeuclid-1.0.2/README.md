# PyEuclid: A Versatile Formal Plane Geometry System in Python

PyEuclid is a formal plane geometry system that combines symbolic inference rules with algebraic reasoning to generate and check geometric proofs. Use it to experiment with benchmark datasets, extend inference rules, or integrate interactive proof steps for human/LLM collaboration.

<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="docs/images/pyeuclid-architecture.png" alt="PyEuclid architecture diagram" width="900"/>
</p>
<!-- markdownlint-enable MD033 -->

Documentation: <https://kellyjdavis.github.io/PyEuclid/>

## Quick Start (PyPI)

1. Install from PyPI

```bash
pip install pyeuclid
```

2. Verify your install

```bash
python - <<'PY'
import sympy as sp
from pyeuclid.formalization.relation import Point, Length, Variable

print("PyEuclid version:", __import__("pyeuclid").__version__)

# Mini example inspired by Geometry3K/2820
pi = sp.pi
conditions = [
    Length(Point("A"), Point("B")) - sp.Integer(4),
    Length(Point("A"), Point("B")) - Variable("radius_A"),
]
goal = (pi * Variable("radius_A")) * Variable("radius_A")

print("Conditions:", conditions)
print("Goal:", goal)
PY
```

## Developer Setup (from source)

Use this path if you need the benchmark datasets, cached diagrams, or want to extend PyEuclid.

Install from source:

```bash
git clone https://github.com/KellyJDavis/PyEuclid.git
cd PyEuclid
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install .
tar -xvzf cache.tar.gz
```

Project layout:

```text
.
├── cache/                                # Cached diagrams sampled from JGEX-AG-231
├── data/                                 # Benchmark datasets (JGEX-AG-231, Geometry3K)
├── pyeuclid/
│   ├── engine/                           # Core reasoning components: inference rules, deductive database, algebraic system, proof generator
│   └── formalization/                    # Problem formalization: relations, construction rules, state management, diagram handling
├── Dockerfile                            # Docker configuration for containerized setup
├── requirements.txt                      # List of required Python packages
├── setup.py                              # Setup script to build and install PyEuclid
└── test.py                               # Run experiments on test datasets
```

After installation, verify everything works:

```bash
python test_single.py --help
python test_single.py --show-proof
```

Docker (optional for dev parity):

You can either build the Docker image locally or pull it from Docker Hub:

```bash
# Build the Docker image locally
docker build -t pyeuclid .
# Alternatively, pull the image from Docker Hub
docker pull dahubao/pyeuclid
# After obtaining the image, run
docker run -it pyeuclid bash
```

Note: PyEuclid uses Gurobi as a component of its proof generator. To solve more complex problems, you may need a [Gurobi academic license](https://www.gurobi.com/academia/academic-program-and-licenses/), as the free version has a limit of 2000 variables and constraints.

## Evaluation

We provide both sequential and parallel methods to run experiments on the JGEX-AG-231 and Geometry3K datasets:

```bash
python test.py                            # Run sequentially on a single machine
sbatch slurm.sh                           # Run in parallel on a compute cluster via SLURM
```

## Extension

If you would like to improve the reasoning ability of PyEuclid, one straightforward way is to add more complex inference rule at `pyeuclid/engine/inference_rule.py`. Here is an example:

```python
@register('complex')
class AreaHeronFormula(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c

    def condition(self):
        return [NotCollinear(self.a, self.b, self.c), Different(self.a, self.b, self.c), Lt(self.a, self.b), Lt(self.b, self.c)]

    def conclusion(self):
        s = (Length(self.a, self.b)+Length(self.a, self.c)+Length(self.b, self.c))/2
        return [Area(self.a, self.b, self.c)**2-(s*(s-Length(self.a, self.b))*(s-Length(self.a, self.c))*(s-Length(self.b, self.c)))]
```

You need to specify the condition and conclusion of the inference rule. The Lt relation defines a partial order on the names of the points to reduce equivalent permutations of the inference rule.

We also provide an interactive interface that allows PyEuclid to collaborate with a human user or a Large-Language-Model (LLM) agent.
You can explicitly trigger a reasoning step by calling:

```python
engine.step(conditions, conclusions)
```

PyEuclid will verify both the conditions and the desired conclusions, and automatically apply the appropriate theorems or algebraic equations to derive the conclusions from the given conditions.

## License

PyEuclid is licensed under the MIT License.
