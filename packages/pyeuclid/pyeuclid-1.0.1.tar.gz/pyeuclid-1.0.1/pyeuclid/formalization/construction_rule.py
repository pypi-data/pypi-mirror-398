from sympy import pi

from pyeuclid.formalization.relation import *
from pyeuclid.formalization.utils import *

construction_rule_sets = {}


class ConstructionRule:
    """Base class for geometric construction rules."""

    def __init__(self):
        """Initialize an empty construction rule."""
        pass
    
    def arguments(self):
        """Return the input entities required for the construction."""
        return []
        
    def constructed_points(self):
        """Return the points constructed by this rule."""
        return []

    def conditions(self):
        """Return prerequisite relations for the construction to be valid."""
        return []
    
    def conclusions(self):
        """Return relations implied after applying the construction."""
        return []

    def __str__(self):
        class_name = self.__class__.__name__
        attributes = ",".join(str(value) for _, value in vars(self).items())
        return f"{class_name}({attributes})"


class register:
    """Decorator that registers a construction rule into labeled sets."""

    def __init__(self, *annotations):
        self.annotations = annotations

    def __call__(self, cls):
        for item in self.annotations:
            if not item in construction_rule_sets:
                construction_rule_sets[item] = [cls]
            else:
                construction_rule_sets[item].append(cls)

        def expanded_conditions(self):
            return expand_definition(self._conditions())

        cls._conditions = cls.conditions
        cls.conditions = expanded_conditions
        return cls


@register("AG")
class construct_angle_bisector(ConstructionRule):
    """Construct the bisector point X of angle ABC."""
    def __init__(self, x, a, b, c):
        self.x, self.a, self.b, self.c = x, a, b, c
        
    def arguments(self):
        return [self.a, self.b, self.c]
    
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [NotCollinear(self.a, self.b, self.c)]

    def conclusions(self):
        return [Angle(self.a, self.b, self.x) - Angle(self.x, self.b, self.c)]


@register("AG")
class construct_angle_mirror(ConstructionRule):
    """Construct point X as the mirror of BA across BC."""
    def __init__(self, x, a, b, c):
        self.x, self.a, self.b, self.c = x, a, b, c
        
    def arguments(self):
        return [self.a, self.b, self.c]
    
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [NotCollinear(self.a, self.b, self.c)]

    def conclusions(self):
        return [Angle(self.a, self.b, self.c) - Angle(self.c, self.b, self.x)]


@register("AG")
class construct_circle(ConstructionRule):
    """Construct circle center X equidistant from A, B, C."""
    def __init__(self, x, a, b, c):
        self.x, self.a, self.b, self.c = x, a, b, c
        
    def arguments(self):
        return [self.a, self.b, self.c]
    
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [NotCollinear(self.a, self.b, self.c)]

    def conclusions(self):
        return [
            Length(self.x, self.a) - Length(self.x, self.b),
            Length(self.x, self.b) - Length(self.x, self.c),
        ]


@register("AG")
class construct_circumcenter(ConstructionRule):
    """Construct circumcenter X of triangle ABC."""
    def __init__(self, x, a, b, c):
        self.x, self.a, self.b, self.c = x, a, b, c
        
    def arguments(self):
        return [self.a, self.b, self.c]
    
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [NotCollinear(self.a, self.b, self.c)]

    def conclusions(self):
        return [
            Length(self.x, self.a) - Length(self.x, self.b),
            Length(self.x, self.b) - Length(self.x, self.c),
        ]


@register("AG")
class construct_eq_quadrangle(ConstructionRule):
    """Construct quadrilateral ABCD with equal diagonals."""
    def __init__(self, a, b, c, d):
        self.a, self.b, self.c, self.d = a, b, c, d
        
    def constructed_points(self):
        return [self.a, self.b, self.c, self.d]
    
    def conclusions(self):
        return [
            Length(self.a, self.d) - Length(self.b, self.c)
        ]


@register("AG")
class construct_eq_trapezoid(ConstructionRule):
    """Construct isosceles trapezoid ABCD (AB ∥ CD)."""
    def __init__(self, a, b, c, d):
        self.a, self.b, self.c, self.d = a, b, c, d
        
    def constructed_points(self):
        return [self.a, self.b, self.c, self.d]

    def conclusions(self):
        return [
            Length(self.a, self.d) - Length(self.b, self.c),
            Parallel(self.a, self.b, self.c, self.d),
            Angle(self.d, self.a, self.b) - Angle(self.a, self.b, self.c),
            Angle(self.b, self.c, self.d) - Angle(self.c, self.d, self.a),
        ]


@register("AG")
class construct_eq_triangle(ConstructionRule):
    """Construct equilateral triangle with vertex X and base BC."""
    def __init__(self, x, b, c):
        self.x, self.b, self.c = x, b, c
        
    def arguments(self):
        return [self.b, self.c]
        
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [Different(self.b, self.c)]

    def conclusions(self):
        return [
            Length(self.x, self.b) - Length(self.b, self.c),
            Length(self.b, self.c) - Length(self.c, self.x),
            Angle(self.x, self.b, self.c) - Angle(self.b, self.c, self.x),
            Angle(self.c, self.x, self.b) - Angle(self.x, self.b, self.c),
        ]


