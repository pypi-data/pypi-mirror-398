"""Inference rules and registry for the deductive database."""

from __future__ import annotations
from typing import Iterable
from pyeuclid.formalization.relation import *
from pyeuclid.formalization.utils import *
from sympy import sin, cos
import sympy

inference_rule_sets = {}


class register():
    """Decorator that registers an inference rule class into named rule sets."""

    def __init__(self, *annotations):
        self.annotations = annotations

    def __call__(self, cls):
        for item in self.annotations:
            if not item in inference_rule_sets:
                inference_rule_sets[item] = [cls]
            else:
                inference_rule_sets[item].append(cls)

        def expanded_condition(self):
            lst = expand_definition(self._condition())
            return lst

        def expanded_conclusion(self):
            lst = expand_definition(self._conclusion())
            result = []
            for item in lst:
                if isinstance(item, sympy.core.numbers.Zero):
                    continue
                result.append(item)
            return result
        cls._condition = cls.condition
        cls._conclusion = cls.conclusion
        cls.condition = expanded_condition
        cls.conclusion = expanded_conclusion
        return cls


class InferenceRule:
    """Base class for all geometric inference rules.

    Subclasses implement `condition()` and `conclusion()`, each returning
    relations/equations. The `register` decorator wraps these to expand
    definitions and filter zero expressions before the deductive database uses
    them.
    """

    def __init__(self):
        pass

    def condition(self):
        """Return premises (relations/equations) required to trigger the rule."""

    def conclusion(self):
        """Return relations/equations that are added when the rule fires."""

    def get_entities_in_condition(self):
        entities = set()
        for i in self.condition()[2]:
            entities = entities.union(set(i.get_entities()))
        return entities

    def degenerate(self):
        return False

    def get_entities_in_conclusion(self):
        entities = set()
        for i in self.conclusion()[2]:
            entities = entities.union(set(i.get_entities()))
        return entities

    def __str__(self):
        class_name = self.__class__.__name__
        content = []
        for key, value in vars(self).items():
            if key.startswith("_") or key == "depth":
                continue
            if not isinstance(value, Iterable):
                content.append(str(value))
            else:
                content.append(','.join(str(i) for i in value))
        attributes = ','.join(content)
        return f"{class_name}({attributes})"

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))


