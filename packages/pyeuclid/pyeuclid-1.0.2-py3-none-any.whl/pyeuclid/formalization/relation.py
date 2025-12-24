"""Geometric primitive types and relations used throughout PyEuclid."""

from __future__ import annotations

import copy
import re
import itertools

from sympy import Symbol, pi  # type: ignore[import]
from pyeuclid.formalization.utils import sort_points, sort_cyclic_points, sort_point_groups,compare_names


class Point:
    """Named geometric point used throughout the formalization."""

    def __init__(self, name: str):
        """Create a point.

        Args:
            name (str): Identifier (underscores are not allowed).
        """
        self.name = name
        assert "_" not in name
        
    def __str__(self):
        return self.name

    def __eq__(self, other):
        return str(self) == str(other)

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(str(self))


class Relation:
    """Base class for logical relations over points."""

    def __init__(self):
        self.negated = False

    def negate(self):
        """Toggle negation flag in-place."""
        self.negated = not self.negated
        
    def get_points(self):
        """Return all point instances contained in the relation."""
        points = []
        for v in vars(self).values():
            if isinstance(v, Point):
                points.append(v)
            elif isinstance(v, list):
                for p in v:
                    if isinstance(p, Point):
                        points.append(p)
        return points

    def __str__(self):
        """Readable representation, prefixed with Not() when negated."""
        class_name = self.__class__.__name__
        points = self.get_points()
        args_name = ",".join([p.name for p in points])
        
        if not self.negated:
            return f"{class_name}({args_name})"
        else:
            return f"Not({class_name}({args_name}))"

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))


class Lt(Relation):
    def __init__(self, v1: Point, v2: Point):
        """Ordering helper used to canonicalize inference rule assignments."""
        super().__init__()
        self.v1 = v1
        self.v2 = v2


class Equal(Relation):
    """Point equality relation."""

    def __init__(self, v1: Point, v2: Point):
        super().__init__()
        self.v1, self.v2 = sort_points(v1, v2)

    def permutations(self):
        """Enumerate equivalent orderings of the two points."""
        return [(self.v1, self.v2), (self.v2, self.v1)]


def Not(p: Relation) -> Relation:
    """Return a negated shallow copy of a relation."""
    other = copy.copy(p)
    other.negate()
    return other


def Angle(p1: Point, p2: Point, p3: Point):
    """Symbolic angle at p2.

    Returns:
        sympy.Symbol: Non-negative angle symbol.
    """
    p1, p3 = sort_points(p1, p3)
    return Symbol(f"Angle_{p1}_{p2}_{p3}", non_negative=True)


def Length(p1: Point, p2: Point):
    """Symbolic length between two points.

    Returns:
        sympy.Symbol: Positive length symbol.
    """
    p1, p2 = sort_points(p1, p2)
    return Symbol(f"Length_{str(p1)}_{str(p2)}", positive=True)


def Area(*ps: list[Point]):
    """Symbolic polygonal area over an ordered point cycle.

    Returns:
        sympy.Symbol: Positive area symbol.
    """
    ps = sort_cyclic_points(*ps)
    return Symbol("_".join(["Area"] + [str(item) for item in ps]), positive=True)


def Variable(name: str):
    """Free symbolic variable placeholder.

    Returns:
        sympy.Symbol: Dimensionless variable symbol.
    """
    return Symbol(f"Variable_{name}")


class Different(Relation):
    """All provided points must be pairwise distinct."""

    def __init__(self, *ps: list[Point]):
        """
        Args:
            *ps (Point): Points that must be distinct.
        """
        super().__init__()
        self.ps = ps

    def definition(self):
        """Expand to pairwise inequality relations.

        Returns:
            list[Relation]: Negated equalities for every point pair.
        """
        return [Not(Equal(self.ps[i], self.ps[j])) for i in range(len(self.ps)) for j in range(i + 1, len(self.ps))]


class Between(Relation):
    """p1 lies between p2 and p3 (on the same line)."""

    def __init__(self, p1: Point, p2: Point, p3: Point):
        """
        p1 is between p2 and p3.

        Args:
            p1 (Point): Middle point.
            p2 (Point): Endpoint 1.
            p3 (Point): Endpoint 2.
        """
        super().__init__()
        p2, p3 = sort_points(p2, p3)
        self.p1, self.p2, self.p3 = p1, p2, p3

    def permutations(self):
        """Enumerate equivalent point orderings for the between relation.

        Returns:
            list[tuple[Point, Point, Point]]: Permitted permutations.
        """
        return [(self.p1, self.p2, self.p3), (self.p1, self.p3, self.p2)]