@register("AG")
class construct_eqangle2(ConstructionRule):
    """Construct X so that angle ABX equals angle XCB."""
    def __init__(self, x, a, b, c):
        self.x, self.a, self.b, self.c = x, a, b, c
        
    def arguments(self):
        return [self.a, self.b, self.c]
        
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [NotCollinear(self.a, self.b, self.c)]

    def conclusions(self):
        return [Angle(self.b, self.a, self.x) - Angle(self.x, self.c, self.b)]


@register("AG")
class construct_eqdia_quadrangle(ConstructionRule):
    def __init__(self, a, b, c, d):
        self.a, self.b, self.c, self.d = a, b, c, d
        
    def constructed_points(self):
        return [self.a, self.b, self.c, self.d]
    
    def conclusions(self):
        return [
            Length(self.b, self.d) - Length(self.a, self.c)
        ]


@register("AG")
class construct_eqdistance(ConstructionRule):
    def __init__(self, x, a, b, c):
        self.x, self.a, self.b, self.c = x, a, b, c
    
    def arguments(self):
        return [self.a, self.b, self.c]
        
    def constructed_points(self):
        return [self.x]
    
    def conditions(self):
        return [Different(self.b, self.c)]

    def conclusions(self):
        return [Length(self.x, self.a) - Length(self.b, self.c)]


@register("AG")
class construct_eqdistance2(ConstructionRule):
    def __init__(self, x, a, b, c, alpha):
        self.x, self.a, self.b, self.c, self.alpha = x, a, b, c, alpha
    
    def arguments(self):
        return [self.a, self.b, self.c, self.alpha]
        
    def constructed_points(self):
        return [self.x]
    
    def conditions(self):
        return [Different(self.b, self.c)]

    def conclusions(self):
        return [Length(self.x, self.a) - sympy.simplify(self.alpha) * Length(self.b, self.c)]


@register("AG")
class construct_eqdistance3(ConstructionRule):
    def __init__(self, x, a, alpha):
        self.x, self.a, self.alpha = x, a, alpha
    
    def arguments(self):
        return [self.a, self.alpha]
        
    def constructed_points(self):
        return [self.x]

    def conclusions(self):
        return [Length(self.x, self.a) - sympy.simplify(self.alpha)]


@register("AG")
class construct_foot(ConstructionRule):
    def __init__(self, x, a, b, c):
        self.x, self.a, self.b, self.c = x, a, b, c
    
    def arguments(self):
        return [self.a, self.b, self.c]
        
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [NotCollinear(self.a, self.b, self.c)]

    def conclusions(self):
        return [Perpendicular(self.x, self.a, self.b, self.c), Collinear(self.x, self.b, self.c)]


@register("AG")
class construct_free(ConstructionRule):
    def __init__(self, a):
        self.a = a
        
    def constructed_points(self):
        return [self.a]


@register("AG")
class construct_incenter(ConstructionRule):
    def __init__(self, x, a, b, c):
        self.x, self.a, self.b, self.c = x, a, b, c
    
    def arguments(self):
        return [self.a, self.b, self.c]
        
    def constructed_points(self):
        return [self.x]
    
    def conditions(self):
        return [NotCollinear(self.a, self.b, self.c)]

    def conclusions(self):
        return [
            Angle(self.b, self.a, self.x) - Angle(self.x, self.a, self.c),
            Angle(self.a, self.c, self.x) - Angle(self.x, self.c, self.b),
            Angle(self.c, self.b, self.x) - Angle(self.x, self.b, self.a),
        ]


class construct_incenter2(ConstructionRule):
    def __init__(self, x, y, z, i, a, b, c):
        self.x, self.y, self.z, self.i, self.a, self.b, self.c = x, y, z, i, a, b, c
        
    def arguments(self):
        return [self.a, self.b, self.c]
        
    def constructed_points(self):
        return [self.x, self.y, self.z, self.i]
    
    def conditions(self):
        return [NotCollinear(self.a, self.b, self.c)]

    def conclusions(self):
        return [
            Angle(self.b, self.a, self.i) - Angle(self.i, self.a, self.c),
            Angle(self.a, self.c, self.i) - Angle(self.i, self.c, self.b),
            Angle(self.c, self.b, self.i) - Angle(self.i, self.b, self.a),
            Collinear(self.x, self.b, self.c),
            Perpendicular(self.i, self.x, self.b, self.c),
            Collinear(self.y, self.c, self.a),
            Perpendicular(self.i, self.y, self.c, self.a),
            Collinear(self.z, self.a, self.b),
            Perpendicular(self.i, self.z, self.a, self.b),
            Length(self.i, self.x) - Length(self.i, self.y),
            Length(self.i, self.y) - Length(self.i, self.z),
        ]


