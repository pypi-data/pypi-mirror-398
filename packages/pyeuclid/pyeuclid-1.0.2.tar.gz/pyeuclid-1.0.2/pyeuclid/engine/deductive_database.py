"""Deductive database for geometric inference rules.

Matches registered inference rules against the current `State`, instantiates
them with concrete points, and applies resulting conclusions. Uses a Z3 encoding
to search admissible assignments while preserving canonical point orderings via
`Lt` constraints.
"""

import z3
import math
            
from z3 import Solver, BitVec, BitVecVal, ULT, And, Or
from tqdm import tqdm

from pyeuclid.formalization.state import *
from pyeuclid.engine.inference_rule import *


class DeductiveDatabase:
    """Match and apply geometric inference rules against a state."""

    def __init__(self, state, inner_theorems=inference_rule_sets["ex"], outer_theorems=inference_rule_sets["basic"]):
        """Initialize a deductive database.

        Args:
            state (State): Shared state being reasoned over.
            inner_theorems (Iterable[type[InferenceRule]]): Higher-priority rules applied exhaustively first.
            outer_theorems (Iterable[type[InferenceRule]]): Secondary rules applied after inner closure.
        """
        self.state = state
        self.inner_theorems = inner_theorems
        self.outer_theorems = outer_theorems
        self.closure = False
        
    def get_applicable_theorems(self, theorems):
        """Instantiate and return all applicable rules from the given set.

        Returns:
            list[InferenceRule]: Concrete rule instances whose conditions are satisfiable in the current state.
        """
        def search_assignments(theorem):
            if not theorem in self.state.solvers:
                self.state.solvers[theorem] = Solver()
            solver = self.state.solvers[theorem]
            solver.push()
            slots = theorem.__init__.__annotations__
            formal_entities = {}
            for key, attr_type in slots.items():
                if isinstance(attr_type, str):
                    assert attr_type == 'Point'
                else:
                    assert attr_type.__name__ == "Point"
                formal_entities[key] = Point(key)
            example = theorem(**formal_entities)
            formal_conditions = example.condition()
            
            nbits = math.ceil(math.log2(len(self.state.points)))
            point_encoding = {}
            point_decoding = {}
            formal_points = {}
            points = list(self.state.points)
            points.sort(key=lambda x: x.name)
            for i, point in enumerate(points):
                point_encoding[point.name] = BitVecVal(i, nbits)
                point_decoding[BitVecVal(i, nbits)] = point
            for name in formal_entities:
                formal_points[name] = BitVec(name, nbits)
                if len(self.state.points) < 2**nbits:
                    solver.add(ULT(formal_points[name], len(self.state.points)))

            def in_component(formal, component):
                clause = False
                if len(formal) == 2:
                    for item in component:
                        actual, _ = get_points_and_symbols(item)
                        p1 = And(formal_points[formal[0]] == point_encoding[actual[0]],
                                formal_points[formal[1]] == point_encoding[actual[1]])
                        p2 = And(formal_points[formal[0]] == point_encoding[actual[1]],
                                formal_points[formal[1]] == point_encoding[actual[0]])
                        clause = Or(clause, Or(p1, p2))
                elif len(formal) == 3:
                    for item in component:
                        actual, _ = get_points_and_symbols(item)
                        p1 = And(formal_points[formal[0]] == point_encoding[actual[0]], formal_points[formal[1]]
                                == point_encoding[actual[1]], formal_points[formal[2]] == point_encoding[actual[2]])
                        p2 = And(formal_points[formal[0]] == point_encoding[actual[2]], formal_points[formal[1]]
                                == point_encoding[actual[1]], formal_points[formal[2]] == point_encoding[actual[0]])
                        clause = Or(clause, Or(p1, p2))
                else:
                    assert False
                return clause

            for cond in formal_conditions:
                clause = False
                if isinstance(cond, Relation):
                    formal = cond.get_points()
                else:
                    formal, _ = get_points_and_symbols(cond)
                if isinstance(cond, Relation):
                    if isinstance(cond, Equal):
                        clause = formal_points[cond.v1.name] == formal_points[cond.v2.name]
                        if cond.negated:
                            clause = z3.Not(clause)
                    elif isinstance(cond, Lt):
                        clause = ULT(
                            formal_points[cond.v1.name], formal_points[cond.v2.name])
                    else:
                        assert type(cond) in (
                            Collinear, SameSide, Between, Perpendicular, Concyclic, Parallel)
                        if type(cond) == Between:
                            clauses = []
                            for rel in self.state.relations:
                                if type(rel) == type(cond):
                                    assert not rel.negated
                                    permutations = rel.permutations()
                                    for perm in permutations:
                                        assignment = True
                                        for i in range(len(formal)):
                                            assignment = And(
                                                formal_points[formal[i]] == point_encoding[perm[i]], assignment)
                                        clauses.append(assignment)
                            clause = Or(*clauses)
                            if cond.negated:  # we have all between relations, and never store negated between relations
                                clause = z3.Not(clause)
                        else:
                            for rel in self.state.relations:
                                if type(rel) == type(cond) and rel.negated == cond.negated:
                                    if hasattr(rel, "permutations"):
                                        permutations = rel.permutations()
                                    else:
                                        permutations = [
                                            re.pattern.findall(str(rel))]
                                    for perm in permutations:
                                        if not isinstance(perm[0], str):
                                            perm = [item.name for item in perm]
                                        partial_assignment = True
                                        for i in range(len(formal)):
                                            partial_assignment = And(
                                                formal_points[formal[i]] == point_encoding[perm[i]], partial_assignment)
                                        clause = Or(partial_assignment, clause)
                            if type(cond) == Collinear:
                                degenerate = Or(formal_points[formal[0]]==formal_points[formal[1]], formal_points[formal[1]]==formal_points[formal[2]], formal_points[formal[2]]==formal_points[formal[0]])
                                clause = Or(clause, degenerate)
                elif isinstance(cond, sympy.core.expr.Expr):
                    pattern_eqlength = re.compile(r"^-?Length\w+ [-\+] Length\w+$")
                    pattern_eqangle = re.compile(r"^-?Angle\w+ [-\+] Angle\w+$")
                    pattern_eqratio = re.compile(
                        r"^-?Length\w+/Length\w+ [\+-] Length\w+/Length\w+$")
                    pattern_angle_const = re.compile(
                        r"^-?Angle\w+ [-\+] [\w/\d]+$")
                    pattern_angle_sum = re.compile(
                        r"^-?Angle\w+ [-\+] Angle\w+ [-\+] [\w/\d]+$")
                    s = str(cond)
                    if pattern_eqlength.match(s):
                        points, _ = get_points_and_symbols(cond)
                        l, r = points[:2], points[2:]
                        for component in self.state.lengths.equivalence_classes().values():
                            clause = Or(clause, And(in_component(
                                l, component), in_component(r, component)))
                    elif pattern_eqangle.match(s):
                        points, _ = get_points_and_symbols(cond)
                        l, r = points[:3], points[3:]
                        for component in self.state.angles.equivalence_classes().values():
                            clause = Or(clause, And(in_component(
                                l, component), in_component(r, component)))
                    elif pattern_eqratio.match(s):
                        points, _ = get_points_and_symbols(cond)
                        a, b, c, d = points[:2], points[2:4], points[4:6], points[6:8]
                        for ratios in self.state.ratios.values():
                            l_clause = False
                            r_clause = False
                            for ratio in ratios:
                                _, symbols = get_points_and_symbols(ratio)
                                length1, length2 = symbols
                                length1, length2 = self.state.lengths.find(
                                    length1), self.state.lengths.find(length2)
                                component1, component2 = self.state.lengths.equivalence_classes(
                                )[length1], self.state.lengths.equivalence_classes()[length2]
                                l_clause = Or(l_clause, And(in_component(
                                    a, component1), in_component(b, component2)))
                                r_clause = Or(r_clause, And(in_component(
                                    c, component1), in_component(d, component2)))
                            clause = Or(clause, And(l_clause, r_clause))
                    elif pattern_angle_const.match(s):
                        points, _ = get_points_and_symbols(cond)
                        left = points[:3]
                        cnst = [arg for arg in cond.args if len(arg.free_symbols)==0][0]
                        cnst = abs(cnst)
                        for rep, component in self.state.angles.equivalence_classes().items():
                            if self.state.check_conditions(cnst - rep):
                                clause = in_component(left, component)
                                break
                    else:
                        assert pattern_angle_sum.match(s)
                        cnst = [arg for arg in cond.args if len(
                            arg.free_symbols) == 0][0]
                        cnst = abs(cnst)
                        points, _ = get_points_and_symbols(cond)
                        left, right = points[:3], points[3:]
                        for rep, angle_sums in self.state.angle_sums.items():
                            if self.state.check_conditions(cnst-rep):
                                for angle_sum in angle_sums:
                                    if isinstance(angle_sum, sympy.core.add.Add):
                                        angle1, angle2 = angle_sum.args
                                        # angle1 + angle2
                                    else:
                                        angle1 = list(angle_sum.free_symbols)[0]
                                        angle2 = angle1
                                        # 2 * angle_1
                                    angle1, angle2 = self.state.angles.find(angle1), self.state.angles.find(angle2)
                                    try:
                                        component1, component2 = self.state.angles.equivalence_classes(
                                        )[angle1], self.state.angles.equivalence_classes()[angle2]
                                    except:
                                        breakpoint()
                                        assert False
                                    clause = Or(clause, And(in_component(
                                        left, component1), in_component(right, component2)))
                                break
                solver.add(clause)
            solutions = []
            assignments = []
            while solver.check() == z3.sat:
                m = solver.model()
                dic = {str(i): point_decoding[m[i]] for i in m}
                concrete = theorem(**dic)
                concrete._depth = self.state.current_depth
                # if try complex, solutions in later iterations may be weaker than previous ones and unionfind because of abondoning complex equations, causing check condition failure
                if not self.state.try_complex and not self.state.check_conditions(concrete.condition()):
                    for condition in concrete.condition():
                        if not self.state.check_conditions(condition):
                            print(f"Failed condition: {condition}")
                            breakpoint()
                            self.state.check_conditions(condition)
                            assert False
                if not concrete.degenerate():
                    assignments.append(concrete)
                solution = False
                for i in m:
                    solution = Or((formal_points[str(i)] != m[i]), solution)
                solver.add(solution)
                solutions.append(solution)
            solver.pop()
            for item in solutions:
                solver.add(item)
            solver.push()
            assignments.sort(key=lambda x: str(x))
            return assignments
        
        applicable_theorems = []
        pbar = tqdm(theorems, disable=self.state.silent)
        for theorem in pbar:
            pbar.set_description(
                f"{theorem.__name__} #rels {len(self.state.relations)} # eqns {len(self.state.equations)}")
            concrete_theorems = search_assignments(theorem)
            applicable_theorems += concrete_theorems
        return applicable_theorems
    
    def apply(self, inferences):
        """Apply instantiated rules by adding their conclusions to the state.

        Args:
            inferences (Iterable[InferenceRule]): Instantiated rules to apply.

        Returns:
            None
        """
        last = None
        cnt = 0
        for item in inferences:
            tmp = type(item)
            if not tmp == last:
                if cnt > 3:
                    if not self.state.silent:
                        self.state.logger.info(f"...and {cnt-3} more.")
                cnt = 0
                last = tmp
            if cnt < 3:
                if not self.state.silent:
                    self.state.logger.info(str(item))
            cnt += 1
            conclusions = item.conclusion()
            for i, conclusion in enumerate(conclusions):
                if isinstance(conclusion, sympy.core.expr.Expr):
                    conclusion = Traced(conclusion)
                    conclusion.sources = [item]
                else:
                    conclusion.source = item
                conclusion.depth = self.state.current_depth
                item.depth = self.state.current_depth
                conclusions[i] = conclusion
            self.state.add_relations(conclusions)
        if cnt > 3:
            if not self.state.silent:
                self.state.logger.info(f"...and {cnt - 3} more.")
    
    def run(self):
        """Execute one deductive phase over inner then outer theorems.

        Updates `closure` when no further inferences are available.

        Returns:
            None
        """
        inner_closure = True
        while True:
            if self.state.complete() is not None:
                return
            inner_applicable = self.get_applicable_theorems(self.inner_theorems)
            self.apply(inner_applicable)
            if len(inner_applicable) == 0:
                break
            inner_closure = False
            
        if self.state.complete() is not None:
            return
        
        applicable_theorems = self.get_applicable_theorems(self.outer_theorems)
        self.apply(applicable_theorems)
        
        if len(applicable_theorems) == 0 and inner_closure:
            self.closure = True
            if not self.state.silent:
                self.state.logger.debug("Found Closure")
            return