class SameSide(Relation):
    """Points p1,p2 lie on the same side of the line (p3,p4)."""

    def __init__(self, p1: Point, p2: Point, p3: Point, p4: Point):
        """
        Args:
            p1 (Point): First query point.
            p2 (Point): Second query point.
            p3 (Point): Line endpoint 1.
            p4 (Point): Line endpoint 2.
        """
        super().__init__()
        self.p1, self.p2 = sort_points(p1, p2)
        self.p3, self.p4 = sort_points(p3, p4)

    def permutations(self):
        """Enumerate symmetric orderings for same-side tests."""
        return [
            (self.p1, self.p2, self.p3, self.p4),
            (self.p1, self.p2, self.p4, self.p3),
            (self.p2, self.p1, self.p3, self.p4),
            (self.p2, self.p1, self.p4, self.p3),
        ]


class OppositeSide(Relation):
    """Points p1,p2 lie on opposite sides of the line (p3,p4)."""

    def __init__(self, p1: Point, p2: Point, p3: Point, p4: Point):
        """
        Args:
            p1 (Point): First query point.
            p2 (Point): Second query point.
            p3 (Point): Line endpoint 1.
            p4 (Point): Line endpoint 2.
        """
        super().__init__()
        self.p1, self.p2 = sort_points(p1, p2)
        self.p3, self.p4 = sort_points(p3, p4)

    def definition(self):
        """Logical expansion expressing opposite-side constraints.

        Returns:
            list[Relation]: Primitive relations defining opposite sides.
        """
        return [
            Not(Collinear(self.p1, self.p3, self.p4)),
            Not(Collinear(self.p2, self.p3, self.p4)),
            Not(SameSide(self.p1, self.p2, self.p3, self.p4)),
        ]


class Collinear(Relation):
    """Points p1,p2,p3 are collinear."""

    def __init__(self, p1, p2, p3):
        """
        Args:
            p1 (Point)
            p2 (Point)
            p3 (Point)
        """
        super().__init__()
        self.p1, self.p2, self.p3 = sort_points(p1, p2, p3)

    def permutations(self):
        """Enumerate collinearity argument permutations.

        Returns:
            itertools.permutations: All orderings of the three points.
        """
        return itertools.permutations([self.p1, self.p2, self.p3])


class NotCollinear(Relation):
    """Points p1,p2,p3 are not collinear."""

    def __init__(self, p1, p2, p3):
        """
        Args:
            p1 (Point)
            p2 (Point)
            p3 (Point)
        """
        super().__init__()
        self.p1, self.p2, self.p3 = sort_points(p1, p2, p3)

    def definition(self):
        """Expand non-collinearity into primitive constraints."""
        return [
            Not(Collinear(self.p1, self.p2, self.p3)),
            Different(self.p1, self.p2, self.p3)
        ]


class Midpoint(Relation):
    """p1 is the midpoint of segment p2p3."""

    def __init__(self, p1: Point, p2: Point, p3: Point):
        """
        Args:
            p1 (Point): Candidate midpoint.
            p2 (Point): Segment endpoint.
            p3 (Point): Segment endpoint.
        """
        super().__init__()
        self.p1 = p1
        self.p2, self.p3 = sort_points(p2, p3)

    def definition(self):
        """Midpoint expressed via equal lengths, collinearity, and betweenness.

        Returns:
            list[Relation | sympy.Expr]: Derived relations/equations.
        """
        return [
            Length(self.p1, self.p2) - Length(self.p1, self.p3),
            Collinear(self.p1, self.p2, self.p3),
            Different(self.p2, self.p3),
            Between(self.p1, self.p2, self.p3),
        ]
        

class Congruent(Relation):
    """Triangles (p1,p2,p3) and (p4,p5,p6) are congruent."""

    def __init__(
        self, p1: Point, p2: Point, p3: Point, p4: Point, p5: Point, p6: Point
    ):
        """
        Args:
            p1, p2, p3 (Point): First triangle vertices.
            p4, p5, p6 (Point): Second triangle vertices.
        """
        super().__init__()
        self.p1, self.p2, self.p3, self.p4, self.p5, self.p6 = p1, p2, p3, p4, p5, p6

    def definition(self):
        """Congruence expressed as equal side lengths and non-collinearity.

        Returns:
            list[Relation | sympy.Expr]: Derived relations/equations.
        """
        return [
            Length(self.p1, self.p2) - Length(self.p4, self.p5),
            Length(self.p2, self.p3) - Length(self.p5, self.p6),
            Length(self.p1, self.p3) - Length(self.p4, self.p6),
            NotCollinear(self.p1, self.p2, self.p3),
        ]