@register("AG")
class construct_excenter(ConstructionRule):
    def __init__(self, x, a, b, c):
        self.x, self.a, self.b, self.c = x, a, b, c
    
    def arguments(self):
        return [self.a, self.b, self.c]
        
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [NotCollinear(self.a, self.b, self.c)]

    def conclusions(self):
        return [
            Angle(self.b, self.a, self.x) - Angle(self.x, self.a, self.c),
            Angle(self.a, self.b, self.x) - (Angle(self.a, self.b, self.c) / 2 + pi / 2),
            Angle(self.a, self.c, self.x) - (Angle(self.a, self.c, self.b) / 2 + pi / 2),
        ]


class construct_excenter2(ConstructionRule):
    def __init__(self, x, y, z, i, a, b, c):
        self.x, self.y, self.z, self.i, self.a, self.b, self.c = x, y, z, i, a, b, c
    
    def arguments(self):
        return [self.a, self.b, self.c]
        
    def constructed_points(self):
        return [self.x, self.y, self.z, self.i]
    
    def conditions(self):
        return [NotCollinear(self.a, self.b, self.c)]

    def conclusions(self):
        return [
            Angle(self.b, self.a, self.i) - Angle(self.i, self.a, self.c),
            Angle(self.a, self.b, self.i) - (Angle(self.a, self.b, self.c) / 2 + pi / 2),
            Angle(self.a, self.c, self.i) - (Angle(self.a, self.c, self.b) / 2 + pi / 2),
            Collinear(self.x, self.b, self.c),
            Perpendicular(self.i, self.x, self.b, self.c),
            Collinear(self.y, self.c, self.a),
            Perpendicular(self.i, self.y, self.c, self.a),
            Collinear(self.z, self.a, self.b),
            Perpendicular(self.i, self.z, self.a, self.b),
            Length(self.i, self.x) - Length(self.i, self.y),
            Length(self.i, self.y) - Length(self.i, self.z),
        ]


@register("AG")
class construct_centroid(ConstructionRule):
    def __init__(self, x, y, z, i, a, b, c):
        self.x, self.y, self.z, self.i, self.a, self.b, self.c = x, y, z, i, a, b, c
    
    def arguments(self):
        return [self.a, self.b, self.c]
        
    def constructed_points(self):
        return [self.x, self.y, self.z, self.i]
    
    def conditions(self):
        return [NotCollinear(self.a, self.b, self.c)]

    def conclusions(self):
        return [
            Collinear(self.x, self.b, self.c),
            Length(self.x, self.b) - Length(self.x, self.c),
            Collinear(self.y, self.c, self.a),
            Length(self.y, self.c) - Length(self.y, self.a),
            Collinear(self.z, self.a, self.b),
            Length(self.z, self.a) - Length(self.z, self.b),
            Collinear(self.a, self.x, self.i),
            Collinear(self.b, self.y, self.i),
            Collinear(self.c, self.z, self.i),
        ]


@register("AG")
class construct_intersection_cc(ConstructionRule):
    def __init__(self, x, o, w, a):
        self.x, self.o, self.w, self.a = x, o, w, a
    
    def arguments(self):
        return [self.o, self.w, self.a]
        
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [NotCollinear(self.o, self.w, self.a)]

    def conclusions(self):
        return [
            Length(self.o, self.a) - Length(self.o, self.x),
            Length(self.w, self.a) - Length(self.w, self.x),
        ]


@register("AG")
class construct_intersection_lc(ConstructionRule):
    def __init__(self, x, a, o, b):
        self.x, self.a, self.o, self.b = x, a, o, b
    
    def arguments(self):
        return [self.a, self.o, self.b]
        
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [
            Different(self.a, self.b),
            Different(self.o, self.b),
            Not(Perpendicular(self.b, self.o, self.b, self.a)),
        ]

    def conclusions(self):
        return [
            Collinear(self.x, self.a, self.b),
            Length(self.o, self.b) - Length(self.o, self.x),
        ]


@register("AG")
class construct_intersection_ll(ConstructionRule):
    def __init__(self, x, a, b, c, d):
        self.x, self.a, self.b, self.c, self.d = x, a, b, c, d
    
    def arguments(self):
        return [self.a, self.b, self.c, self.d]
        
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [
            Not(Parallel(self.a, self.b, self.c, self.d))
            # ,Not(Collinear(self.a,self.b,self.c,self.d)) # TODO
        ]

    def conclusions(self):
        return [Collinear(self.x, self.a, self.b), Collinear(self.x, self.c, self.d)]


@register("AG")
class construct_intersection_lp(ConstructionRule):
    def __init__(self, x, a, b, c, m, n):
        self.x, self.a, self.b, self.c, self.m, self.n = x, a, b, c, m, n
    
    def arguments(self):
        return [self.a, self.b, self.c, self.m, self.n]
        
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [
            Not(Parallel(self.m, self.n, self.a, self.b)),
            NotCollinear(self.a, self.b, self.c),
            NotCollinear(self.c, self.m, self.n),
        ]

    def conclusions(self):
        return [Collinear(self.x, self.a, self.b), Parallel(self.c, self.x, self.m, self.n)]