@register("basic")
class AlphaGeometry1(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point, e: Point, f: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e
        self.f = f

    def condition(self):
        return Perpendicular(self.a, self.b, self.c, self.d), Perpendicular(self.c, self.d, self.e, self.f), Lt(self.a, self.b), Lt(self.c, self.d), Lt(self.e, self.f), Lt(self.a, self.e)

    def conclusion(self):
        return Parallel(self.a, self.b, self.e, self.f)


@register("ex")
class CollinearTransist(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def condition(self):
        return Collinear(self.a, self.b, self.c), Collinear(self.a, self.b, self.d), Lt(self.a, self.b), Lt(self.c, self.d), Different(self.a, self.b, self.c, self.d)

    def conclusion(self):
        return Collinear(self.a, self.c, self.d), Collinear(self.b, self.c, self.d)


@register("ex")
class AlphaGeometry1b(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point, e: Point, f: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e
        self.f = f

    def condition(self):
        return Perpendicular(self.a, self.b, self.c, self.d), Parallel(self.a, self.b, self.e, self.f), Lt(self.a, self.b), Lt(self.c, self.d), Lt(self.e, self.f)

    def conclusion(self):
        return Perpendicular(self.c, self.d, self.e, self.f)


@register("basic")
class AlphaGeometry2(InferenceRule):
    def __init__(self, o: Point, a: Point, b: Point, c: Point, d: Point):
        super().__init__()
        self.o = o
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def condition(self):
        return Length(self.o, self.a) - Length(self.o, self.b), Length(self.o, self.a) - Length(self.o, self.c), Length(self.o, self.a) - Length(self.o, self.d), Lt(self.a, self.b), Lt(self.b, self.c), Lt(self.c, self.d)

    def conclusion(self):
        return Concyclic(self.a, self.b, self.c, self.d)


@register("ex")
class AlphaGeometry3a(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point, e: Point, f: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e
        self.f = f

    def condition(self):
        return Angle(self.a, self.b, self.c) - Angle(self.d, self.e, self.f), Parallel(self.b, self.c, self.e, self.f), SameSide(self.a, self.e, self.b, self.c), OppositeSide(self.d, self.b, self.e, self.f), SameSide(self.f, self.c, self.b, self.e)

    def conclusion(self):
        return Parallel(self.b, self.a, self.d, self.e)


@register("ex")
class AlphaGeometry3b(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point, e: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e

    def condition(self):
        return Angle(self.b, self.a, self.c) - Angle(self.d, self.e, self.c), Collinear(self.a, self.c, self.e), SameSide(self.b, self.d, self.a, self.c), Not(Between(self.c, self.a, self.e))

    def conclusion(self):
        return Parallel(self.a, self.b, self.d, self.e)


@register("basic")
class AlphaGeometry4a(InferenceRule):
    def __init__(self, a: Point, b: Point, p: Point, q: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.p = p
        self.q = q

    def condition(self):
        return Concyclic(self.a, self.b, self.p, self.q), Lt(self.a, self.b), Lt(self.p, self.q), SameSide(self.p, self.q, self.a, self.b)

    def conclusion(self):
        return Angle(self.a, self.p, self.b)-Angle(self.a, self.q, self.b),


@register("basic")
class AlphaGeometry4b(InferenceRule):
    def __init__(self, a: Point, b: Point, p: Point, q: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.p = p
        self.q = q

    def condition(self):
        return Concyclic(self.a, self.b, self.p, self.q), Lt(self.a, self.b), Lt(self.p, self.q), OppositeSide(self.p, self.q, self.a, self.b)

    def conclusion(self):
        return Angle(self.a, self.p, self.b)+Angle(self.a, self.q, self.b)-pi,


@register("basic")
class AlphaGeometry5a(InferenceRule):
    def __init__(self, a: Point, b: Point, p: Point, q: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.p = p
        self.q = q

    def condition(self):
        return Not(Collinear(self.p, self.q, self.b)), Not(Collinear(self.p, self.q, self.a)), Not(Collinear(self.b, self.q, self.a)), Not(Collinear(self.p, self.a, self.b)), Angle(self.a, self.p, self.b)-Angle(self.a, self.q, self.b), Lt(self.a, self.b), Lt(self.p, self.q), SameSide(self.p, self.q, self.a, self.b)

    def conclusion(self):
        return Concyclic(self.a, self.b, self.p, self.q)


@register("basic")
class AlphaGeometry5b(InferenceRule):
    def __init__(self, a: Point, b: Point, p: Point, q: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.p = p
        self.q = q

    def condition(self):
        return Not(Collinear(self.p, self.q, self.b)), Not(Collinear(self.p, self.q, self.a)), Not(Collinear(self.b, self.q, self.a)), Not(Collinear(self.p, self.a, self.b)), Angle(self.a, self.p, self.b)+Angle(self.a, self.q, self.b)-pi, Lt(self.a, self.b), Lt(self.p, self.q), OppositeSide(self.p, self.q, self.a, self.b)

    def conclusion(self):
        return Concyclic(self.a, self.b, self.p, self.q)


@register("basic")
class AlphaGeometry6a(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, p: Point, q: Point, r: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.p = p
        self.q = q
        self.r = r

    def condition(self):
        return Concyclic(self.a, self.b, self.c, self.p), Concyclic(self.a, self.b, self.c, self.q), Concyclic(self.a, self.b, self.c, self.r), Angle(self.a, self.c, self.b)-Angle(self.p, self.r, self.q), Different(self.a, self.b), Different(self.p, self.q)

    def conclusion(self):
        return Length(self.a, self.b)-Length(self.p, self.q)


@register("basic")
class AlphaGeometry6b(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, p: Point, q: Point, r: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.p = p
        self.q = q
        self.r = r

    def condition(self):
        return Concyclic(self.a, self.b, self.c, self.p), Concyclic(self.a, self.b, self.c, self.q), Concyclic(self.a, self.b, self.c, self.r), Angle(self.a, self.c, self.b)+Angle(self.p, self.r, self.q)-pi, Different(self.a, self.b), Different(self.p, self.q)

    def conclusion(self):
        return Length(self.a, self.b)-Length(self.p, self.q)


@register("basic")
class AlphaGeometry7(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, e: Point, f: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.e = e
        self.f = f

    def condition(self):
        return Midpoint(self.e, self.a, self.b), Midpoint(self.f, self.a, self.c), Different(self.b, self.c), Different(self.e, self.f), Lt(self.b, self.c)

    def conclusion(self):
        return Parallel(self.e, self.f, self.b, self.c)


@register("basic")
class AlphaGeometry8(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point, o: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.o = o

    def condition(self):
        return Collinear(self.o, self.a, self.c), Collinear(self.o, self.b, self.d), Parallel(self.a, self.b, self.c, self.d), Different(self.o, self.a, self.b, self.c, self.d), Not(Collinear(self.a, self.c, self.b)), Not(Collinear(self.a, self.c, self.d)), Lt(self.a, self.c), Lt(self.a, self.b), Lt(self.a, self.d)

    def conclusion(self):
        # Length(self.a, self.o)/Length(self.b, self.o)-Length(self.c, self.o)/Length(self.d, self.o) by similar triangle
        return Length(self.a, self.o)/Length(self.b, self.o)-Length(self.a, self.c)/Length(self.b, self.d)


@register("basic")
class AlphaGeometry12(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def condition(self):
        return NotCollinear(self.a, self.b, self.c),  Collinear(self.d, self.b, self.c), Length(self.d, self.b)/Length(self.d, self.c)-Length(self.a, self.b)/Length(self.a, self.c), Lt(self.b, self.c), Between(self.d, self.b, self.c)

    def conclusion(self):
        return Angle(self.b, self.a, self.d)-Angle(self.d, self.a, self.c)


@register("basic")
class AlphaGeometry13(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def condition(self):
        return NotCollinear(self.a, self.b, self.c), Collinear(self.d, self.b, self.c), Angle(self.b, self.a, self.d) - Angle(self.d, self.a, self.c), Different(self.a, self.b, self.c, self.d), Lt(self.b, self.c), Between(self.d, self.b, self.c)

    def conclusion(self):
        return Length(self.d, self.b)/Length(self.d, self.c)-Length(self.a, self.b)/Length(self.a, self.c)


@register("basic")
class AlphaGeometry14(InferenceRule):
    def __init__(self, o: Point, a: Point, b: Point):
        super().__init__()
        self.o = o
        self.a = a
        self.b = b

    def condition(self):
        return NotCollinear(self.o, self.a, self.b), Length(self.o, self.a)-Length(self.o, self.b), Lt(self.a, self.b)

    def conclusion(self):
        return Angle(self.o, self.a, self.b) - Angle(self.a, self.b, self.o)


@register("basic")
class AlphaGeometry15(InferenceRule):
    def __init__(self, o: Point, a: Point, b: Point):
        super().__init__()
        self.o = o
        self.a = a
        self.b = b

    def condition(self):
        return NotCollinear(self.o, self.a, self.b), Angle(self.o, self.a, self.b) - Angle(self.a, self.b, self.o), Lt(self.a, self.b)

    def conclusion(self):
        return Length(self.o, self.a)-Length(self.o, self.b)


@register("basic")
class AlphaGeometry16a(InferenceRule):
    def __init__(self, o: Point, a: Point, b: Point, c: Point, x: Point):
        super().__init__()
        self.o = o
        self.a = a
        self.b = b
        self.c = c
        self.x = x

    def condition(self):
        return Length(self.o, self.a) - Length(self.o, self.b), Length(self.o, self.a) - Length(self.o, self.c), Perpendicular(self.o, self.a, self.a, self.x), Different(self.o, self.a, self.b, self.c, self.x), SameSide(self.x, self.c, self.a, self.b)

    def conclusion(self):
        return Angle(self.x, self.a, self.b)+Angle(self.a, self.c, self.b)-pi


@register("basic")
class AlphaGeometry16b(InferenceRule):
    def __init__(self, o: Point, a: Point, b: Point, c: Point, x: Point):
        super().__init__()
        self.o = o
        self.a = a
        self.b = b
        self.c = c
        self.x = x

    def condition(self):
        return Length(self.o, self.a) - Length(self.o, self.b), Length(self.o, self.a) - Length(self.o, self.c), Perpendicular(self.o, self.a, self.a, self.x), Different(self.o, self.a, self.b, self.c, self.x), OppositeSide(self.x, self.c, self.a, self.b)

    def conclusion(self):
        return Angle(self.x, self.a, self.b)-Angle(self.a, self.c, self.b)


@register("basic")
class AlphaGeometry17a(InferenceRule):
    def __init__(self, o: Point, a: Point, b: Point, c: Point, x: Point):
        super().__init__()
        self.o = o
        self.a = a
        self.b = b
        self.c = c
        self.x = x

    def condition(self):
        return Length(self.o, self.a) - Length(self.o, self.b), Length(self.o, self.a) - Length(self.o, self.c), Angle(self.x, self.a, self.b)+Angle(self.a, self.c, self.b)-pi, Different(self.o, self.a, self.b, self.c, self.x), Lt(self.a, self.b), SameSide(self.x, self.c, self.a, self.b)

    def conclusion(self):
        return Perpendicular(self.o, self.a, self.a, self.x)


@register("basic")
class AlphaGeometry17b(InferenceRule):
    def __init__(self, o: Point, a: Point, b: Point, c: Point, x: Point):
        super().__init__()
        self.o = o
        self.a = a
        self.b = b
        self.c = c
        self.x = x

    def condition(self):
        return Length(self.o, self.a) - Length(self.o, self.b), Length(self.o, self.a) - Length(self.o, self.c), Angle(self.x, self.a, self.b)-Angle(self.a, self.c, self.b), Different(self.o, self.a, self.b, self.c, self.x), Lt(self.a, self.b), OppositeSide(self.x, self.c, self.a, self.b)

    def conclusion(self):
        return Perpendicular(self.o, self.a, self.a, self.x)


@register("basic")
class AlphaGeometry18a(InferenceRule):
    def __init__(self, o: Point, a: Point, b: Point, c: Point, m: Point):
        super().__init__()
        self.o = o
        self.a = a
        self.b = b
        self.c = c
        self.m = m

    def condition(self):
        return Midpoint(self.m, self.b, self.c), Length(self.o, self.a) - Length(self.o, self.b), Length(self.o, self.a) - Length(self.o, self.c), Different(self.a, self.b, self.c, self.m, self.o), SameSide(self.a, self.o, self.b, self.c)

    def conclusion(self):
        return Angle(self.b, self.a, self.c)-Angle(self.b, self.o, self.m)


@register("basic")
class AlphaGeometry18b(InferenceRule):
    def __init__(self, o: Point, a: Point, b: Point, c: Point, m: Point):
        super().__init__()
        self.o = o
        self.a = a
        self.b = b
        self.c = c
        self.m = m

    def condition(self):
        return Midpoint(self.m, self.b, self.c), Length(self.o, self.a) - Length(self.o, self.b), Length(self.o, self.a) - Length(self.o, self.c), Different(self.a, self.b, self.c, self.m, self.o), OppositeSide(self.a, self.o, self.b, self.c)

    def conclusion(self):
        return Angle(self.b, self.a, self.c) + Angle(self.b, self.o, self.m) - pi


@register("basic")
class AlphaGeometry19a(InferenceRule):
    def __init__(self, o: Point, a: Point, b: Point, c: Point, m: Point):
        super().__init__()
        self.o = o
        self.a = a
        self.b = b
        self.c = c
        self.m = m

    def condition(self):
        return Collinear(self.m, self.b, self.c), Length(self.o, self.a) - Length(self.o, self.b), Length(self.o, self.a) - Length(self.o, self.c), Angle(self.b, self.a, self.c)-Angle(self.b, self.o, self.m), Different(self.o, self.a, self.b, self.c, self.m), SameSide(self.a, self.o, self.b, self.c), Between(self.m, self.b, self.c)

    def conclusion(self):
        return Midpoint(self.m, self.b, self.c)


@register("basic")
class AlphaGeometry19b(InferenceRule):
    def __init__(self, o: Point, a: Point, b: Point, c: Point, m: Point):
        super().__init__()
        self.o = o
        self.a = a
        self.b = b
        self.c = c
        self.m = m

    def condition(self):
        return Collinear(self.m, self.b, self.c), Length(self.o, self.a) - Length(self.o, self.b), Length(self.o, self.a) - Length(self.o, self.c), Angle(self.b, self.o, self.m) + Angle(self.b, self.a, self.c) - pi, Different(self.o, self.a, self.b, self.c, self.m), OppositeSide(self.a, self.o, self.b, self.c), Between(self.m, self.b, self.c)

    def conclusion(self):
        return Midpoint(self.m, self.b, self.c)


@register("basic")
class AlphaGeometry20(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, m: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.m = m

    def condition(self):
        return Midpoint(self.m, self.a, self.c), Perpendicular(self.a, self.b, self.b, self.c), Lt(self.a, self.c)

    def conclusion(self):
        return Length(self.a, self.m)-Length(self.b, self.m)


@register("basic")
class AlphaGeometry21(InferenceRule):
    def __init__(self, o: Point, a: Point, b: Point, c: Point):
        super().__init__()
        self.o = o
        self.a = a
        self.b = b
        self.c = c

    def condition(self):
        return Collinear(self.a, self.o, self.c), NotCollinear(self.c, self.b, self.a), Length(self.o, self.a) - Length(self.o, self.b), Length(self.o, self.a) - Length(self.o, self.c), Lt(self.a, self.c)

    def conclusion(self):
        return Perpendicular(self.a, self.b, self.b, self.c)


@register("basic")
class AlphaGeometry22(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def condition(self):
        return Concyclic(self.a, self.b, self.c, self.d), Parallel(self.a, self.b, self.c, self.d), Lt(self.a, self.b), Lt(self.c, self.d), Lt(self.a, self.c)

    def conclusion(self):
        return Angle(self.a, self.d, self.c)-Angle(self.d, self.c, self.b)


@register("basic")
class AlphaGeometry23(InferenceRule):
    def __init__(self, m: Point, o: Point, a: Point, b: Point):
        super().__init__()
        self.m = m
        self.o = o
        self.a = a
        self.b = b

    def condition(self):
        return Midpoint(self.m, self.a, self.b), Perpendicular(self.o, self.m, self.a, self.b), Lt(self.a, self.b)

    def conclusion(self):
        return Length(self.o, self.a)-Length(self.o, self.b)


@register("basic")
class AlphaGeometry24(InferenceRule):
    def __init__(self, a: Point, b: Point, p: Point, q: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.p = p
        self.q = q

    def condition(self):
        return Length(self.a, self.p)-Length(self.b, self.p), Length(self.a, self.q)-Length(self.b, self.q), Different(self.a, self.b, self.p, self.q), Lt(self.a, self.b), Lt(self.p, self.q)

    def conclusion(self):
        return Perpendicular(self.a, self.b, self.p, self.q)


@register("basic")
class AlphaGeometry25(InferenceRule):
    def __init__(self, a: Point, b: Point, p: Point, q: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.p = p
        self.q = q

    def condition(self):
        return Concyclic(self.a, self.b, self.p, self.q), Length(self.a, self.p)-Length(self.b, self.p), Length(self.a, self.q)-Length(self.b, self.q), Lt(self.p, self.q), Lt(self.a, self.b)

    def conclusion(self):
        return Perpendicular(self.p, self.a, self.a, self.q), Perpendicular(self.p, self.b, self.b, self.q)


@register("basic")
class AlphaGeometry26(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point, m: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.m = m

    def condition(self):
        return Midpoint(self.m, self.a, self.b), Midpoint(self.m, self.c, self.d), Lt(self.a, self.b), Lt(self.c, self.d), Lt(self.a, self.c)

    def conclusion(self):
        return Parallel(self.a, self.c, self.b, self.d), Parallel(self.a, self.d, self.b, self.c)


@register("basic")
class AlphaGeometry27(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point, m: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.m = m

    def condition(self):
        return Midpoint(self.m, self.a, self.b), Parallel(self.a, self.c, self.b, self.d), Parallel(self.a, self.d, self.b, self.c), Lt(self.a, self.b), Lt(self.c, self.d), Not(Collinear(self.a, self.b, self.c)),  Not(Collinear(self.a, self.b, self.d)), Not(Collinear(self.a, self.c, self.d)), Not(Collinear(self.b, self.c, self.d))

    def conclusion(self):
        return Midpoint(self.m, self.c, self.d)


@register("basic")
class AlphaGeometry28(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point, o: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.o = o

    def condition(self):
        return Collinear(self.o, self.a, self.c), Collinear(self.o, self.b, self.d), Length(self.o, self.a)/Length(self.a, self.c)-Length(self.o, self.b)/Length(self.b, self.d), SameSide(self.c, self.d, self.a, self.b), SameSide(self.a, self.b, self.c, self.d), Different(self.a, self.b, self.c, self.d, self.o), Lt(self.a, self.b)

    def conclusion(self):
        return Parallel(self.a, self.b, self.c, self.d)


@register("basic")
class AlphaGeometry29(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c

    def condition(self):
        return Parallel(self.a, self.b, self.a, self.c), Different(self.a, self.b, self.c), Lt(self.b, self.c)

    def conclusion(self):
        return Collinear(self.a, self.b, self.c)


@register("basic")
class AlphaGeometry34(InferenceRule):  # SAS
    def __init__(self, a: Point, b: Point, c: Point, p: Point, q: Point, r: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.p = p
        self.q = q
        self.r = r

    def condition(self):
        return NotCollinear(self.a, self.b, self.c), Length(self.a, self.b)-Length(self.p, self.q), Length(self.b, self.c)-Length(self.q, self.r), Angle(self.a, self.b, self.c) - Angle(self.p, self.q, self.r), Lt(self.a, self.c)

    def degenerate(self):
        return self.a == self.p and self.b == self.q and self.c == self.r

    def conclusion(self):
        return Congruent(self.a, self.b, self.c, self.p, self.q, self.r),

# @register("basic")
# class HLCongruent(InferenceRule): #SAS
#   def __init__(self, a: Point, b: Point, c: Point, p: Point, q: Point, r: Point):
#     super().__init__()
#     self.a = a
#     self.b = b
#     self.c = c
#     self.p = p
#     self.q = q
#     self.r = r

#   def condition(self):
#     return NotCollinear(self.a,self.b,self.c), Angle(self.a,self.b,self.c)-pi/2,Angle(self.p,self.q,self.r)-pi/2, Length(self.a,self.b)-Length(self.p,self.q), Length(self.a,self.c) - Length(self.p,self.r), Lt(self.a,self.c), Lt(self.a,self.p)

#   def degenerate(self):
#     return self.a==self.p and self.b == self.q and self.c == self.r

#   def conclusion(self):
#     return [Congruent(self.a,self.b,self.c,self.p,self.q,self.r)]


@register("basic")
class AlphaGeometry3536(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, p: Point, q: Point, r: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.p = p
        self.q = q
        self.r = r

    def condition(self):
        return NotCollinear(self.a, self.b, self.c), Angle(self.a, self.b, self.c) - Angle(self.p, self.q, self.r), Angle(self.a, self.c, self.b) - Angle(self.p, self.r, self.q), Lt(self.b, self.c)

    def degenerate(self):
        return self.a == self.p and self.b == self.q and self.c == self.r

    def conclusion(self):
        return [Similar(self.a, self.b, self.c, self.p, self.q, self.r)]


@register("basic")
class AlphaGeometry37(InferenceRule):  # ASA
    def __init__(self, a: Point, b: Point, c: Point, p: Point, q: Point, r: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.p = p
        self.q = q
        self.r = r

    def condition(self):
        return NotCollinear(self.a, self.b, self.c), Angle(self.a, self.b, self.c) - Angle(self.p, self.q, self.r), Angle(self.a, self.c, self.b) - Angle(self.p, self.r, self.q), Length(self.b, self.c)-Length(self.q, self.r), Lt(self.b, self.c)

    def degenerate(self):
        return self.a == self.p and self.b == self.q and self.c == self.r

    def conclusion(self):
        return [Congruent(self.a, self.b, self.c, self.p, self.q, self.r)]


@register("basic")
class AlphaGeometry38(InferenceRule):  # AAS
    def __init__(self, a: Point, b: Point, c: Point, p: Point, q: Point, r: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.p = p
        self.q = q
        self.r = r

    def condition(self):
        return NotCollinear(self.a, self.b, self.c), Angle(self.a, self.b, self.c) - Angle(self.p, self.q, self.r), Angle(self.b, self.a, self.c) - Angle(self.q, self.p, self.r), Length(self.b, self.c)-Length(self.q, self.r), Lt(self.b, self.c)

    def degenerate(self):
        return self.a == self.p and self.b == self.q and self.c == self.r

    def conclusion(self):
        return [Congruent(self.a, self.b, self.c, self.p, self.q, self.r)]


@register("basic")
class RTSSA(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, p: Point, q: Point, r: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.p = p
        self.q = q
        self.r = r

    def condition(self):
        return NotCollinear(self.a, self.b, self.c), Angle(self.a, self.b, self.c) - pi/2, Angle(self.p, self.q, self.r)-pi/2, Length(self.a, self.b)-Length(self.p, self.q), Length(self.a, self.c)-Length(self.p, self.r)

    def degenerate(self):
        return self.a == self.p and self.b == self.q and self.c == self.r

    def conclusion(self):
        return [Congruent(self.a, self.b, self.c, self.p, self.q, self.r)]


@register("basic")
class AlphaGeometry40(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, p: Point, q: Point, r: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.p = p
        self.q = q
        self.r = r

    def condition(self):
        return NotCollinear(self.a, self.b, self.c), Length(self.a, self.b)/Length(self.p, self.q)-Length(self.b, self.c)/Length(self.q, self.r), Angle(self.a, self.b, self.c) - Angle(self.p, self.q, self.r), Lt(self.a, self.c)

    def degenerate(self):
        return self.a == self.p and self.b == self.q and self.c == self.r

    def conclusion(self):
        return [Similar(self.a, self.b, self.c, self.p, self.q, self.r)]


@register("basic")
class AlphaGeometry42(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point, m: Point, n: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.m = m
        self.n = n

    def condition(self):
        return Collinear(self.m, self.a, self.d), Parallel(self.a, self.b, self.c, self.d), Collinear(self.n, self.b, self.c), Length(self.m, self.a)/Length(self.m, self.d)-Length(self.n, self.b)/Length(self.n, self.c),  SameSide(self.m, self.n, self.a, self.b),  SameSide(self.m, self.n, self.c, self.d), Different(self.a, self.b, self.c, self.d), Lt(self.a, self.b), Lt(self.a, self.d)

    def conclusion(self):
        return Parallel(self.m, self.n, self.a, self.b)


@register("basic")
class AlphaGeometry43(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point, m: Point, n: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.m = m
        self.n = n

    def condition(self):
        return Collinear(self.m, self.a, self.d), Collinear(self.n, self.b, self.c), Parallel(self.a, self.b, self.m, self.n), Parallel(self.a, self.b, self.d, self.c), Different(self.a, self.b, self.c, self.d, self.m, self.n), Lt(self.a, self.b), Lt(self.a, self.d), Lt(self.d, self.m), Not(Collinear(self.m, self.n, self.a)), Not(Collinear(self.m, self.n, self.d))

    def conclusion(self):
        return Length(self.m, self.a)/Length(self.m, self.d)-Length(self.n, self.b)/Length(self.n, self.c)


@register("basic")
class EqTrapezoid1(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def condition(self):
        return (
            Parallel(self.a, self.b, self.c, self.d),
            SameSide(self.a, self.d, self.b, self.c),
            Length(self.a, self.c) - Length(self.b, self.d),  # diagonals
            Different(self.a, self.b, self.c, self.d),
            Lt(self.a, self.b),
            Lt(self.a, self.c),
            Lt(self.a, self.d)
        )

    def conclusion(self):
        return Length(self.b, self.c) - Length(self.a, self.d), Angle(self.a, self.b, self.c) - Angle(self.b, self.a, self.d), Angle(self.b, self.a, self.c) - Angle(self.a, self.b, self.d)


@register("basic")
class EqTrapezoid2(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def condition(self):
        return (
            Parallel(self.a, self.b, self.c, self.d),
            SameSide(self.a, self.d, self.b, self.c),
            Angle(self.a, self.b, self.c) - Angle(self.b, self.a, self.d),
            Different(self.a, self.b, self.c, self.d),
            Lt(self.a, self.b),
            Lt(self.a, self.c),
            Lt(self.a, self.d)
        )

    def conclusion(self):
        return Length(self.a, self.c) - Length(self.b, self.d), Length(self.b, self.c) - Length(self.a, self.d), Angle(self.b, self.a, self.c) - Angle(self.a, self.b, self.d)


@register("basic")
class EqTrapezoid3(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def condition(self):
        return (
            Parallel(self.a, self.b, self.c, self.d),
            SameSide(self.a, self.d, self.b, self.c),
            Angle(self.b, self.a, self.c) - Angle(self.a, self.b, self.d),
            Different(self.a, self.b, self.c, self.d),
            Lt(self.a, self.b),
            Lt(self.a, self.c),
            Lt(self.a, self.d)
        )

    def conclusion(self):
        return Length(self.a, self.c) - Length(self.b, self.d), Length(self.b, self.c) - Length(self.a, self.d), Angle(self.a, self.b, self.c) - Angle(self.b, self.a, self.d)

"""
# cannot distinguish eqtrapezoid from parallelogram
@register("basic")
class EqTrapezoid4(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def condition(self):
        return (
            Parallel(self.a, self.b, self.c, self.d),
            SameSide(self.a, self.d, self.b, self.c),
            Length(self.b, self.c) - Length(self.a, self.d),  # legs
            Different(self.a, self.b, self.c, self.d),
            Lt(self.a, self.b),
            Lt(self.a, self.c),
            Lt(self.a, self.d)
        )

    def conclusion(self):
        return Length(self.b, self.c) - Length(self.a, self.d), Angle(self.a, self.b, self.c) - Angle(self.b, self.a, self.d), Angle(self.b, self.a, self.c) - Angle(self.a, self.b, self.c)
"""

    
@register("basic")
class SimilarImplication(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point, e: Point, f: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e
        self.f = f

    def condition(self):
        return Similar(self.a, self.b, self.c, self.d, self.e, self.f), Lt(self.a, self.b), Lt(self.b, self.c)

    def degenerate(self):
        return self.a == self.d and self.b == self.e and self.c == self.f

    def conclusion(self):
        return Angle(self.a, self.b, self.c) - Angle(self.d, self.e, self.f), Angle(self.b, self.c, self.a) - Angle(self.e, self.f, self.d), Angle(self.c, self.a, self.b) - Angle(self.f, self.d, self.e),


@register("basic")
class CongruentImplication(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point, e: Point, f: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e
        self.f = f

    def condition(self):
        return Congruent(self.a, self.b, self.c, self.d, self.e, self.f), Lt(self.a, self.b), Lt(self.b, self.c)

    def degenerate(self):
        return self.a == self.d and self.b == self.e and self.c == self.f

    def conclusion(self):
        return Angle(self.a, self.b, self.c) - Angle(self.d, self.e, self.f), Angle(self.b, self.c, self.a) - Angle(self.e, self.f, self.d), Angle(self.c, self.a, self.b) - Angle(self.f, self.d, self.e)


@register("ex")
class BetweenLength(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c

    def condition(self):
        return Between(self.b, self.a, self.c), Lt(self.a, self.c)

    def conclusion(self):
        return Length(self.a, self.b)+Length(self.b, self.c)-Length(self.a, self.c)


@register("ex")  # stronger than basic9
class Perp2Angle(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c

    def condition(self):
        return Perpendicular(self.a, self.b, self.b, self.c), Lt(self.a, self.c)

    def conclusion(self):
        return Angle(self.a, self.b, self.c) - pi/2


@register("ex")
class Perp2Angle2(InferenceRule):  # one point inside triangle
    def __init__(self, a: Point, b: Point, c: Point, d: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def condition(self):
        return Perpendicular(self.a, self.b, self.c, self.d), SameSide(self.a, self.b, self.c, self.d), OppositeSide(self.c, self.d, self.a, self.b), SameSide(self.b, self.c, self.a, self.d), SameSide(self.b, self.d, self.a, self.c), Lt(self.c, self.d)

    def conclusion(self):
        return Angle(self.b, self.a, self.d) + Angle(self.c, self.d, self.a) - pi/2, Angle(self.b, self.a, self.c) + Angle(self.d, self.c, self.a) - pi/2, Angle(self.a, self.b, self.c) - Angle(self.b, self.c, self.d) - pi/2, Angle(self.a, self.b, self.d) - Angle(self.c, self.d, self.b) - pi/2


@register("ex")
class Perp2Angle3(InferenceRule):  # segments cross
    def __init__(self, a: Point, b: Point, c: Point, d: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def condition(self):
        return Perpendicular(self.a, self.b, self.c, self.d), OppositeSide(self.a, self.b, self.c, self.d), OppositeSide(self.c, self.d, self.a, self.b), Lt(self.a, self.b), Lt(self.c, self.d), Lt(self.a, self.c)

    def conclusion(self):
        return Angle(self.b, self.a, self.d) + Angle(self.c, self.d, self.a) - pi/2, Angle(self.b, self.a, self.c) + Angle(self.d, self.c, self.a) - pi/2, Angle(self.b, self.c, self.d) + Angle(self.a, self.b, self.c) - pi/2, Angle(self.a, self.b, self.d) + Angle(self.c, self.d, self.b) - pi/2


@register("ex")
class Angle2Perp(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c

    def condition(self):
        return Angle(self.a, self.b, self.c) - pi/2

    def conclusion(self):
        return Perpendicular(self.a, self.b, self.b, self.c)


@register("ex")
class Angle2Perp2(InferenceRule):  # point b inside triangle
    def __init__(self, a: Point, b: Point, c: Point, d: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def condition(self):
        return SameSide(self.a, self.b, self.c, self.d), OppositeSide(self.c, self.d, self.a, self.b), SameSide(self.b, self.c, self.a, self.d), SameSide(self.b, self.d, self.a, self.c), Angle(self.b, self.a, self.c) + Angle(self.d, self.c, self.a) - pi/2

    def conclusion(self):
        return Perpendicular(self.a, self.b, self.c, self.d)


@register("ex")
class Angle2Perp3(InferenceRule):  # segments cross
    def __init__(self, a: Point, b: Point, c: Point, d: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def condition(self):
        return OppositeSide(self.a, self.b, self.c, self.d), OppositeSide(self.c, self.d, self.a, self.b), Lt(self.a, self.d), Angle(self.b, self.a, self.d) + Angle(self.c, self.d, self.a) - pi/2

    def conclusion(self):
        return Perpendicular(self.a, self.b, self.c, self.d)


@register("ex")
class Angle2Para(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def condition(self):
        return Angle(self.b, self.a, self.c) + Angle(self.a, self.c, self.d) - pi, Not(Collinear(self.a, self.b, self.c)), SameSide(self.b, self.d, self.a, self.c), Lt(self.a, self.c)

    def conclusion(self):
        return Parallel(self.a, self.b, self.c, self.d)


@register("ex")
class Para2Angle(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def condition(self):
        return Parallel(self.a, self.b, self.c, self.d), Not(Collinear(self.a, self.b, self.c)), SameSide(self.b, self.d, self.a, self.c), Lt(self.a, self.c)

    def conclusion(self):
        return Angle(self.b, self.a, self.c) + Angle(self.a, self.c, self.d) - pi


@register("ex")
class DiagramAngle4a(InferenceRule):  # systemE Diagram-angle transfer 4
    def __init__(self, a: Point, b: Point, c: Point, b1: Point, c1: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.b1 = b1
        self.c1 = c1

    def condition(self):
        return Not(Between(self.a, self.c1, self.c)), Not(Between(self.a, self.b1, self.b)), Different(self.a, self.b, self.c, self.b1, self.c1), Not(Collinear(self.a, self.b, self.c)), Collinear(self.a, self.c, self.c1), Collinear(self.b, self.b1, self.a)

    def conclusion(self):
        return Angle(self.b1, self.a, self.c1) - Angle(self.b, self.a, self.c)


@register("ex")
class DiagramAngle4b(InferenceRule):  # systemE Diagram-angle transfer 4
    def __init__(self, a: Point, b: Point, c: Point, b1: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.b1 = b1

    def condition(self):
        return Not(Between(self.a, self.b1, self.b)), Different(self.a, self.b, self.c), Different(self.a, self.b, self.c, self.b1), Not(Collinear(self.a, self.b, self.c)), Collinear(self.b, self.b1, self.a)

    def conclusion(self):
        return Angle(self.b1, self.a, self.c) - Angle(self.b, self.a, self.c)


@register("ex")
# systemE Diagram-angle transfer 2, Angle addition, stronger than basic10
class DiagramAngle2(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def condition(self):
        return SameSide(self.b, self.d, self.c, self.a), SameSide(self.c, self.d, self.b, self.a), Lt(self.b, self.c)

    def conclusion(self):
        return Angle(self.b, self.a, self.c) - Angle(self.d, self.a, self.c) - Angle(self.d, self.a, self.b)


@register("ex")
class TriangleAngles(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c

    def condition(self):
        return Not(Collinear(self.a, self.b, self.c)), Lt(self.a, self.b), Lt(self.b, self.c)

    def conclusion(self):
        return Angle(self.b, self.a, self.c)+Angle(self.c, self.b, self.a)+Angle(self.a, self.c, self.b) - pi


@register("ex")
class FlatAngle(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c

    def condition(self):
        return Collinear(self.a, self.b, self.c), Between(self.b, self.a, self.c), Lt(self.a, self.c)

    def conclusion(self):
        return Angle(self.a, self.b, self.c) - pi


@register("ex")
class FlatAngle2(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def condition(self):
        return Collinear(self.a, self.b, self.c), Between(self.b, self.a, self.c), Lt(self.a, self.c), Not(Collinear(self.d, self.a, self.c)), Different(self.a, self.b, self.c, self.d)

    def conclusion(self):
        return Angle(self.a, self.b, self.d) + Angle(self.c, self.b, self.d) - pi


@register("ex")
class FlatAngle2Collinear(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c

    def condition(self):
        return Angle(self.a, self.b, self.c) - pi, Lt(self.a, self.c)

    def conclusion(self):
        return Collinear(self.a, self.b, self.c)


@register("ex")
class ParaTrans(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point, e: Point, f: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e
        self.f = f

    def condition(self):
        return Parallel(self.a, self.b, self.c, self.d), Parallel(self.a, self.b, self.e, self.f), Lt(self.a, self.b), Lt(self.c, self.d), Lt(self.e, self.f), Lt(self.c, self.e), Different(self.a, self.b, self.c), Different(self.a, self.b, self.e)

    def degenerate(self):
        return self.a == self.c and self.b == self.d or self.a == self.e and self.b == self.f or self.e == self.c and self.f == self.d

    def conclusion(self):
        return Parallel(self.c, self.d, self.e, self.f)


@register("ex")
class CollinearParallel(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c

    def condition(self):
        return Collinear(self.a, self.b, self.c), Lt(self.a, self.b), Lt(self.b, self.c)

    def conclusion(self):
        return Parallel(self.a, self.b, self.b, self.c), Parallel(self.a, self.b, self.a, self.c), Parallel(self.a, self.c, self.b, self.c)


@register("complex")
class RightTriangleTrigonometry(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point):
        super().__init__()
        self.a = a  # Vertex at angle A
        self.b = b  # Right angle at B
        self.c = c  # Vertex at C

    def condition(self):
        return [
            NotCollinear(self.a, self.b, self.c),
            Angle(self.a, self.b, self.c) - pi / 2,  # Right angle at B
            Different(self.a, self.b, self.c),
        ]

    def conclusion(self):
        return [
            sin(Angle(self.b, self.a, self.c)) -
            Length(self.b, self.c) / Length(self.a, self.c),
            cos(Angle(self.b, self.a, self.c)) -
            Length(self.a, self.b) / Length(self.a, self.c),
        ]


@register("complex")
class LawOfSines(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c

    def condition(self):
        return [
            NotCollinear(self.a, self.b, self.c),
            Different(self.a, self.b, self.c),
            Lt(self.a, self.b),
            Lt(self.b, self.c),
            Lt(self.a, self.c)
        ]

    def conclusion(self):
        return [
            sin(Angle(self.a, self.c, self.b)) / Length(self.a, self.b) -
            sin(Angle(self.a, self.b, self.c)) /
            Length(self.a, self.c),
            sin(Angle(self.a, self.b, self.c)) / Length(self.a, self.c) -
            sin(Angle(self.b, self.a, self.c)) /
            Length(self.b, self.c),
            sin(Angle(self.b, self.a, self.c)) / Length(self.b, self.c) -
            sin(Angle(self.a, self.c, self.b)) /
            Length(self.a, self.b)
        ]


@register("complex")
class LawOfCosines(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c

    def condition(self):
        return [
            NotCollinear(self.a, self.b, self.c),
            Different(self.a, self.b, self.c),
            Lt(self.a, self.b),
            Lt(self.a, self.c),
            Lt(self.b, self.c)
        ]

    def conclusion(self):
        return [
            Length(self.b, self.c)**2 - Length(self.a, self.b)**2 - Length(self.a, self.c)**2 + Length(
                self.a, self.b) * Length(self.a, self.c) * 2 * cos(Angle(self.b, self.a, self.c)),
            Length(self.a, self.c)**2 - Length(self.a, self.b)**2 - Length(self.b, self.c)**2 + Length(
                self.a, self.b) * Length(self.b, self.c) * 2 * cos(Angle(self.a, self.b, self.c)),
            Length(self.a, self.b)**2 - Length(self.a, self.c)**2 - Length(self.b, self.c)**2 + Length(
                self.a, self.c) * Length(self.b, self.c) * 2 * cos(Angle(self.a, self.c, self.b))
        ]


# @register('complex')
# class Pythagorean(InferenceRule): # a special case of law of cosines
#     def __init__(self, a: Point, b: Point, c: Point):
#         super().__init__()
#         self.a = a  # Vertex at angle A
#         self.b = b  # Right angle at B
#         self.c = c  # Vertex at C

    # def condition(self):
    #     return [
    #         NotCollinear(self.a, self.b, self.c),
    #         Angle(self.a, self.b, self.c) - pi/2,  # Right angle at B
    #         Different(self.a, self.b, self.c),
    #     ]

#     def conclusion(self):
#         return [
#             (Length(self.a,self.b)**2+Length(self.b,self.c)**2) - Length(self.a,self.c)**2
#         ]


@register('complex')
class AreaEqualsBaseTimesHeight(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def condition(self):

        return [NotCollinear(self.a, self.b, self.c), Different(self.a, self.b, self.c), Perpendicular(self.d, self.a, self.b, self.c), Collinear(self.d, self.b, self.c),
                ]

    def conclusion(self):
        return [Area(self.a, self.b, self.c)-(Length(self.a, self.d)*Length(self.b, self.c))/2]


@register('complex')
class AreaRightTriangle(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c

    def condition(self):
        return [NotCollinear(self.a, self.b, self.c), Angle(self.a, self.b, self.c)-pi/2, Different(self.a, self.b, self.c), Lt(self.a, self.c),]

    def conclusion(self):

        return [Area(self.a, self.b, self.c)-Length(self.a, self.b) * Length(self.b, self.c) / 2]


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

# @register("complex")
# class AreaEqualsBaseHeightSin(InferenceRule):
#     def __init__(self, a: Point, b: Point, c: Point):
#         super().__init__()
#         self.a = a
#         self.b = b
#         self.c = c

#     def condition(self):
#         return [NotCollinear(self.a, self.b, self.c), Different(self.a, self.b, self.c)]

#     def conclusion(self):
#         return [Area(self.a,self.b,self.c)-Length(self.a,self.b)*Length(self.b,self.c)*Function('sin', Angle(self.a,self.b,self.c))/2]


@register("complex")
class ParallelogramArea(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def condition(self):
        return [Parallelogram(self.a, self.b, self.c, self.d), Different(self.a, self.b, self.c, self.d), Lt(self.a, self.b), Lt(self.a, self.c), Lt(self.a, self.d)
                ]

    def conclusion(self):
        return [Area(self.a, self.b, self.c, self.d) - Length(self.a, self.b) * Length(self.b, self.c) * sin(Angle(self.a, self.b, self.c))]


@register("complex")
class TrapezoidArea(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point, e: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e

    def condition(self):

        return [Trapezoid(self.a, self.b, self.c, self.d), Perpendicular(self.a, self.e, self.c, self.d), Collinear(self.e, self.c, self.d), Different(self.a, self.b, self.c, self.d)
                ]

    def conclusion(self):
        return [Area(self.a, self.b, self.c, self.d) - (Length(self.a, self.b) + Length(self.c, self.d)) * Length(self.a, self.e) / 2]


@register("complex")
class RightTrapezoidArea(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def condition(self):
        return [Trapezoid(self.a, self.b, self.c, self.d), Perpendicular(self.a, self.b, self.b, self.c)]

    def conclusion(self):
        return [Area(self.a, self.b, self.c, self.d) - (Length(self.a, self.b) + Length(self.c, self.d)) * Length(self.b, self.c) / 2]


@register("complex")
class Similar4PAreaLengthRatio(InferenceRule):
    # only consider convex polygons
    def __init__(self, a: Point, b: Point, c: Point, d: Point, e: Point, f: Point, g: Point, h: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e
        self.f = f
        self.g = g
        self.h = h

    def degenerate(self):
        return self.a == self.e and self.b == self.f and self.c == self.g and self.d == self.h

    def condition(self):
        return [Similar4P(self.a, self.b, self.c, self.d, self.e, self.f, self.g, self.h), Lt(self.a, self.b), Lt(self.a, self.c), Lt(self.a, self.d), Lt(self.b, self.d), Quadrilateral(self.a, self.b, self.c, self.d), Quadrilateral(self.e, self.f, self.g, self.h)]

    def conclusion(self):
        return [Area(self.a, self.b, self.c, self.d)/Area(self.e, self.f, self.g, self.h)-Length(self.a, self.b)**2 / Length(self.e, self.f)**2,
                Area(self.a, self.b, self.c, self.d)/Area(self.e, self.f, self.g, self.h)-Length(self.b, self.c)**2 / Length(self.f, self.g)**2,
                Area(self.a, self.b, self.c, self.d)/Area(self.e, self.f, self.g, self.h)-Length(self.c, self.d)**2 / Length(self.g, self.h)**2,
                Area(self.a, self.b, self.c, self.d)/Area(self.e, self.f, self.g, self.h)-Length(self.d, self.a)**2 / Length(self.h, self.e)**2]


@register("complex")
class RhombusArea(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def condition(self):
        return [Perpendicular(self.a, self.c, self.b, self.d), Different(self.a, self.b, self.c, self.d),
                Lt(self.a, self.b), Lt(self.a, self.c), Lt(self.a, self.d), OppositeSide(self.a, self.c, self.b, self.d), OppositeSide(self.b, self.d, self.a, self.c)]

    def conclusion(self):
        return [Area(self.a, self.b, self.c, self.d) - Length(self.a, self.c) * Length(self.b, self.d) / 2]


@register("basic")
class InscribedAngleTheorem1(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, o: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.o = o

    def condition(self):
        return [SameSide(self.o, self.b, self.a, self.c), Lt(self.a, self.c), Different(self.a, self.b, self.c, self.o),
                Length(self.o, self.a)-Length(self.o, self.b), Length(self.o, self.b) - Length(self.o, self.c)]

    def conclusion(self):
        return [Angle(self.a, self.b, self.c) - Angle(self.a, self.o, self.c) / 2]


@register("basic")
class InscribedAngleTheorem2(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, o: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.o = o

    def condition(self):
        return [OppositeSide(self.o, self.b, self.a, self.c), Lt(self.a, self.c), Different(self.a, self.b, self.c, self.o),
                Length(self.o, self.a)-Length(self.o, self.b), Length(self.o, self.b) - Length(self.o, self.c)]

    def conclusion(self):
        return [Angle(self.a, self.b, self.c) + Angle(self.a, self.o, self.c) / 2 - pi]


@register("basic")
class MidsegmentTheorem(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point, e: Point, f: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e
        self.f = f

    def condition(self):
        return [Quadrilateral(self.a, self.b, self.c, self.d),
                Parallel(self.a, self.b, self.c, self.d),
                Lt(self.a, self.b), Lt(self.a, self.c), Lt(self.a, self.d),
                Midpoint(self.e, self.a, self.d), Midpoint(self.f, self.b, self.c), ]

    def conclusion(self):
        return [Length(self.e, self.f) - (Length(self.a, self.b) + Length(self.c, self.d)) / 2]

@register("basic")
class IntersectingChordsTheorem(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point, e: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e

    def condition(self):
        return [Concyclic(self.a, self.b, self.c, self.d), Lt(self.a, self.b), Lt(self.c, self.d), Lt(self.a, self.c), Different(self.a, self.b, self.c, self.d, self.e), Collinear(self.e, self.a, self.b), Collinear(self.e, self.c, self.d)]

    def conclusion(self):
        return [Length(self.a, self.e)/Length(self.c, self.e) - Length(self.d, self.e)/Length(self.b, self.e)]

# When one line is tangent to the circle


@register("basic")
class IntersectingChordsTheorem2(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, o: Point, e: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.o = o
        self.e = e

    def condition(self):
        return [Length(self.a, self.o)-Length(self.b, self.o), Length(self.a, self.o)-Length(self.c, self.o), Lt(self.a, self.b), Angle(self.o, self.c, self.e)-pi/2, Collinear(self.a, self.b, self.e), Different(self.a, self.b, self.c, self.o, self.e)]

    def conclusion(self):
        return [Length(self.a, self.e) / Length(self.c, self.e) - Length(self.c, self.e) / Length(self.b, self.e)]

@register("basic")
class AlternateSegmentTheorem(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point, o: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.o = o
        

    def condition(self):
        return [Length(self.a, self.o)-Length(self.b, self.o), Length(self.b, self.o)-Length(self.c, self.o), Different(self.a,self.b,self.c,self.d,self.o), OppositeSide(self.a,self.d, self.b,self.c), Angle(self.o,self.c,self.d)-pi / 2, ]

    def conclusion(self):
        return [Angle(self.b,self.a,self.c)-Angle(self.b,self.c,self.d)]
    

@register("ex")
class MidpointRatio(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c

    def condition(self):
        return Midpoint(self.a, self.b, self.c)

    def conclusion(self):
        return Length(self.a, self.b) - Length(self.b, self.c)/2, Length(self.a, self.c) - Length(self.b, self.c)/2


@register("basic")
class CentroidTheorem(InferenceRule):
    def __init__(self, o: Point, a: Point, b: Point, c: Point, d: Point, e: Point, f: Point, ):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e
        self.f = f
        self.o = o

    def condition(self):
        return [Centroid(self.o, self.a, self.b, self.c, self.d, self.e, self.f), Lt(self.a, self.b), Lt(self.a, self.c), Lt(self.b, self.c)]

    def conclusion(self):
        return [Length(self.o, self.d) / Length(self.a, self.d) - sympy.simplify('1/3'),
                Length(self.o, self.a) / Length(self.a, self.d) - sympy.simplify('2/3'),
                Length(self.o, self.e) / Length(self.b, self.e) - sympy.simplify('1/3'),
                Length(self.o, self.b) / Length(self.b, self.e) - sympy.simplify('2/3'),
                Length(self.o, self.f) / Length(self.c, self.f) - sympy.simplify('1/3'),
                Length(self.o, self.c) / Length(self.c, self.f) - sympy.simplify('2/3'),]

@register("basic")
class AlternateSegmentTheorem(InferenceRule):
    def __init__(self, a: Point, b: Point, c: Point, d: Point, o: Point):
        super().__init__()
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.o = o
        

    def condition(self):
        return [Length(self.a, self.o)-Length(self.b, self.o), Length(self.b, self.o)-Length(self.c, self.o), Different(self.a,self.b,self.c,self.d,self.o), OppositeSide(self.a,self.d, self.b,self.c), Angle(self.o,self.c,self.d)-pi / 2, ]

    def conclusion(self):
        return [Angle(self.b,self.a,self.c)-Angle(self.b,self.c,self.d)]