class Similar(Relation):
    """Triangles (p1,p2,p3) and (p4,p5,p6) are similar."""

    def __init__(
        self, p1: Point, p2: Point, p3: Point, p4: Point, p5: Point, p6: Point
    ):
        """
        Args:
            p1, p2, p3 (Point): First triangle vertices.
            p4, p5, p6 (Point): Second triangle vertices.
        """
        super().__init__()
        self.p1, self.p2, self.p3, self.p4, self.p5, self.p6 = p1, p2, p3, p4, p5, p6

    def definition(self):
        """Similarity expressed via length ratios and non-collinearity.

        Returns:
            list[Relation | sympy.Expr]: Derived relations/equations.
        """
        return [
            Length(self.p1, self.p2) / Length(self.p4, self.p5)
            - Length(self.p2, self.p3) / Length(self.p5, self.p6),
            Length(self.p1, self.p2) / Length(self.p4, self.p5)
            - Length(self.p3, self.p1) / Length(self.p6, self.p4),
            NotCollinear(self.p1, self.p2, self.p3),
        ]


class Concyclic(Relation):
    """All given points lie on the same circle."""

    def __init__(self, *ps: Point):
        """
        Args:
            *ps (Point): Points to be tested for concyclicity.
        """
        super().__init__()
        self.ps = list(sort_points(*ps))

    def permutations(self):
        """Enumerate symmetric permutations of the point set.

        Returns:
            itertools.permutations: All orderings of the points.
        """
        return itertools.permutations(self.ps)


class Parallel(Relation):
    """Segments (p1,p2) and (p3,p4) are parallel."""

    def __init__(self, p1: Point, p2: Point, p3: Point, p4: Point):
        """
        Args:
            p1, p2 (Point): First segment endpoints.
            p3, p4 (Point): Second segment endpoints.
        """
        super().__init__()
        p1, p2 = sort_points(p1, p2)
        p3, p4 = sort_points(p3, p4)
        self.p1, self.p2, self.p3, self.p4 = sort_point_groups([p1, p2], [p3, p4])

    def permutations(self):
        """Enumerate symmetric endpoint permutations preserving segment groups.

        Returns:
            list[tuple[Point, Point, Point, Point]]: Valid permutations.
        """
        return [
            (self.p1, self.p2, self.p3, self.p4),
            (self.p1, self.p2, self.p4, self.p3),
            (self.p2, self.p1, self.p3, self.p4),
            (self.p2, self.p1, self.p4, self.p3),
            (self.p3, self.p4, self.p1, self.p2),
            (self.p4, self.p3, self.p1, self.p2),
            (self.p3, self.p4, self.p2, self.p1),
            (self.p4, self.p3, self.p2, self.p1),
        ]


class Perpendicular(Relation):
    """Segments (p1,p2) and (p3,p4) are perpendicular."""

    def __init__(self, p1: Point, p2: Point, p3: Point, p4: Point):
        """
        Args:
            p1, p2 (Point): First segment endpoints.
            p3, p4 (Point): Second segment endpoints.
        """
        super().__init__()
        p1, p2 = sort_points(p1, p2)
        p3, p4 = sort_points(p3, p4)
        self.p1, self.p2, self.p3, self.p4 = sort_point_groups([p1, p2], [p3, p4])

    def permutations(self):
        """Enumerate symmetric endpoint permutations preserving segment groups.

        Returns:
            list[tuple[Point, Point, Point, Point]]: Valid permutations.
        """
        return [
            (self.p1, self.p2, self.p3, self.p4),
            (self.p1, self.p2, self.p4, self.p3),
            (self.p2, self.p1, self.p3, self.p4),
            (self.p2, self.p1, self.p4, self.p3),
            (self.p3, self.p4, self.p1, self.p2),
            (self.p4, self.p3, self.p1, self.p2),
            (self.p3, self.p4, self.p2, self.p1),
            (self.p4, self.p3, self.p2, self.p1),
        ]


