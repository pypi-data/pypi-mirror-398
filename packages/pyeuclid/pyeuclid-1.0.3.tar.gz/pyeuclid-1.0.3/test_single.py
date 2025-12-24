import time
from sympy import sympify
import sympy
import logging
from stopit import ThreadingTimeout as Timeout
import argparse

from pyeuclid.formalization.state import State
from pyeuclid.formalization.relation import *
from pyeuclid.engine.inference_rule import inference_rule_sets
from pyeuclid.engine.deductive_database import DeductiveDatabase
from pyeuclid.engine.algebraic_system import AlgebraicSystem
from pyeuclid.engine.proof_generator import ProofGenerator
from pyeuclid.engine.engine import Engine

parser = argparse.ArgumentParser()
parser.add_argument('--problem-id', type=int, default=2455)
parser.add_argument('--problem-string', type=str, default=None)   
parser.add_argument('--show-proof', action='store_true')

def run_single_problem(args):
    state = State()
    state.logger.setLevel(logging.INFO)
    if args.problem_string is not None:
        state.load_problem_from_text(args.problem_string, f'diagrams/JGEX-AG-231/test.jpg')
    else:
        namespace = {}
        with open(f'data/Geometry3K/{args.problem_id}/problem.py', "r") as file:
            exec(file.read(), namespace)
        conditions = namespace.get("conditions")
        goal = namespace.get("goal")
        solution = namespace.get("solution")
        diagrammatic_relations = namespace.get("diagrammatic_relations")
        state.try_complex = True
        state.load_problem(conditions=conditions, goal=goal)
        state.add_relations(diagrammatic_relations)
    deductive_database = DeductiveDatabase(state, outer_theorems=inference_rule_sets['basic'] + inference_rule_sets['complex'])
    algebraic_system = AlgebraicSystem(state)
    proof_generator = ProofGenerator(state)
    engine = Engine(state, deductive_database, algebraic_system)
    t0 = time.time()
    try:
        with Timeout(600):
            engine.search()
    except:
        pass
    t = time.time() - t0
    result = state.complete()
    if result is not None:
        if args.show_proof:
            proof_generator.generate_proof()
            proof_generator.show_proof()
        print(f"Solved in {t:.2f}s")
    else:
        print(f"Not solved in {t:.2f}s")

if __name__ == '__main__':
    args = parser.parse_args()
    run_single_problem(args)