@register("AG")
class construct_intersection_lt(ConstructionRule):
    def __init__(self, x, a, b, c, d, e):
        self.x, self.a, self.b, self.c, self.d, self.e = x, a, b, c, d, e
        
    def arguments(self):
        return [self.a, self.b, self.c, self.d, self.e]
        
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [
            NotCollinear(self.a, self.b, self.c),
            Not(Perpendicular(self.a, self.b, self.d, self.e)),
        ]

    def conclusions(self):
        return [Collinear(self.x, self.a, self.b), Perpendicular(self.x, self.c, self.d, self.e)]


@register("AG")
class construct_intersection_pp(ConstructionRule):
    def __init__(self, x, a, b, c, d, e, f):
        self.x, self.a, self.b, self.c, self.d, self.e, self.f = x, a, b, c, d, e, f
    
    def arguments(self):
        return [self.a, self.b, self.c, self.d, self.e, self.f]
        
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [
            Different(self.a, self.d),
            Not(Parallel(self.b, self.c, self.e, self.f)),
        ]

    def conclusions(self):
        return [
            Parallel(self.x, self.a, self.b, self.c),
            Parallel(self.x, self.d, self.e, self.f),
        ]


@register("AG")
class construct_intersection_tt(ConstructionRule):
    def __init__(self, x, a, b, c, d, e, f):
        self.x, self.a, self.b, self.c, self.d, self.e, self.f = x, a, b, c, d, e, f
    
    def arguments(self):
        return [self.a, self.b, self.c, self.d, self.e, self.f]
        
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [
            Different(self.a, self.d),
            Not(Parallel(self.b, self.c, self.e, self.f)),
        ]

    def conclusions(self):
        return [
            Perpendicular(self.x, self.a, self.b, self.c),
            Perpendicular(self.x, self.d, self.e, self.f),
        ]


@register("AG")
class construct_iso_triangle(ConstructionRule):
    def __init__(self, a, b, c):
        self.a, self.b, self.c = a, b, c
        
    def constructed_points(self):
        return [self.a, self.b, self.c]
    
    def conclusions(self):
        return [Length(self.a, self.b) - Length(self.a, self.c), Angle(self.a, self.b, self.c) - Angle(self.b, self.c, self.a)]


@register("AG")
class construct_lc_tangent(ConstructionRule):
    def __init__(self, x, a, o):
        self.x, self.a, self.o = x, a, o
    
    def arguments(self):
        return [self.a, self.o]
        
    def constructed_points(self):
        return [self.x]

    def conclusions(self):
        return [Perpendicular(self.a, self.x, self.a, self.o)]


@register("AG")
class construct_midpoint(ConstructionRule):
    def __init__(self, x, a, b):
        self.x, self.a, self.b = x, a, b
    
    def arguments(self):
        return [self.a, self.b]
        
    def constructed_points(self):
        return [self.x]
    
    def conditions(self):
        return [Different(self.a, self.b)]

    def conclusions(self):
        return [Collinear(self.x, self.a, self.b), Length(self.x, self.a) - Length(self.x, self.b)]


@register("AG")
class construct_mirror(ConstructionRule):
    def __init__(self, x, a, b):
        self.x, self.a, self.b = x, a, b
    
    def arguments(self):
        return [self.a, self.b]
        
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [Different(self.a, self.b)]

    def conclusions(self):
        return [
            Length(self.b, self.a) - Length(self.b, self.x),
            Collinear(self.x, self.a, self.b),
        ]


@register("AG")
class construct_nsquare(ConstructionRule):
    def __init__(self, x, a, b):
        self.x, self.a, self.b = x, a, b
    
    def arguments(self):
        return [self.a, self.b]
        
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [Different(self.a, self.b)]

    def conclusions(self):
        return [
            Length(self.x, self.a) - Length(self.a, self.b),
            Perpendicular(self.x, self.a, self.a, self.b),
        ]


@register("AG")
class construct_on_aline(ConstructionRule):
    def __init__(self, x, a, b, c, d, e):
        self.x, self.a, self.b, self.c, self.d, self.e = x, a, b, c, d, e
    
    def arguments(self):
        return [self.a, self.b, self.c, self.d, self.e]
        
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [
            NotCollinear(self.c, self.d, self.e),
            Different(self.a, self.b),
            Different(self.c, self.d),
            Different(self.c, self.e),
        ]

    def conclusions(self):
        return Angle(self.x, self.a, self.b) - Angle(self.c, self.d, self.e), Angle(self.x, self.a, self.b) + Angle(self.c, self.d, self.e) - pi



# @register("AG")
# class construct_on_aline2(ConstructionRule):
#     def __init__(self, x, a, b, c, d, e):
#         self.x, self.a, self.b, self.c, self.d, self.e = x, a, b, c, d, e
    
#     def arguments(self):
#         return [self.a, self.b, self.c, self.d, self.e]
        
#     def constructed_points(self):
#         return [self.x]

#     def conditions(self):
#         return [
#             NotCollinear(self.c, self.d, self.e),
#             Different(self.a, self.b),
#             Different(self.c, self.d),
#             Different(self.c, self.e),
#         ]

#     def conclusions(self):
#         return [Angle(self.x, self.a, self.b) + Angle(self.c, self.d, self.e) - pi]