class Quadrilateral(Relation):
    """Points form a cyclically ordered quadrilateral."""

    def __init__(self, p1: Point, p2: Point, p3: Point, p4: Point):
        """
        Args:
            p1, p2, p3, p4 (Point): Vertices.
        """
        super().__init__()
        self.p1, self.p2, self.p3, self.p4 = sort_cyclic_points(p1, p2, p3, p4)

    def permutations(self):
        """Enumerate cyclic and reversed vertex orderings.

        Returns:
            list[tuple[Point, Point, Point, Point]]: Valid permutations.
        """
        return [
            (self.p1, self.p2, self.p3, self.p4),
            (self.p2, self.p3, self.p4, self.p1),
            (self.p3, self.p4, self.p1, self.p2),
            (self.p4, self.p1, self.p2, self.p3),
            (self.p4, self.p3, self.p2, self.p1),
            (self.p3, self.p2, self.p1, self.p4),
            (self.p2, self.p1, self.p4, self.p3),
            (self.p1, self.p4, self.p3, self.p2),
        ]

    def definition(self):
        """Opposite sides must lie on opposite sides of diagonals.

        Returns:
            list[Relation]: Primitive opposite-side relations.
        """
        return [
            OppositeSide(self.p1, self.p3, self.p2, self.p4),
            OppositeSide(self.p2, self.p4, self.p1, self.p3),
        ]


class Pentagon(Relation):
    """Points form a cyclically ordered pentagon."""

    def __init__(self, p1: Point, p2: Point, p3: Point, p4: Point, p5: Point):
        """
        Args:
            p1, p2, p3, p4, p5 (Point): Vertices.
        """
        super().__init__()
        self.p1, self.p2, self.p3, self.p4, self.p5 = sort_cyclic_points(p1, p2, p3, p4, p5)

    def permutations(self):
        """Enumerate cyclic and reversed vertex orderings.

        Returns:
            list[tuple[Point, Point, Point, Point, Point]]: Valid permutations.
        """
        return [
            (self.p1, self.p2, self.p3, self.p4, self.p5),
            (self.p2, self.p3, self.p4, self.p5, self.p1),
            (self.p3, self.p4, self.p5, self.p1, self.p2),
            (self.p4, self.p5, self.p1, self.p2, self.p3),
            (self.p5, self.p1, self.p2, self.p3, self.p4),
            (self.p5, self.p4, self.p3, self.p2, self.p1),
            (self.p4, self.p3, self.p2, self.p1, self.p5),
            (self.p3, self.p2, self.p1, self.p5, self.p4),
            (self.p2, self.p1, self.p5, self.p4, self.p3),
            (self.p1, self.p5, self.p4, self.p3, self.p2),
        ]


class Similar4P(Relation):
    """Two quadrilaterals are similar."""

    def __init__(
        self,
        p1: Point,
        p2: Point,
        p3: Point,
        p4: Point,
        p5: Point,
        p6: Point,
        p7: Point,
        p8: Point,
    ):
        """
        Args:
            p1..p4 (Point): First quadrilateral.
            p5..p8 (Point): Second quadrilateral.
        """
        super().__init__()
        point_map_12 = {p1: p5, p2: p6, p3: p7, p4: p8}
        point_map_21 = {p5: p1, p6: p2, p7: p3, p8: p4}

        sorted_1 = sort_cyclic_points(p1, p2, p3, p4)
        sorted_2 = sort_cyclic_points(p5, p6, p7, p8)
        if compare_names(sorted_1, sorted_2) == 0:
            self.p1, self.p2, self.p3, self.p4 = sorted_1
            self.p5,self.p6,self.p7,self.p8 = point_map_12[self.p1], point_map_12[
                self.p2], point_map_12[self.p3], point_map_12[self.p4]
        else:
            self.p1, self.p2, self.p3, self.p4 = sorted_2
            self.p5, self.p6, self.p7, self.p8 = point_map_21[self.p1], point_map_21[
                self.p2], point_map_21[self.p3], point_map_21[self.p4]

    def definition(self):
        """Similarity expressed via side ratios and angle equalities.

        Returns:
            list[Relation | sympy.Expr]: Derived relations/equations.
        """
        return [
            Length(self.p1, self.p2) / Length(self.p5, self.p6)
            - Length(self.p2, self.p3) / Length(self.p6, self.p7),
            Length(self.p1, self.p2) / Length(self.p5, self.p6)
            - Length(self.p3, self.p4) / Length(self.p7, self.p8),
            Length(self.p1, self.p2) / Length(self.p5, self.p6)
            - Length(self.p4, self.p1) / Length(self.p8, self.p5),
            Angle(self.p1, self.p2, self.p3) - Angle(self.p5, self.p6, self.p7),
            Angle(self.p2, self.p3, self.p4) - Angle(self.p6, self.p7, self.p8),
            Angle(self.p3, self.p4, self.p1) - Angle(self.p7, self.p8, self.p5),
            Angle(self.p4, self.p1, self.p2) - Angle(self.p8, self.p5, self.p6),
        ]


