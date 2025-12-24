"""Core orchestration for geometric search.

`Engine` coordinates the deductive database (discrete inference rules) with the
algebraic system (symbolic equation solving) against a mutable `State`. The two
systems alternate until a goal is solved, a fixed point is reached, or a depth
limit is hit.
"""

from pyeuclid.formalization.relation import *


class Engine:
    """Coordinate deductive and algebraic reasoning over a `State`.

    Typical usage::

        state = State()
        db = DeductiveDatabase(state)
        alg = AlgebraicSystem(state)
        engine = Engine(state, db, alg)
        engine.search()
    """

    def __init__(self, state, deductive_database, algebraic_system):
        """Create an engine.

        Args:
            state (State): Shared state tracking relations, equations, and goal.
            deductive_database (DeductiveDatabase): Applies inference rules.
            algebraic_system (AlgebraicSystem): Solves symbolic constraints.
        """
        self.state = state
        self.deductive_database = deductive_database
        self.algebraic_system = algebraic_system
        
    def search(self, depth=9999):
        """Run alternating algebraic + deductive steps until solved or closed.

        Args:
            depth (int): Maximum additional reasoning depth to explore before returning.

        The method:
            1) solves current algebraic constraints,
            2) alternates deductive and algebraic steps, incrementing depth,
            3) stops early if the goal is satisfied or the deductive database reports closure.

        Returns:
            None
        """
        self.algebraic_system.run()
        for _ in range(self.state.current_depth, self.state.current_depth + depth):
            if self.state.complete() is not None:
                break
            
            self.state.current_depth += 1
            
            self.deductive_database.run()
            
            if self.deductive_database.closure:
                break
            
            if self.state.complete() is not None:
                break
            
            self.algebraic_system.run()
    
    def step(self, conditions, conclusions=[]):
        """Apply a single interactive step constrained to given conditions.

        The method temporarily restricts the state to a subset of relations,
        verifies `conditions`, runs one search depth, then checks `conclusions`.
        It restores the previous state afterward, allowing interactive/human-in-the-loop
        experimentation without polluting the main search trace.

        Args:
            conditions (Iterable): Relations/equations that must hold.
            conclusions (Iterable): Relations/equations expected to be derivable.

        Raises:
            AssertionError: If `conditions` is empty.
            Exception: If any condition cannot be verified or any conclusion fails.

        Returns:
            None
        """
        assert len(conditions) > 0
        relations_bak = self.state.relations
        equations_bak = self.state.equations
        lengths_bak = self.state.lengths
        angles_bak = self.state.angles
        points_bak = self.state.points
        
        diagrammatic_relations = (Between, SameSide, Collinear)
        
        try:
            self.algebraic_system.solve_equation()
            for condition in conditions:
                if not self.state.check_conditions(condition):
                    raise Exception(f"Condition {condition} is not verified")
            diagrammatic_relations = [item for item in self.state.relations if isinstance(item, diagrammatic_relations)]
            
            self.state.add_relations(conditions)

            for relation in diagrammatic_relations:
                if all([point in self.state.points for point in relation.get_points()]):
                    self.state.add_relation(relation)
                
            self.search(depth=1)
            
            for conclusion in conclusions:
                if not self.state.check_conditions(conclusion):
                    raise Exception(f"Conclusion {conclusion} is not verified")
                
            self.state.points = points_bak
            self.state.lengths = lengths_bak
            self.state.angles = angles_bak
            new_relations = [item for item in self.state.relations if not item in conditions]
            new_equations = [item for item in self.state.equations if not item in conditions]
            self.state.relations = relations_bak
            self.state.equations = equations_bak
            self.state.add_relations(new_relations + new_equations)
            self.state.solutions = self.state.solutions[:-1]
            self.algebraic_system.solve_equation()
        
        except Exception as e:
            self.state.points = points_bak
            self.state.lengths = lengths_bak
            self.state.angles = angles_bak
            self.state.relations = relations_bak
            self.state.equations = equations_bak
            raise e
    