"""State container for geometric problems and intermediate deductions."""

import os
import sys
import logging

from itertools import permutations

from pyeuclid.formalization.utils import *
from pyeuclid.formalization.translation import *
from pyeuclid.formalization.diagram import *
from pyeuclid.formalization.relation import *


class State:
    """Mutable state holding points, relations, equations, and goal/solution status."""

    def __init__(self):
        self.goal = None
        self.diagram = None
        self.points = set()
        self.relations = set()
        self.equations = []
        self.lengths = UnionFind()
        self.angles = UnionFind()
        self.var_types = {}
        self.ratios = {}
        self.angle_sums = {}
        
        self.current_depth = 0
        self.solutions = []
        self.solvers = {}
        self.try_complex = False
        self.silent = False
        self.logger = logging.getLogger(__name__)
        self.set_logger(logging.DEBUG)
        
    def load_problem(self, conditions=None, goal=None, diagram=None):        
        """Seed the state with initial conditions, goal, and optional diagram.

        Adds relations/equations, infers variable categories, sets the goal, and
        records an optional diagram instance.

        Args:
            conditions (Iterable | None): Relations/equations to seed the state.
            goal (Relation | sympy.Expr | None): Target to satisfy.
            diagram (Diagram | None): Optional diagram object.

        Returns:
            None
        """
        if conditions:
            self.add_relations(conditions)
            old_size = 0
            self.categorize_variable()
            size = len(self.var_types)
            while(size > old_size):
                self.categorize_variable()
                old_size = size
                size = len(self.var_types)
        if goal:
            self.goal = goal
        if diagram:
            self.diagram = diagram
    
    def set_logger(self, level):
        """Configure the state logger; rank-aware for MPI runs.

        Args:
            level (int): Logging level (e.g., logging.INFO).

        Returns:
            None
        """
        self.logger.setLevel(level)
        rank = os.environ.get("OMPI_COMM_WORLD_RANK", None)
        if not len(self.logger.handlers):
            handler = logging.StreamHandler(sys.stdout)
            if rank is None:
                formatter = logging.Formatter(
                    '%(levelname)s - %(message)s')  # %(asctime)s - %(name)s -
            else:
                formatter = logging.Formatter(
                    rank+' %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
    def add_relations(self, relations):
        """Add one or more relations/equations, expanding definitions as needed.

        Args:
            relations: Relation or sympy expression or iterable of them. Composite
                relations with a `definition()` are expanded before insertion.

        Returns:
            None
        """
        if not isinstance(relations, (tuple, list, set)):
            relations = [relations]
        for item in relations:
            if hasattr(item, "definition") and not item.negated:
                self.add_relations(item.definition())
            else:
                if isinstance(item, Relation):
                    self.add_relation(item)
                else:
                    self.add_equation(item)
    
    def add_relation(self, relation):
        """Insert a relation, ensuring its points are tracked."""
        if relation in self.relations:
            return
        points = relation.get_points()
        for p in points:
            self.add_point(p)
        self.relations.add(relation)
        
    def add_point(self, p):
        """Track a new point and initialize length union-find edges to existing points.

        Args:
            p (Point): Point to register.

        Returns:
            None
        """
        if not p in self.points:
            for point in self.points:
                self.lengths.add(Length(point, p))
            self.points.add(p)
    
    def add_equation(self, equation):
        """Insert an equation, tracing its depth and registering involved symbols.

        Args:
            equation (sympy.Expr): Equation to add.

        Returns:
            None
        """
        # allow redundant equations for neat proofs
        equation = Traced(equation, depth=self.current_depth)
        for item in self.equations:
            if equation.expr - item.expr == 0:
                return
        points, quantities = get_points_and_symbols(equation)
        for p in points:
            self.add_point(p)
        unionfind = None
        for quantity in quantities:
            if "Angle" in str(quantity):
                unionfind = self.angles
                unionfind.add(quantity)
            elif "Length" in str(quantity):
                unionfind = self.lengths
                unionfind.add(quantity)
        self.equations.append(equation)
    
    def categorize_variable(self):
        """Infer variable types (Angle/Length) from existing equations.

        Returns:
            None
        """
        angle_linear, length_linear, length_ratio, others = classify_equations(self.equations, self.var_types)
        for eq in self.equations:
            if "Variable" not in str(eq):
                continue
            _, entities = get_points_and_symbols(eq)
            label = None
            if eq in angle_linear and ("Angle" in str(eq) or "pi" in str(eq)):
                label = "Angle"
            elif eq in length_linear and "Length" in str(eq):
                label = "Length"
            elif eq in length_ratio and "Length" in str(eq):
                label = "Length"
            else:
                continue
            for entity in entities:
                if label is not None:
                    if entity in self.var_types:
                        if self.var_types[entity] is None: # dimensionless variable
                            continue
                        elif self.var_types[entity] != label:
                            self.var_types[entity] = None
                    else:
                        self.var_types[entity] = label
        
    def load_problem_from_text(self, text, diagram_path=None, resample=False):
        """Parse a textual benchmark instance and populate state+diagram.

        Builds a diagram, verifies numerical consistency with the goal, and
        populates points/relations deduced from construction rules and sampling.

        Args:
            text (str): Problem description string.
            diagram_path (str | None): Optional path for saving diagram.
            resample (bool): Force resampling even if cache exists.

        Returns:
            None
        Raises:
            Exception: If a consistent diagram cannot be generated in allotted attempts.
        """
        constructions_list = get_constructions_list_from_text(text)
        goal = get_goal_from_text(text)
        
        diagram = Diagram(constructions_list, diagram_path, resample=resample)
        satisfied, satisfied_goal = diagram.numerical_check_goal(goal)
        
        for _ in range(MAX_DIAGRAM_ATTEMPTS):
            if satisfied:
                break
            diagram = Diagram(constructions_list, diagram_path, resample=True)
            satisfied, satisfied_goal = diagram.numerical_check_goal(goal)

        if not satisfied:
            raise Exception(f"Failed to satisfy goal after {MAX_DIAGRAM_ATTEMPTS} attempts.")
        
        self.diagram = diagram
        self.goal = satisfied_goal
        # self.diagram.show()
        
        for constructions in constructions_list:
            for construction in constructions:
                for p in construction.constructed_points():
                    self.add_point(p)
                
                relations = construction.conclusions()
                if isinstance(relations, tuple):
                    if self.diagram.numerical_check(relations[0]):
                        assert not self.diagram.numerical_check(relations[1])
                        self.add_relations(relations[0])
                    else:
                        assert self.diagram.numerical_check(relations[1])
                        self.add_relations(relations[1])
                else:
                    self.add_relations(relations)
        
        for perm in permutations(self.points, 3):
            between_relation = Between(*perm)
            if self.diagram.numerical_check(between_relation):
                self.add_relations(between_relation)
                
            notcollinear_relation = NotCollinear(*perm)
            if self.diagram.numerical_check(notcollinear_relation):
                self.add_relations(notcollinear_relation)
        
        for perm in permutations(self.points, 4):
            sameside_relation = SameSide(*perm)
            if self.diagram.numerical_check(sameside_relation):
                self.add_relations(sameside_relation)
                
            oppositeside_relation = OppositeSide(*perm)
            if self.diagram.numerical_check(oppositeside_relation):
                self.add_relations(oppositeside_relation)
 
    def complete(self):
        """Return solved status: True/expr if goal satisfied, else None.

        Returns:
            bool | sympy.Expr | None: True or numeric expression if solved; otherwise None.
        """
        if isinstance(self.goal, Relation):
            if self.check_conditions(self.goal):
                return True
            else:
                return None
        else:
            assert isinstance(self.goal, sympy.core.expr.Expr)
            solution = self.simplify_equation(self.goal)
            if len(solution.free_symbols) == 0:
                return solution
            return None
    
    def simplify_equation(self, expr, depth=None):
        """Substitute solved variables into an expression.

        Args:
            expr (sympy.Expr): Expression to simplify.
            depth (int | None): Solution depth to use; defaults to latest.

        Returns:
            sympy.Expr: Simplified expression.
        """
        if depth is None:
            depth = len(self.solutions) - 1
        solved_vars = self.solutions[depth]
        expr = getattr(expr, "expr", expr)
        for symbol in expr.free_symbols:
            if symbol in solved_vars:
                value = solved_vars[symbol].expr
                expr = expr.subs(symbol, value)
        return expr
    
    def check_conditions(self, conditions):
        """Verify that a set of relations/equations holds in the current state.

        Expands relation definitions, checks presence in `relations`, and
        simplifies equations via solved variables.

        Args:
            conditions (Iterable | Relation | sympy.Expr): Conditions to verify.

        Returns:
            bool: True if all conditions hold; False otherwise.
        """
        if not type(conditions) in (list, tuple, set):
            conditions = [conditions]
        conditional_relations, conditional_equations = set(), []
        i = 0
        while i < len(conditions):
            item = conditions[i]
            if isinstance(item, Equal):
                if not ((item.v1 == item.v2) ^ item.negated):
                    return False
            elif hasattr(item, "definition") and not item.negated:
                unrolled = item.definition()
                if not (isinstance(unrolled, tuple) or isinstance(unrolled, list)):
                    unrolled = unrolled,
                conditions += unrolled
            # auxillary predicate for canonical ordering of inference rule params, does not used for checking
            elif isinstance(item, Lt):
                pass
            elif isinstance(item, Between):
                if item.negated:
                    if Not(item) in self.relations:
                        return False
                else:
                    if not item in self.relations:
                        return False
                    if item.p1 == item.p2 or item.p2 == item.p3 or item.p3 == item.p1:
                        return False
            elif isinstance(item, Relation):
                if isinstance(item, Collinear) and (item.p1 == item.p2 or item.p2 == item.p3 or item.p3 == item.p1):
                    pass
                elif not item in self.relations:
                    return False
            else:
                conditional_equations.append(self.simplify_equation(item))
            i += 1
        equation_satisfied = check_equalities(conditional_equations)
        return equation_satisfied
    