class Similar5P(Relation):
    """Two pentagons are similar."""

    def __init__(
        self,
        p1: Point,
        p2: Point,
        p3: Point,
        p4: Point,
        p5: Point,
        p6: Point,
        p7: Point,
        p8: Point,
        p9: Point,
        p10: Point,
    ):
        """
        Args:
            p1..p5 (Point): First pentagon.
            p6..p10 (Point): Second pentagon.
        """
        super().__init__()
        self.p1, self.p2, self.p3, self.p4, self.p5, self.p6, self.p7, self.p8, self.p9, self.p10 = p1, p2, p3, p4, p5, p6, p7, p8, p9, p10

    def definition(self):
        """Similarity expressed via consecutive side ratios and angle equalities.

        Returns:
            list[Relation | sympy.Expr]: Derived relations/equations.
        """
        return [
            Length(self.p1, self.p2) / Length(self.p6, self.p7)
            - Length(self.p2, self.p3) / Length(self.p7, self.p8),
            Length(self.p2, self.p3) / Length(self.p7, self.p8)
            - Length(self.p3, self.p4) / Length(self.p8, self.p9),
            Length(self.p3, self.p4) / Length(self.p8, self.p9)
            - Length(self.p4, self.p5) / Length(self.p9, self.p10),
            Length(self.p4, self.p5) / Length(self.p9, self.p10)
            - Length(self.p5, self.p1) / Length(self.p10, self.p6),
            Length(self.p5, self.p1) / Length(self.p10, self.p6)
            - Length(self.p1, self.p2) / Length(self.p6, self.p7),
            Angle(self.p1, self.p2, self.p3) - Angle(self.p6, self.p7, self.p8),
            Angle(self.p2, self.p3, self.p4) - Angle(self.p7, self.p8, self.p9),
            Angle(self.p3, self.p4, self.p5) - Angle(self.p8, self.p9, self.p10),
            Angle(self.p4, self.p5, self.p1) - Angle(self.p9, self.p10, self.p6),
            Angle(self.p5, self.p1, self.p2) - Angle(self.p10, self.p6, self.p7),
        ]


class Parallelogram(Relation):
    def __init__(self, p1: Point, p2: Point, p3: Point, p4: Point):
        super().__init__()
        self.p1, self.p2, self.p3, self.p4 = sort_cyclic_points(p1, p2, p3, p4)

    def definition(self):
        return [
            Parallel(self.p1, self.p2, self.p3, self.p4),
            Parallel(self.p2, self.p3, self.p4, self.p1),
            Quadrilateral(self.p1, self.p2, self.p3, self.p4),
        ]


class Square(Relation):
    def __init__(self, p1: Point, p2: Point, p3: Point, p4: Point):
        super().__init__()
        self.p1, self.p2, self.p3, self.p4 = sort_cyclic_points(p1, p2, p3, p4)

    def definition(self):
        return [
            Length(self.p1, self.p2) - Length(self.p2, self.p3),
            Length(self.p2, self.p3) - Length(self.p3, self.p4),
            Length(self.p3, self.p4) - Length(self.p4, self.p1),
            Length(self.p4, self.p1) - Length(self.p1, self.p2),
            Angle(self.p1, self.p2, self.p3) - pi / 2,
            Angle(self.p2, self.p3, self.p4) - pi / 2,
            Angle(self.p3, self.p4, self.p1) - pi / 2,
            Angle(self.p4, self.p1, self.p2) - pi / 2,
            Quadrilateral(self.p1, self.p2, self.p3, self.p4),
        ]


class Rectangle(Relation):
    def __init__(self, p1: Point, p2: Point, p3: Point, p4: Point):
        super().__init__()
        self.p1, self.p2, self.p3, self.p4 = sort_cyclic_points(p1, p2, p3, p4)

    def definition(self):
        return [
            Length(self.p1, self.p2) - Length(self.p3, self.p4),
            Length(self.p2, self.p3) - Length(self.p4, self.p1),
            Angle(self.p1, self.p2, self.p3) - pi / 2,
            Angle(self.p2, self.p3, self.p4) - pi / 2,
            Angle(self.p3, self.p4, self.p1) - pi / 2,
            Angle(self.p4, self.p1, self.p2) - pi / 2,
            Quadrilateral(self.p1, self.p2, self.p3, self.p4),
        ]