@register("AG")
class construct_on_bline(ConstructionRule):
    def __init__(self, x, a, b):
        self.x, self.a, self.b = x, a, b
    
    def arguments(self):
        return [self.a, self.b]
        
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [Different(self.a, self.b)]

    def conclusions(self):
        return [
            Length(self.x, self.a) - Length(self.x, self.b),
            Angle(self.x, self.a, self.b) - Angle(self.a, self.b, self.x),
        ]


@register("AG")
class construct_on_circle(ConstructionRule):
    def __init__(self, x, o, a):
        self.x, self.o, self.a = x, o, a
    
    def arguments(self):
        return [self.o, self.a]
        
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [Different(self.o, self.a)]

    def conclusions(self):
        return [Length(self.o, self.x) - Length(self.o, self.a)]


@register("AG")
class construct_on_line(ConstructionRule):
    def __init__(self, x, a, b):
        self.x, self.a, self.b = x, a, b
    
    def arguments(self):
        return [self.a, self.b]
        
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [Different(self.a, self.b)]

    def conclusions(self):
        return [Collinear(self.x, self.a, self.b)]


@register("AG")
class construct_on_pline(ConstructionRule):
    def __init__(self, x, a, b, c):
        self.x, self.a, self.b, self.c = x, a, b, c
    
    def arguments(self):
        return [self.a, self.b, self.c]
        
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [Different(self.b, self.c), NotCollinear(self.a, self.b, self.c)]

    def conclusions(self):
        return [Parallel(self.x, self.a, self.b, self.c)]


@register("AG")
class construct_on_tline(ConstructionRule):
    def __init__(self, x, a, b, c):
        self.x, self.a, self.b, self.c = x, a, b, c
    
    def arguments(self):
        return [self.a, self.b, self.c]
        
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [Different(self.b, self.c)]

    def conclusions(self):
        return [Perpendicular(self.x, self.a, self.b, self.c)]


@register("AG")
class construct_orthocenter(ConstructionRule):
    def __init__(self, x, a, b, c):
        self.x, self.a, self.b, self.c = x, a, b, c
    
    def arguments(self):
        return [self.a, self.b, self.c]
        
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [NotCollinear(self.a, self.b, self.c)]

    def conclusions(self):
        return [
            Perpendicular(self.x, self.a, self.b, self.c),
            Perpendicular(self.x, self.b, self.c, self.a),
            Perpendicular(self.x, self.c, self.a, self.b),
        ]


@register("AG")
class construct_parallelogram(ConstructionRule):
    def __init__(self, a, b, c, x):
        self.a, self.b, self.c, self.x = a, b, c, x
    
    def arguments(self):
        return [self.a, self.b, self.c]
        
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [NotCollinear(self.a, self.b, self.c)]

    def conclusions(self):
        return [
            Parallel(self.a, self.b, self.c, self.x),
            Parallel(self.a, self.x, self.b, self.c),
            Length(self.a, self.b) - Length(self.c, self.x),
            Length(self.a, self.x) - Length(self.b, self.c),
        ]


@register("AG")
class construct_pentagon(ConstructionRule):
    def __init__(self, a, b, c, d, e):
        self.a, self.b, self.c, self.d, self.e = a, b, c, d, e
        
    def constructed_points(self):
        return [self.a, self.b, self.c, self.d, self.e]


@register("AG")
class construct_psquare(ConstructionRule):
    def __init__(self, x, a, b):
        self.x, self.a, self.b = x, a, b
    
    def arguments(self):
        return [self.a, self.b]
        
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [Different(self.a, self.b)]

    def conclusions(self):
        return [
            Length(self.x, self.a) - Length(self.a, self.b),
            Perpendicular(self.x, self.a, self.a, self.b),
        ]


@register("AG")
class construct_quadrangle(ConstructionRule):
    def __init__(self, a, b, c, d):
        self.a, self.b, self.c, self.d = a, b, c, d
        
    def constructed_points(self):
        return [self.a, self.b, self.c, self.d]


@register("AG")
class construct_r_trapezoid(ConstructionRule):
    def __init__(self, a, b, c, d):
        self.a, self.b, self.c, self.d = a, b, c, d
        
    def constructed_points(self):
        return [self.a, self.b, self.c, self.d]
    
    def conclusions(self):
        return [Perpendicular(self.a, self.b, self.a, self.d), Parallel(self.a, self.b, self.c, self.d)]


@register("AG")
class construct_r_triangle(ConstructionRule):
    def __init__(self, a, b, c):
        self.a, self.b, self.c = a, b, c
        
    def constructed_points(self):
        return [self.a, self.b, self.c]
    
    def conclusions(self):
        return [Perpendicular(self.a, self.b, self.a, self.c)]


@register("AG")
class construct_rectangle(ConstructionRule):
    def __init__(self, a, b, c, d):
        self.a, self.b, self.c, self.d = a, b, c, d
        
    def constructed_points(self):
        return [self.a, self.b, self.c, self.d]
    
    def conclusions(self):
        return [
            Perpendicular(self.a, self.b, self.b, self.c),
            Parallel(self.a, self.b, self.c, self.d),
            Parallel(self.a, self.d, self.b, self.c),
            Perpendicular(self.a, self.b, self.a, self.d),
            Length(self.a, self.b) - Length(self.c, self.d),
            Length(self.a, self.d) - Length(self.b, self.c),
            Length(self.a, self.c) - Length(self.b, self.d),
        ]


