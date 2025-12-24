import math
import gurobipy as gp
import numpy as np
import sympy
from gurobipy import GRB
from pyeuclid.formalization.relation import *
from pyeuclid.formalization.utils import *
from pyeuclid.engine.inference_rule import *


class ProofGenerator:
    def __init__(self, state):
        self.state = state
        self.proof = ""
    
    def show_proof(self):
        print(self.proof)
    
    def traceback(self, augmented_A, e) -> list[str]:
        m, n = augmented_A.shape
        e = e[0]
        n = n-1

        model = gp.Model()
        model.setParam('OutputFlag', 0)

        x = model.addVars(m, lb=-GRB.INFINITY, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS, name="x")
        z = model.addVars(m, vtype=GRB.BINARY, name="z")

        model.setObjective(gp.quicksum(z[i] for i in range(m)), GRB.MINIMIZE)

        for i in range(n + 1):
            model.addConstr(gp.quicksum(augmented_A[j, i] * x[j] for j in range(m)) == e[i])

        M = 1e6
        for i in range(m):
            model.addConstr(x[i] <= M * z[i])
            model.addConstr(x[i] >= -M * z[i])

        model.optimize()

        assert model.status == GRB.OPTIMAL        
        return [i for i in range(m) if z[i].x > 0]
    
    def vectorize(self, equations, variables, source):
        A = np.zeros(shape=(len(equations), len(variables)), dtype=np.float64)
        b = np.zeros(shape=(len(equations), 1), dtype=np.float64)
        if source in ("angle_linear", "length_linear"):
            for i, eqn in enumerate(equations):
                eqn = sympy.expand(eqn)
                assert isinstance(eqn, sympy.core.add.Add) or isinstance(eqn, sympy.core.symbol.Symbol)

                for add_arg in eqn.args:
                    if len(add_arg.args) == 0:
                        mul_args = [add_arg]
                    else:
                        assert isinstance(add_arg, sympy.core.mul.Mul)
                        mul_args = add_arg.args
                    factors = [item for item in mul_args if len(
                        item.free_symbols) == 0]
                    factor = sympy.core.mul.Mul(*factors)
                    symbols = [item for item in mul_args if len(
                        item.free_symbols) > 0]
                    if len(symbols) == 0:
                        b[i, 0] = factor.evalf()
                    else:
                        A[i, variables[symbols[0]]] = factor.evalf()
        else:
            assert source == "length_ratio"  # length=const or eqlength or eqlength ratio or lengthratio=const
            for i, eqn in enumerate(equations):
                if isinstance(eqn, sympy.core.add.Add):
                    if len(eqn.args) > 2:
                        breakpoint()
                        assert False
                    add_args = eqn.args
                else:
                    add_args = [eqn]
                for j, add_arg in enumerate(add_args):
                    if len(add_arg.args) > 0:
                        mul_args = add_arg.args
                    else:
                        mul_args = [add_arg]
                    for mul_arg in mul_args:
                        factor = (-1)**(j)
                        if isinstance(mul_arg, sympy.core.power.Pow):
                            factor *= mul_arg.args[1]
                            mul_arg = mul_arg.args[0]
                        if len(mul_arg.free_symbols) == 0:
                            b[i, 0] += factor * math.log(abs(mul_arg))
                        else:
                            symbol = list(mul_arg.free_symbols)[0]
                            A[i, variables[symbol]] += factor
        return np.concat([A, b], axis=1)


    def find_conditions(self, equations: list[Traced], conclusion, source):
        angle_linear, length_linear, length_ratio, others = classify_equations(equations, self.state.var_types)
        """Given sympified equations and conclusions, return a list of necessary conditions"""
        def try_find(equations, conclusion):
            variables = set()
            for eqn in equations:
                variables = variables.union(eqn.free_symbols)
            variables = {item: i for i, item in enumerate(list(variables))}
            mat = self.vectorize([item.expr for item in equations], variables, source)
            eq = self.vectorize([conclusion], variables, source)
            deps = self.traceback(mat, eq)
            return [equations[i] for i in deps]
        if source == "angle_linear":
            equations = angle_linear
        elif source == "length_linear":
            equations = length_linear
        else:
            assert source == "length_ratio"
            equations = length_ratio
        return try_find(equations, conclusion)
    
    def run(self, node, visited=set([]), depth=None, verbose=False, root=True):
        if root:
            depth = self.state.current_depth
            visited = set([])
        elif depth is None:
            depth = node.depth
        # self.logger.debug(f"{node}@{depth}: {getattr(node, 'sources', None)}")
        def format_proof(proof_dict, conclusion):
            proof_steps = {}
            visited = set()
            step_counter = 1

            def format_conditions(condition, proof_steps, theorem):
                s = []
                for condition in conditions:
                    if condition in proof_steps:
                        s.append(f"{condition}({proof_steps[condition][0]})")
                    else:
                        s.append(f"{condition}")
                if theorem is None:
                    return " &\n".join(s)
                return " &\n".join(s) + f"({theorem})"
            def search(node):  # root-last traversal
                nonlocal step_counter
                if node in visited or node not in proof_dict or proof_dict[node] is None:
                    return
                visited.add(node)
                conditions = proof_dict[node]
                theorem = None
                while len(conditions) == 1 and conditions[0] in proof_dict: # collapse single-condition inferences
                    if isinstance(conditions[0], InferenceRule) and not type(conditions[0]) in inference_rule_sets["ex"]:
                        theorem = conditions[0]
                    conditions = proof_dict[conditions[0]]
                for condition in conditions:
                    if condition is not None:
                        search(condition)
                if all([type(item) in (Collinear, Between, SameSide)for item in conditions]):
                    return
                if type(node) in (Traced, sympy.core.add.Add):
                    for item in visited:
                        if not item is node and type(item) in (Traced, sympy.core.add.Add):
                            if getattr(node, "expr", node) - getattr(item, "expr", item) == 0:
                                return
                            if getattr(node, "expr", node) + getattr(item, "expr", item) == 0:
                                return
                proof_steps[node] = (step_counter, conditions, theorem)
                step_counter += 1
            search(conclusion)
            self.proof += "* Proof steps:\n"
            lst = [(key, value) for key, value in proof_steps.items()]
            lst.sort(key=lambda x: x[1][0])
            last = -1
            for node, (step_number, conditions, theorem) in lst:
                if step_number == last:
                    continue
                last = step_number
                self.proof += f"{step_number:03}. {format_conditions(node, proof_steps, theorem)} ⇒ {node}\n"
        if node in visited:
            return {}
        if isinstance(node, InferenceRule):
            visited.add(node)
            conds = [item for item in node.condition() if type(item)
                     not in (Equal, Lt) and not item == 0]
            result = {}
            result[node] = conds
            for cond in conds:
                result.update(self.run(cond, visited, depth=depth-1, root=False))
        elif isinstance(node, Relation):
            visited.add(node)
            if type(node) in (Between, SameSide, Lt, Equal) or type(node) == Collinear and (node.p1 == node.p2 or node.p2 == node.p3 or node.p3 == node.p1):
                return {}
            if hasattr(node, "definition"):
                defs = node.definition()
                result = {node: defs}
                for cond in defs:
                    result.update(self.run(cond, visited, depth=depth, root=False))
                return result
            result = {}
            for tmp in self.state.relations:
                if tmp == node:
                    if hasattr(tmp, "source"):
                        source = tmp.source
                        result = {node: [source]}
                        result.update(self.run(source, visited, root=False))
                    else:
                        result = {node: []}
                    break
            assert len(result) > 0, f"{node} is not proved"
        else:
            if isinstance(node, Traced):
                sources = node.sources
                if len(sources) == 0: # initial conditions
                    visited.add(node)
                elif isinstance(sources[0], str):
                    # backtrace linear systems
                    equations = [item for item in self.state.equations if item.depth <= node.depth]
                    if not node.symbol is None:
                        expr = node.symbol - node.expr
                    else:
                        expr = node.expr
                    conditions = self.find_conditions(equations, expr, sources[0])
                    if not conditions:
                        breakpoint()
                        assert False
                    sources = conditions
                else:
                    visited.add(node)
            else:
                assert isinstance(node, sympy.core.expr.Expr)
                sources = []
                solved_vars = self.state.solutions[min(int(depth), len(self.state.solutions)-1)]
                for symbol in node.free_symbols:
                    if not symbol in solved_vars:
                        continue  # free vars
                    expr = symbol-solved_vars[symbol].expr
                    expr = Traced(expr, sources=solved_vars[symbol].sources, depth=int(depth))
                    sources.append(expr)
                if isinstance(node, sympy.core.symbol.Symbol):
                    node = node - solved_vars[node].expr
            result = {node: sources}
            for item in sources:
                result.update(self.run(item, visited, root=False))
        if root:
            format_proof(result, node)
        return result
    
    def generate_proof(self):
        self.run(self.state.goal)