class Rhombus(Relation):
    def __init__(self, p1: Point, p2: Point, p3: Point, p4: Point):
        super().__init__()
        self.p1, self.p2, self.p3, self.p4 = sort_cyclic_points(p1, p2, p3, p4)

    def definition(self):
        return [
            Length(self.p1, self.p2) - Length(self.p2, self.p3),
            Length(self.p2, self.p3) - Length(self.p3, self.p4),
            Length(self.p3, self.p4) - Length(self.p4, self.p1),
            Length(self.p4, self.p1) - Length(self.p1, self.p2),
            Perpendicular(self.p1, self.p3, self.p2, self.p4),
            Quadrilateral(self.p1, self.p2, self.p3, self.p4),
        ]


class Trapezoid(Relation):
    def __init__(self, p1: Point, p2: Point, p3: Point, p4: Point):
        super().__init__()
        if p1.name > p3.name:
            if p3.name > p4.name:
                self.p1, self.p2, self.p3, self.p4 = p4, p3, p2, p1
            else:
                self.p1, self.p2, self.p3, self.p4 = p3, p4, p1, p2
        else:
            if p1.name > p2.name:
                self.p1, self.p2, self.p3, self.p4 = p2, p1, p4, p3
            else:
                self.p1, self.p2, self.p3, self.p4 = p1, p2, p3, p4

    def definition(self):
        return [
            Parallel(self.p1, self.p2, self.p3, self.p4),
            Quadrilateral(self.p1, self.p2, self.p3, self.p4),
        ]


class Kite(Relation):
    def __init__(self, p1: Point, p2: Point, p3: Point, p4: Point):
        super().__init__()
        self.p1, self.p2, self.p3, self.p4 = p1, p2, p3, p4

    def definition(self):
        return [
            Length(self.p1, self.p2) - Length(self.p2, self.p3),
            Length(self.p3, self.p4) - Length(self.p4, self.p1),
            Angle(self.p2, self.p1, self.p4) - Angle(self.p2, self.p3, self.p4),
            Angle(self.p1, self.p2, self.p3) - Angle(self.p1, self.p4, self.p3),
            Different(self.p1, self.p2, self.p3, self.p4),
            Perpendicular(self.p1, self.p3, self.p2, self.p4),
            Quadrilateral(self.p1, self.p2, self.p3, self.p4),
        ]


class Incenter(Relation):
    def __init__(self, p1: Point, p2: Point, p3: Point, p4: Point):
        super().__init__()
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.p4 = p4

    def definition(self):
        return [
            Angle(self.p3, self.p2, self.p1) - Angle(self.p1, self.p2, self.p4),
            Angle(self.p2, self.p4, self.p1) - Angle(self.p1, self.p4, self.p3),
            Angle(self.p4, self.p3, self.p1) - Angle(self.p1, self.p3, self.p2),
        ]


class Centroid(Relation):
    def __init__(
        self, o: Point, a: Point, b: Point, c: Point, d: Point, e: Point, f: Point
    ):
        super().__init__()
        self.o = o
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e
        self.f = f

    def definition(self):
        return [
            Midpoint(self.d, self.b, self.c),
            Midpoint(self.e, self.a, self.c),
            Midpoint(self.f, self.b, self.a),
            NotCollinear(self.a, self.b, self.c),
            Collinear(self.o, self.a, self.d),
            Collinear(self.o, self.b, self.e),
            Collinear(self.o, self.c, self.f),
            Between(self.o, self.a, self.d),
            Between(self.o, self.b, self.e),
            Between(self.o, self.c, self.f),
        ]


def get_points_and_symbols(eqn):
    pattern = re.compile(r"((?:Angle|Length|Area|Variable)\w+)")
    # eqn.free_symbols is not apRelationoriate in this case, we need an ordered list instead of a set
    matches = pattern.findall(str(eqn))
    symbols = []
    points = []
    for match in matches:
        cls, args = match.split("_")[0], match.split("_")[1:]
        if cls == "Variable":
            arg = "_".join(match.split("_")[1:])
            symbol = Variable(arg)
        else:
            args = [Point(item) for item in args]
            if cls == "Angle":
                symbol = Angle(*args)
            elif cls == "Length":
                symbol = Length(*args)
            elif cls == "Area":
                symbol = Area(*args)
            points += args
        symbols.append(symbol)
    return points, symbols