@register("AG")
class construct_reflect(ConstructionRule):
    def __init__(self, x, a, b, c):
        self.x, self.a, self.b, self.c = x, a, b, c
    
    def arguments(self):
        return [self.a, self.b, self.c]
        
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [Different(self.b, self.c), NotCollinear(self.a, self.b, self.c)]

    def conclusions(self):
        return [
            Perpendicular(self.b, self.c, self.a, self.x),
            Length(self.a, self.b) - Length(self.b, self.x),
            Length(self.a, self.c) - Length(self.c, self.x),
        ]


@register("AG")
class construct_risos(ConstructionRule):
    def __init__(self, a, b, c):
        self.a, self.b, self.c = a, b, c
        
    def constructed_points(self):
        return [self.a, self.b, self.c]
    
    def conclusions(self):
        return [
            Angle(self.a, self.b, self.c) - Angle(self.b, self.c, self.a),
            Perpendicular(self.a, self.b, self.a, self.c),
            Length(self.a, self.b) - Length(self.a, self.c),
        ]


@register("AG")
class construct_s_angle(ConstructionRule):
    def __init__(self, a, b, x, alpha):
        self.a, self.b, self.x, self.alpha = a, b, x, alpha
    
    def arguments(self):
        return [self.a, self.b, self.alpha]
        
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [Different(self.a, self.b)]

    def conclusions(self):
        return [Angle(self.a, self.b, self.x) - sympy.simplify(sympy.Rational(abs(self.alpha),180)*pi)]


@register("AG")
class construct_segment(ConstructionRule):
    def __init__(self, a, b):
        self.a, self.b = a, b
        
    def constructed_points(self):
        return [self.a, self.b]


@register("AG")
class construct_s_segment(ConstructionRule):
    def __init__(self, a, b, alpha):
        self.a, self.b, self.alpha = a, b, alpha
    
    def arguments(self):
        return [self.alpha]
        
    def constructed_points(self):
        return [self.a, self.b]

    def conclusions(self):
        return [Length(self.a, self.x) - sympy.simplify(self.alpha)]


@register("AG")
class construct_shift(ConstructionRule):
    def __init__(self, x, b, c, d):
        self.x, self.b, self.c, self.d = x, b, c, d
    
    def arguments(self):
        return [self.b, self.c, self.d]
        
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [Different(self.d, self.b)]

    def conclusions(self):
        return [
            Length(self.x, self.b) - Length(self.c, self.d),
            Length(self.x, self.c) - Length(self.b, self.d),
        ]


class construct_square(ConstructionRule):
    def __init__(self, a, b, x, y):
        self.a, self.b, self.x, self.y = a, b, x, y
    
    def arguments(self):
        return [self.a, self.b]
        
    def constructed_points(self):
        return [self.x, self.y]
    
    def conditions(self):
        return [Different(self.a, self.b)]

    def conclusions(self):
        return [
            Perpendicular(self.a, self.b, self.b, self.x),
            Length(self.a, self.b) - Length(self.b, self.x),
            Parallel(self.a, self.b, self.x, self.y),
            Parallel(self.a, self.y, self.b, self.x),
            Perpendicular(self.a, self.y, self.y, self.x),
            Length(self.b, self.x) - Length(self.x, self.y),
            Length(self.x, self.y) - Length(self.y, self.a),
            Perpendicular(self.a, self.x, self.b, self.y),
            Length(self.a, self.x) - Length(self.b, self.y),
        ]


@register("AG")
class construct_isquare(ConstructionRule):
    def __init__(self, a, b, c, d):
        self.a, self.b, self.c, self.d = a, b, c, d
        
    def constructed_points(self):
        return [self.a, self.b, self.c, self.d]
    
    def conclusions(self):
        return [
            Perpendicular(self.a, self.b, self.b, self.c),
            Length(self.a, self.b) - Length(self.b, self.c),
            Parallel(self.a, self.b, self.c, self.d),
            Parallel(self.a, self.d, self.b, self.c),
            Perpendicular(self.a, self.d, self.d, self.c),
            Length(self.b, self.c) - Length(self.c, self.d),
            Length(self.c, self.d) - Length(self.d, self.a),
            Perpendicular(self.a, self.c, self.b, self.d),
            Length(self.a, self.c) - Length(self.b, self.d),
        ]


@register("AG")
class construct_trapezoid(ConstructionRule):
    def __init__(self, a, b, c, d):
        self.a, self.b, self.c, self.d = a, b, c, d
        
    def constructed_points(self):
        return [self.a, self.b, self.c, self.d]
    
    def conclusions(self):
        return [Parallel(self.a, self.b, self.c, self.d)]


@register("AG")
class construct_triangle(ConstructionRule):
    def __init__(self, a, b, c):
        self.a, self.b, self.c = a, b, c
        
    def constructed_points(self):
        return [self.a, self.b, self.c]


@register("AG")
class construct_triangle12(ConstructionRule):
    def __init__(self, a, b, c):
        self.a, self.b, self.c = a, b, c
        
    def constructed_points(self):
        return [self.a, self.b, self.c]
    
    def conclusions(self):
        return [Length(self.a, self.b) / Length(self.a, self.c) - 1 / 2]


@register("AG")
class construct_2l1c(ConstructionRule):
    def __init__(self, x, y, z, i, a, b, c, o):
        self.x, self.y, self.z, self.i, self.a, self.b, self.c, self.o = x, y, z, i, a, b, c, o
    
    def arguments(self):
        return [self.a, self.b, self.c, self.o]
        
    def constructed_points(self):
        return [self.x, self.y, self.z, self.i]
    
    def conditions(self):
        return [
            Length(self.o, self.a) - Length(self.o, self.b),
            NotCollinear(self.a, self.b, self.c),
        ]

    def conclusions(self):
        return [
            Collinear(self.x, self.a, self.c),
            Collinear(self.y, self.b, self.c),
            Length(self.o, self.a) - Length(self.o, self.z),
            Collinear(self.i, self.o, self.z),
            Length(self.i, self.x) - Length(self.i, self.y),
            Length(self.i, self.y) - Length(self.i, self.z),
            Perpendicular(self.i, self.x, self.a, self.c),
            Perpendicular(self.i, self.y, self.b, self.c),
        ]


@register("AG")
class construct_e5128(ConstructionRule):
    def __init__(self, x, y, a, b, c, d):
        self.x, self.y, self.a, self.b, self.c, self.d = x, y, a, b, c, d
    
    def arguments(self):
        return [self.a, self.b, self.c, self.d]
        
    def constructed_points(self):
        return [self.x, self.y]
    
    def conditions(self):
        return [
            Length(self.c, self.b) - Length(self.c, self.d),
            Perpendicular(self.b, self.c, self.b, self.a),
        ]

    def conclusions(self):
        return [
            Length(self.c, self.b) - Length(self.c, self.x),
            Collinear(self.y, self.a, self.b),
            Collinear(self.x, self.y, self.d),
            Angle(self.b, self.a, self.d) - Angle(self.a, self.x, self.y),
        ]


@register("AG")
class construct_3peq(ConstructionRule):
    def __init__(self, x, y, z, a, b, c):
        self.x, self.y, self.z, self.a, self.b, self.c = x, y, z, a, b, c
    
    def arguments(self):
        return [self.a, self.b, self.c]
        
    def constructed_points(self):
        return [self.x, self.y, self.z]
    
    def conditions(self):
        return [NotCollinear(self.a, self.b, self.c)]

    def conclusions(self):
        return [
            Collinear(self.z, self.b, self.c),
            Collinear(self.x, self.a, self.b),
            Collinear(self.y, self.a, self.c),
            Collinear(self.x, self.y, self.z),
            Length(self.z, self.x) - Length(self.z, self.y),
        ]


@register("AG")
class construct_trisect(ConstructionRule):
    def __init__(self, x, y, a, b, c):
        self.x, self.y, self.a, self.b, self.c = x, y, a, b, c
    
    def arguments(self):
        return [self.a, self.b, self.c]
        
    def constructed_points(self):
        return [self.x, self.y]
    
    def conditions(self):
        return [NotCollinear(self.a, self.b, self.c)]

    def conclusions(self):
        return [
            Angle(self.a, self.b, self.x) - Angle(self.x, self.b, self.y),
            Angle(self.x, self.b, self.y) - Angle(self.y, self.b, self.c),
            Collinear(self.x, self.a, self.c),
            Collinear(self.y, self.a, self.c),
        ]


@register("AG")
class construct_trisegment(ConstructionRule):
    def __init__(self, x, y, a, b):
        self.x, self.y, self.a, self.b = x, y, a, b
    
    def arguments(self):
        return [self.a, self.b]
        
    def constructed_points(self):
        return [self.x, self.y]
    
    def conditions(self):
        return [Different(self.a, self.b)]

    def conclusions(self):
        return [
            Length(self.a, self.x) - Length(self.x, self.y),
            Length(self.x, self.y) - Length(self.y, self.b),
            Collinear(self.x, self.a, self.b),
            Collinear(self.y, self.a, self.b),
        ]


@register("AG")
class construct_on_dia(ConstructionRule):
    def __init__(self, x, a, b):
        self.x, self.a, self.b = x, a, b
    
    def arguments(self):
        return [self.a, self.b]
        
    def constructed_points(self):
        return [self.x]
        
    def conditions(self):
        return [Different(self.a, self.b)]

    def conclusions(self):
        return [Perpendicular(self.x, self.a, self.x, self.b)]


@register("AG")
class construct_ieq_triangle(ConstructionRule):
    def __init__(self, a, b, c):
        self.a, self.b, self.c = a, b, c
        
    def constructed_points(self):
        return [self.a, self.b, self.c]
    
    def conclusions(self):
        return [
            Length(self.a, self.b) - Length(self.b, self.c),
            Length(self.b, self.c) - Length(self.c, self.a),
            Angle(self.b, self.a, self.c) - Angle(self.a, self.c, self.b),
            Angle(self.a, self.c, self.b) - Angle(self.c, self.b, self.a),
        ]


@register("AG")
class construct_on_opline(ConstructionRule):
    def __init__(self, x, a, b):
        self.x, self.a, self.b = x, a, b
    
    def arguments(self):
        return [self.a, self.b]
        
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [Different(self.a, self.b)]

    def conclusions(self):
        return [Collinear(self.x, self.a, self.b)]


class construct_cc_tangent0(ConstructionRule):
    def __init__(self, x, y, o, a, w, b):
        self.x, self.y, self.o, self.a, self.w, self.b = x, y, o, a, w, b
    
    def arguments(self):
        return [self.o, self.a, self.w, self.b]
        
    def constructed_points(self):
        return [self.x, self.y]
    
    def conditions(self):
        return [
            Different(self.o, self.a),
            Different(self.w, self.b),
            Different(self.o, self.w),
        ]

    def conclusions(self):
        return [
            Length(self.o, self.x) - Length(self.o, self.a),
            Length(self.w, self.y) - Length(self.w, self.b),
            Perpendicular(self.x, self.o, self.x, self.y),
            Perpendicular(self.y, self.w, self.y, self.x)
        ]
        

class construct_cc_tangent(ConstructionRule):
    def __init__(self, x, y, z, i, o, a, w, b):
        self.x, self.y, self.z, self.i, self.o, self.a, self.w, self.b = x, y, z, i, o, a, w, b
    
    def arguments(self):
        return [self.o, self.a, self.w, self.b]
        
    def constructed_points(self):
        return [self.x, self.y, self.z, self.i]
    
    def conditions(self):
        return [
            Different(self.o, self.a),
            Different(self.w, self.b),
            Different(self.o, self.w),
        ]

    def conclusions(self):
        return [
            Length(self.o, self.x) - Length(self.o, self.a),
            Length(self.w, self.y) - Length(self.w, self.b),
            Perpendicular(self.x, self.o, self.x, self.y),
            Perpendicular(self.y, self.w, self.y, self.x),
            Length(self.o, self.z) - Length(self.o, self.a),
            Length(self.w, self.i) - Length(self.w, self.b),
            Perpendicular(self.z, self.o, self.z, self.i),
            Perpendicular(self.i, self.w, self.i, self.z),
        ]


@register("AG")
class construct_eqangle3(ConstructionRule):
    def __init__(self, x, a, b, d, e, f):
        self.x, self.a, self.b, self.d, self.e, self.f = x, a, b, d, e, f
    
    def arguments(self):
        return [self.a, self.b, self.d, self.e, self.f]
        
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [
            NotCollinear(self.d, self.e, self.f),
            Different(self.a, self.b),
            Different(self.d, self.e),
            Different(self.e, self.f),
        ]

    def conclusions(self):
        return [Angle(self.a, self.x, self.b) - Angle(self.e, self.d, self.f)]


@register("AG")
class construct_tangent(ConstructionRule):
    def __init__(self, x, y, a, o, b):
        self.x, self.y, self.a, self.o, self.b = x, y, a, o, b
    
    def arguments(self):
        return [self.a, self.o, self.b]
        
    def constructed_points(self):
        return [self.x, self.y]
    
    def conditions(self):
        return [
            Different(self.o, self.a),
            Different(self.o, self.b),
            Different(self.a, self.b),
        ]

    def conclusions(self):
        return [
            Length(self.o, self.x) - Length(self.o, self.b),
            Perpendicular(self.a, self.x, self.o, self.x),
            Length(self.o, self.y) - Length(self.o, self.b),
            Perpendicular(self.a, self.y, self.o, self.y),
        ]


@register("AG")
class construct_on_circum(ConstructionRule):
    def __init__(self, x, a, b, c):
        self.x, self.a, self.b, self.c = x, a, b, c
    
    def arguments(self):
        return [self.a, self.b, self.c]
        
    def constructed_points(self):
        return [self.x]
        
    def conditions(self):
        return [NotCollinear(self.a, self.b, self.c)]
    
    def conclusions(self):
        return [Concyclic(self.a, self.b, self.c, self.x)]


class construct_sameside(ConstructionRule):
    def __init__(self, x, a, b, c):
        self.x, self.a, self.b, self.c = x, a, b, c
    
    def arguments(self):
        return [self.a, self.b, self.c]
        
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [NotCollinear(self.a, self.b, self.c)]

    def conclusions(self):
        return [SameSide(self.x, self.a, self.b, self.c)]


class construct_opposingsides(ConstructionRule):
    def __init__(self, x, a, b, c):
        self.x, self.a, self.b, self.c = x, a, b, c
    
    def arguments(self):
        return [self.a, self.b, self.c]
        
    def constructed_points(self):
        return [self.x]

    def conditions(self):
        return [NotCollinear(self.a, self.b, self.c)]

    def conclusions(self):
        return [OppositeSide(self.x, self.a, self.b, self.c)]