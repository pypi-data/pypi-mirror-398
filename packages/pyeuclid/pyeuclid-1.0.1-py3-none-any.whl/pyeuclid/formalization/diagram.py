"""Numerical diagram construction and validation for geometric problems."""
# mypy: ignore-errors

from __future__ import annotations

import os
import pickle
import hashlib

from matplotlib import pyplot as plt  # type: ignore[import]

from pyeuclid.formalization.construction_rule import *
from pyeuclid.formalization.numericals import *
from pyeuclid.formalization.utils import *


def hash_constructions_list(constructions_list):
    s = ",".join(str(c) for constructions in constructions_list for c in constructions)
    return hashlib.md5(s.encode('utf-8')).hexdigest()


class Diagram:    
    def __new__(cls, constructions_list:list[list[ConstructionRule]]=None, save_path=None, cache_folder=os.path.join(ROOT_DIR, 'cache'), resample=False):
        """Load from cache if available, otherwise construct a new diagram instance."""
        if not resample and cache_folder is not None:
            if not os.path.exists(cache_folder):
                os.makedirs(cache_folder)
            
            if constructions_list is not None:
                file_name = f"{hash_constructions_list(constructions_list)}.pkl"
                file_path = os.path.join(cache_folder, file_name)
                try:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            instance = pickle.load(f)
                            instance.save_path = save_path
                            instance.save_diagram()
                            return instance
                except:
                    pass
        
        instance = super().__new__(cls)
        return instance
    
    def __init__(self, constructions_list:list[list[ConstructionRule]]=None, save_path=None, cache_folder=os.path.join(ROOT_DIR, 'cache'), resample=False):
        if hasattr(self, 'cache_folder'):
            return
        
        self.points = []
        self.segments = []
        self.circles = []
        
        self.name2point = {}
        self.point2name = {}
        
        self.fig, self.ax = None, None
        
        self.constructions_list = constructions_list
        self.save_path = save_path
        self.cache_folder = cache_folder
        
        if constructions_list is not None:                
            self.construct_diagram()
            
    def clear(self):
        """Reset all stored points, segments, circles, and name mappings."""
        self.points.clear()
        self.segments.clear()
        self.circles.clear()
        
        self.name2point.clear()
        self.point2name.clear()
        
    def show(self):
        """Render the diagram with matplotlib."""
        self.draw_diagram(show=True)
        
    def save_to_cache(self):
        """Persist the diagram to cache if caching is enabled."""
        if self.cache_folder is not None:
            file_name = f"{hash_constructions_list(self.constructions_list)}.pkl"
            file_path = os.path.join(self.cache_folder, file_name)
            with open(file_path, 'wb') as f:
                pickle.dump(self, f)
    
    def add_constructions(self, constructions):
        """Add a new batch of constructions, retrying if degeneracy occurs."""
        for _ in range(MAX_DIAGRAM_ATTEMPTS):
            try:
                self.construct(constructions)
                self.constructions_list.append(constructions)
                return
            except:
                continue
        
        print(f"Failed to add the constructions after {MAX_DIAGRAM_ATTEMPTS} attempts.")
        raise Exception()
            
    def construct_diagram(self):
        """Construct the full diagram from all construction batches, with retries."""
        for _ in range(MAX_DIAGRAM_ATTEMPTS):
            try:
                self.clear()
                for constructions in self.constructions_list:
                    self.construct(constructions)
                self.draw_diagram()
                self.save_to_cache()
                return
            except:
                continue
        
        print(f"Failed to construct a diagram after {MAX_DIAGRAM_ATTEMPTS} attempts.")
        raise Exception()
            
    def construct(self, constructions: list[ConstructionRule]):
        """Apply a single batch of construction rules to extend the diagram."""
        constructed_points = constructions[0].constructed_points()
        if any(construction.constructed_points() != constructed_points for construction in constructions[1:]):
            raise Exception()

        to_be_intersected = []
        for construction in constructions:
            # print(construction.__class__.__name__ + '('+','.join([str(name) for name in construction.arguments()])+')')
            # for c in construction.conditions:
            #     if not self.numerical_check(c):
            #         raise Exception()
            
            to_be_intersected += self.sketch(construction)
                
        new_points = self.reduce(to_be_intersected, self.points)
        
        if check_too_close(new_points, self.points):
            raise Exception()
        
        if check_too_far(new_points, self.points):
            raise Exception()
        
        self.points += new_points
        
        for p, np in zip(constructed_points, new_points):
            self.name2point[p.name] = np
            self.point2name[np] = p.name
        
        for construction in constructions:
            self.draw(new_points, construction)
            
    def numerical_check_goal(self, goal):
        """Check if the current diagram satisfies a goal relation/expression."""
        if isinstance(goal, tuple):
            for g in goal:
                if self.numerical_check(g):
                    return True, g
        else:
            if self.numerical_check(goal):
                return True, goal
        return False, goal
            
    def numerical_check(self, relation):
        """Numerically evaluate whether a relation/expression holds in the diagram."""
        if isinstance(relation, Relation):
            func = globals()['check_' + relation.__class__.__name__.lower()]
            args = [self.name2point[p.name] for p in relation.get_points()]
            return func(args)
        else:
            symbol_to_value = {}
            symbols, symbol_names = parse_expression(relation)
            
            for angle_symbol, angle_name in zip(symbols['Angle'], symbol_names['Angle']):
                angle_value = calculate_angle(*[self.name2point[n] for n in angle_name])
                symbol_to_value[angle_symbol] = angle_value
            
            for length_symbol, length_name in zip(symbols['Length'], symbol_names['Length']):
                length_value = calculate_length(*[self.name2point[n] for n in length_name])
                symbol_to_value[length_symbol] = length_value
            
            evaluated_expr = relation.subs(symbol_to_value)
            if close_enough(float(evaluated_expr.evalf()), 0):
                return True
            else:
                return False

    def sketch(self, construction):
        func = getattr(self, 'sketch_' + construction.__class__.__name__[10:])
        args = [arg if isinstance(arg, float) else self.name2point[arg.name] for arg in construction.arguments()]
        result = func(*args)
        if isinstance(result, list):
            return result
        else:
            return [result]
        
    def sketch_angle_bisector(self, *args: list[Point]) -> Ray:
        """Ray that bisects angle ABC."""
        a, b, c = args
        dist_ab = a.distance(b)
        dist_bc = b.distance(c)
        x = b + (c - b) * (dist_ab / dist_bc)
        m = (a + x) * 0.5
        return Ray(b, m)
    
    def sketch_angle_mirror(self, *args: list[Point]) -> Ray:
        """Mirror of ray BA across BC."""
        a, b, c = args
        ab = a - b
        cb = c - b

        dist_ab = a.distance(b)
        ang_ab = np.arctan2(ab.y / dist_ab, ab.x / dist_ab)
        dist_cb = c.distance(b)
        ang_bc = np.arctan2(cb.y / dist_cb, cb.x / dist_cb)

        ang_bx = 2 * ang_bc - ang_ab
        x = b + Point(np.cos(ang_bx), np.sin(ang_bx))
        return Ray(b, x)
    
    def sketch_circle(self, *args: list[Point]) -> Point:
        """Center of circle through three points."""
        a, b, c = args
        l1 = perpendicular_bisector(a, b)
        l2 = perpendicular_bisector(b, c)
        x = line_line_intersection(l1, l2)
        return x
    
    def sketch_circumcenter(self, *args: list[Point]) -> Point:
        """Circumcenter of triangle ABC."""
        a, b, c = args
        l1 = perpendicular_bisector(a, b)
        l2 = perpendicular_bisector(b, c)
        x = line_line_intersection(l1, l2)
        return x
    
    def sketch_eq_quadrangle(self, *args: list[Point]) -> list[Point]:
        """Randomly sample a quadrilateral with opposite sides equal."""
        a = Point(0.0, 0.0)
        b = Point(1.0, 0.0)

        length = np.random.uniform(0.5, 2.0)
        ang = np.random.uniform(np.pi / 3, np.pi * 2 / 3)
        d = head_from(a, ang, length)

        ang = ang_of(b, d)
        ang = np.random.uniform(ang / 10, ang / 9)
        c = head_from(b, ang, length)
        a, b, c, d = random_rfss(a, b, c, d)
        return [a, b, c, d]
        
    def sketch_eq_trapezoid(self, *args: list[Point]) -> list[Point]:
        """Randomly sample an isosceles trapezoid."""
        a = Point(0.0, 0.0)
        b = Point(1.0, 0.0)
        l = unif(0.5, 2.0)

        height = unif(0.5, 2.0)
        c = Point(0.5 + l / 2.0, height)
        d = Point(0.5 - l / 2.0, height)

        a, b, c, d = random_rfss(a, b, c, d)
        return [a, b, c, d]
    
    def sketch_eq_triangle(self, *args: list[Point]) -> list[Circle]:
        """Circles defining an equilateral triangle on BC."""
        b, c = args
        return [Circle(center=b, radius=b.distance(c)), Circle(center=c, radius=b.distance(c))]
    
    def sketch_eqangle2(self, *args: list[Point]) -> Point:
        """Point X such that angle ABX equals angle XCB."""
        a, b, c = args
        
        ba = b.distance(a)
        bc = b.distance(c)
        l = ba * ba / bc

        if unif(0.0, 1.0) < 0.5:
            be = min(l, bc)
            be = unif(be * 0.1, be * 0.9)
        else:
            be = max(l, bc)
            be = unif(be * 1.1, be * 1.5)

        e = b + (c - b) * (be / bc)
        y = b + (a - b) * (be / l)
        return line_line_intersection(Line(c, y), Line(a, e))
    
    def sketch_eqdia_quadrangle(self, *args) -> list[Point]:
        """Quadrilateral with equal diagonals."""
        m = unif(0.3, 0.7)
        n = unif(0.3, 0.7)
        a = Point(-m, 0.0)
        c = Point(1 - m, 0.0)
        b = Point(0.0, -n)
        d = Point(0.0, 1 - n)

        ang = unif(-0.25 * np.pi, 0.25 * np.pi)
        sin, cos = np.sin(ang), np.cos(ang)
        b = b.rotate(sin, cos)
        d = d.rotate(sin, cos)
        a, b, c, d = random_rfss(a, b, c, d)
        return [a, b, c, d]
        
    def sketch_eqdistance(self, *args) -> Circle:
        """Circle centered at A with radius BC."""
        a, b, c = args
        return Circle(center=a, radius=b.distance(c))
    
    def sketch_eqdistance2(self, *args) -> Circle:
        """Circle centered at A with radius alpha*BC."""
        a, b, c, alpha = args
        return Circle(center=a, radius=alpha*b.distance(c))
    
    def sketch_eqdistance3(self, *args) -> Circle:
        """Circle centered at A with fixed radius alpha."""
        a, alpha = args
        return Circle(center=a, radius=alpha)
    
    def sketch_foot(self, *args) -> Point:
        """Foot of perpendicular from A to line BC."""
        a, b, c = args
        line_bc = Line(b, c)
        tline = a.perpendicular_line(line_bc)
        return line_line_intersection(tline, line_bc)
    
    def sketch_free(self, *args) -> Point:
        """Free point uniformly sampled in a box."""
        return Point(unif(-1, 1), unif(-1, 1))
    
    def sketch_incenter(self, *args) -> Point:
        """Incenter of triangle ABC."""
        a, b, c = args
        l1 = self.sketch_angle_bisector(a, b, c)
        l2 = self.sketch_angle_bisector(b, c, a)
        return line_line_intersection(l1, l2)
    
    def sketch_incenter2(self, *args) -> list[Point]:
        """Incenter plus touch points on each side."""
        a, b, c = args
        i = self.sketch_incenter(a, b, c)
        x = i.foot(Line(b, c))
        y = i.foot(Line(c, a))
        z = i.foot(Line(a, b))
        return [x, y, z, i]
    
    def sketch_excenter(self, *args) -> Point:
        """Excenter opposite B in triangle ABC."""
        a, b, c = args
        l1 = self.sketch_angle_bisector(b, a, c)
        l2 = self.sketch_angle_bisector(a, b, c).perpendicular_line(b)
        return line_line_intersection(l1, l2)
    
    def sketch_excenter2(self, *args) -> list[Point]:
        """Excenter plus touch points on extended sides."""
        a, b, c = args
        i = self.sketch_excenter(a, b, c)
        x = i.foot(Line(b, c))
        y = i.foot(Line(c, a))
        z = i.foot(Line(a, b))
        return [x, y, z, i]
    
    def sketch_centroid(self, *args) -> list[Point]:
        """Mid-segment points and centroid of triangle ABC."""
        a, b, c = args
        x = (b + c) * 0.5
        y = (c + a) * 0.5
        z = (a + b) * 0.5
        i = line_line_intersection(Line(a, x), Line(b, y))
        return [x, y, z, i]
    
    def sketch_intersection_cc(self, *args) -> list[Circle]:
        """Two circles centered at O and W through A."""
        o, w, a = args
        return [Circle(center=o, radius=o.distance(a)), Circle(center=w, radius=w.distance(a))]
    
    def sketch_intersection_lc(self, *args) -> list:
        """Line and circle defined by A,O,B for intersection."""
        a, o, b = args
        return [Line(b, a), Circle(center=o, radius=o.distance(b))]
    
    def sketch_intersection_ll(self, *args) -> Point:
        """Intersection of lines AB and CD."""
        a, b, c, d = args
        l1 = Line(a, b)
        l2 = Line(c, d)
        return line_line_intersection(l1, l2)
    
    def sketch_intersection_lp(self, *args) -> Point:
        a, b, c, m, n = args
        l1 = Line(a,b)
        l2 = self.sketch_on_pline(c, m, n)
        return line_line_intersection(l1, l2)
    
    def sketch_intersection_lt(self, *args) -> Point:
        a, b, c, d, e = args
        l1 = Line(a, b)
        l2 = self.sketch_on_tline(c, d, e)
        return line_line_intersection(l1, l2)
    
    def sketch_intersection_pp(self, *args) -> Point:
        a, b, c, d, e, f = args
        l1 = self.sketch_on_pline(a, b, c)
        l2 = self.sketch_on_pline(d, e, f)
        return line_line_intersection(l1, l2)
    
    def sketch_intersection_tt(self, *args) -> Point:
        a, b, c, d, e, f = args
        l1 = self.sketch_on_tline(a, b, c)
        l2 = self.sketch_on_tline(d, e, f)
        return line_line_intersection(l1, l2)
    
    def sketch_iso_triangle(self, *args) -> list[Point]:
        base = unif(0.5, 1.5)
        height = unif(0.5, 1.5)

        b = Point(-base / 2, 0.0)
        c = Point(base / 2, 0.0)
        a = Point(0.0, height)
        a, b, c = random_rfss(a, b, c)
        return [a, b, c]
    
    def sketch_lc_tangent(self, *args) -> Line:
        a, o = args
        return self.sketch_on_tline(a, a, o)
    
    def sketch_midpoint(self, *args) -> Point:
        a, b = args
        return (a + b) * 0.5
    
    def sketch_mirror(self, *args) -> Point:
        a, b = args
        return b * 2 - a
    
    def sketch_nsquare(self, *args) -> Point:
        a, b = args
        ang = -np.pi / 2
        return a + (b - a).rotate(np.sin(ang), np.cos(ang))
    
    def sketch_on_aline(self, *args) -> Line:
        e, d, c, b, a = args
        ab = a - b
        cb = c - b
        de = d - e

        dab = a.distance(b)
        ang_ab = np.arctan2(ab.y / dab, ab.x / dab)

        dcb = c.distance(b)
        ang_bc = np.arctan2(cb.y / dcb, cb.x / dcb)

        dde = d.distance(e)
        ang_de = np.arctan2(de.y / dde, de.x / dde)

        ang_ex = ang_de + ang_bc - ang_ab
        x = e + Point(np.cos(ang_ex), np.sin(ang_ex))
        return Ray(e, x)
    
    def sketch_on_bline(self, *args) -> Line:
        a, b = args
        m = (a + b) * 0.5
        return m.perpendicular_line(Line(a, b))
    
    def sketch_on_circle(self, *args) -> Circle:
        o, a = args
        return Circle(o, o.distance(a))
    
    def sketch_on_line(self, *args) -> Line:
        a, b = args
        return Line(a, b)
        
    def sketch_on_pline(self, *args) -> Line:
        a, b, c = args
        return a.parallel_line(Line(b, c))
    
    def sketch_on_tline(self, *args) -> Line:
        a, b, c = args
        return a.perpendicular_line(Line(b, c))
    
    def sketch_orthocenter(self, *args) -> Point:
        a, b, c = args
        l1 = self.sketch_on_tline(a, b, c)
        l2 = self.sketch_on_tline(b, c, a)
        return line_line_intersection(l1, l2)
    
    def sketch_parallelogram(self, *args) -> Point:
        a, b, c = args
        l1 = self.sketch_on_pline(a, b, c)
        l2 = self.sketch_on_pline(c, a, b)
        return line_line_intersection(l1, l2)
    
    def sketch_pentagon(self, *args) -> list[Point]:
        points = [Point(1.0, 0.0)]
        ang = 0.0

        for i in range(4):
            ang += (2 * np.pi - ang) / (5 - i) * unif(0.5, 1.5)
            point = Point(np.cos(ang), np.sin(ang))
            points.append(point)

        a, b, c, d, e = points  # pylint: disable=unbalanced-tuple-unpacking
        a, b, c, d, e = random_rfss(a, b, c, d, e)
        return [a, b, c, d, e]
    
    def sketch_psquare(self, *args) -> Point:
        a, b = args
        ang = np.pi / 2
        return a + (b - a).rotate(np.sin(ang), np.cos(ang))
    
    def sketch_quadrangle(self, *args) -> list[Point]:
        a = Point(0.0, 0.0)
        b = Point(1.0, 0.0)

        length = np.random.uniform(0.5, 2.0)
        ang = np.random.uniform(np.pi / 3, np.pi * 2 / 3)
        d = head_from(a, ang, length)

        ang = ang_of(b, d)
        ang = np.random.uniform(ang / 10, ang / 9)
        c = head_from(b, ang, length)
        a, b, c, d = random_rfss(a, b, c, d)
        return [a, b, c, d]
    
    def sketch_r_trapezoid(self, *args) -> list[Point]:
        """Right trapezoid with AB horizontal and AD vertical."""
        a = Point(0.0, 1.0)
        d = Point(0.0, 0.0)
        b = Point(unif(0.5, 1.5), 1.0)
        c = Point(unif(0.5, 1.5), 0.0)
        a, b, c, d = random_rfss(a, b, c, d)
        return [a, b, c, d]
    
    def sketch_r_triangle(self, *args) -> list[Point]:
        """Random right triangle with legs on axes."""
        a = Point(0.0, 0.0)
        b = Point(0.0, unif(0.5, 2.0))
        c = Point(unif(0.5, 2.0), 0.0)
        a, b, c = random_rfss(a, b, c)
        return [a, b, c]
    
    def sketch_rectangle(self, *args) -> list[Point]:
        """Axis-aligned rectangle with random width/height."""
        a = Point(0.0, 0.0)
        b = Point(0.0, 1.0)
        l = unif(0.5, 2.0)
        c = Point(l, 1.0)
        d = Point(l, 0.0)
        a, b, c, d = random_rfss(a, b, c, d)
        return [a, b, c, d]
    
    def sketch_reflect(self, *args) -> Point:
        """Reflect point A across line BC."""
        a, b, c = args
        m = a.foot(Line(b, c))
        return m * 2 - a
    
    def sketch_risos(self, *args) -> list[Point]:
        """Right isosceles triangle."""
        a = Point(0.0, 0.0)
        b = Point(0.0, 1.0)
        c = Point(1.0, 0.0)
        a, b, c = random_rfss(a, b, c)
        return [a, b, c]
    
    def sketch_s_angle(self, *args) -> Ray:
        """Ray at point B making angle alpha with BA."""
        a, b, alpha = args
        ang = alpha / 180 * np.pi
        x = b + (a - b).rotatea(ang)
        return Ray(b, x)
    
    def sketch_segment(self, *args) -> list[Point]:
        """Random segment endpoints in [-1,1] box."""
        a = Point(unif(-1, 1), unif(-1, 1))
        b = Point(unif(-1, 1), unif(-1, 1))
        return [a, b]
    
    def sketch_shift(self, *args) -> Point:
        """Translate C by vector BA."""
        c, b, a = args
        return c + (b - a)
    
    def sketch_square(self, *args) -> list[Point]:
        """Square constructed on segment AB."""
        a, b = args
        c = b + (a - b).rotatea(-np.pi / 2)
        d = a + (b - a).rotatea(np.pi / 2)
        return [c, d]
    
    def sketch_isquare(self, *args) -> list[Point]:
        """Axis-aligned unit square, randomly re-ordered."""
        a = Point(0.0, 0.0)
        b = Point(1.0, 0.0)
        c = Point(1.0, 1.0)
        d = Point(0.0, 1.0)
        a, b, c, d = random_rfss(a, b, c, d)
        return [a, b, c, d]
    
    def sketch_trapezoid(self, *args) -> list[Point]:
        """Random trapezoid with AB // CD."""
        d = Point(0.0, 0.0)
        c = Point(1.0, 0.0)

        base = unif(0.5, 2.0)
        height = unif(0.5, 2.0)
        a = Point(unif(0.2, 0.5), height)
        b = Point(a.x + base, height)
        a, b, c, d = random_rfss(a, b, c, d)
        return [a, b, c, d]
    
    def sketch_triangle(self, *args) -> list[Point]:
        """Random triangle."""
        a = Point(0.0, 0.0)
        b = Point(1.0, 0.0)
        ac = unif(0.5, 2.0)
        ang = unif(0.2, 0.8) * np.pi
        c = head_from(a, ang, ac)
        return [a, b, c]
    
    def sketch_triangle12(self, *args) -> list[Point]:
        """Triangle with side-length ratios near 1:2."""
        b = Point(0.0, 0.0)
        c = Point(unif(1.5, 2.5), 0.0)
        a, _ = circle_circle_intersection(Circle(b, 1.0), Circle(c, 2.0))
        a, b, c = random_rfss(a, b, c)
        return [a, b, c]
    
    def sketch_2l1c(self, *args) -> list[Point]:
        """Intersections of perpendiculars from P to AC/BC with circle centered at P."""
        a, b, c, p = args
        bc, ac = Line(b, c), Line(a, c)
        circle = Circle(p, p.distance(a))

        d, d_ = line_circle_intersection(p.perpendicular_line(bc), circle)
        if bc.diff_side(d_, a):
            d = d_

        e, e_ = line_circle_intersection(p.perpendicular_line(ac), circle)
        if ac.diff_side(e_, b):
            e = e_

        df = d.perpendicular_line(Line(p, d))
        ef = e.perpendicular_line(Line(p, e))
        f = line_line_intersection(df, ef)

        g, g_ = line_circle_intersection(Line(c, f), circle)
        if bc.same_side(g_, a):
            g = g_

        b_ = c + (b - c) / b.distance(c)
        a_ = c + (a - c) / a.distance(c)
        m = (a_ + b_) * 0.5
        x = line_line_intersection(Line(c, m), Line(p, g))
        return [x.foot(ac), x.foot(bc), g, x]
    
    def sketch_e5128(self, *args) -> list[Point]:
        """Problem-specific construction e5128."""
        a, b, c, d = args
        g = (a + b) * 0.5
        de = Line(d, g)

        e, f = line_circle_intersection(de, Circle(c, c.distance(b)))

        if e.distance(d) < f.distance(d):
            e = f
        return [e, g]
    
    def sketch_3peq(self, *args) -> list[Point]:
        """Three-point equidistance construction."""
        a, b, c = args
        ab, bc, ca = Line(a, b), Line(b, c), Line(c, a)

        z = b + (c - b) * np.random.uniform(-0.5, 1.5)

        z_ = z * 2 - c
        l = z_.parallel_line(ca)
        x = line_line_intersection(l, ab)
        y = z * 2 - x
        return [x, y, z]
    
    def sketch_trisect(self, *args) -> list[Point]:
        """Trisect angle ABC."""
        a, b, c = args
        ang1 = ang_of(b, a)
        ang2 = ang_of(b, c)

        swap = 0
        if ang1 > ang2:
            ang1, ang2 = ang2, ang1
            swap += 1

        if ang2 - ang1 > np.pi:
            ang1, ang2 = ang2, ang1 + 2 * np.pi
            swap += 1

        angx = ang1 + (ang2 - ang1) / 3
        angy = ang2 - (ang2 - ang1) / 3

        x = b + Point(np.cos(angx), np.sin(angx))
        y = b + Point(np.cos(angy), np.sin(angy))

        ac = Line(a, c)
        x = line_line_intersection(Line(b, x), ac)
        y = line_line_intersection(Line(b, y), ac)

        if swap == 1:
            return [y, x]
        return [x, y]
    
    def sketch_trisegment(self, *args) -> list[Point]:
        """Trisect segment AB."""
        a, b = args
        x, y = a + (b - a) * (1.0 / 3), a + (b - a) * (2.0 / 3)
        return [x, y]
    
    def sketch_on_dia(self, *args) -> Circle:
        """Circle with diameter AB."""
        a, b = args
        o = (a + b) * 0.5
        return Circle(o, o.distance(a))
    
    def sketch_ieq_triangle(self, *args) -> list[Point]:
        a = Point(0.0, 0.0)
        b = Point(1.0, 0.0)

        c, _ = Circle(a, a.distance(b)).intersect(Circle(b, b.distance(a)))
        return [a, b, c]
    
    def sketch_on_opline(self, *args) -> Ray:
        a, b = args
        return Ray(a, a + a - b)
    
    def sketch_cc_tangent(self, *args) -> list[Point]:
        o, a, w, b = args
        ra, rb = o.distance(a), w.distance(b)

        ow = Line(o, w)
        if close_enough(ra, rb):
            oo = ow.perpendicular_line(o)
            oa = Circle(o, ra)
            x, z = line_circle_intersection(oo, oa)
            y = x + w - o
            t = z + w - o
            return [x, y, z, t]
    
    def sketch_cc_tangent0(self, *args) -> Ray:
        o, a, w, b = args
        return self.sketch_cc_tangent(o, a, w, b)[:2]
    
    def sketch_eqangle3(self, *args) -> list[Point]:
        a, b, d, e, f = args
        de = d.distance(e)
        ef = e.distance(f)
        ab = b.distance(a)
        ang_ax = ang_of(a, b) + ang_between(e, d, f)
        x = head_from(a, ang_ax, length=de / ef * ab)   
        o = self.sketch_circle(a, b, x)
        return Circle(o, o.distance(a))
    
    def sketch_tangent(self, *args) -> list[Point]:
        a, o, b = args
        dia = self.sketch_dia([a, o])
        return list(circle_circle_intersection(Circle(o, o.distance(b)), dia))
    
    def sketch_on_circum(self, *args) -> Circle:
        a, b, c = args
        o = self.sketch_circle(a, b, c)
        return Circle(o, o.distance(a))
    
    def sketch_sameside(self, *args) -> HalfPlane:
        a, b, c = args
        return HalfPlane(a, b, c)
    
    def sketch_opposingsides(self, *args) -> HalfPlane:
        a, b, c = args
        return HalfPlane(a, b, c, opposingsides=True)
    
    def reduce(self, objs, existing_points) -> list[Point]:
        """Reduce intersecting objects into sampled intersection points.

        Filters half-planes, handles point-only cases, samples within half-planes,
        or intersects pairs of essential geometric objects.
        """
        essential_objs = [i for i in objs if not isinstance(i, HalfPlane)]
        halfplane_objs = [i for i in objs if isinstance(i, HalfPlane)]
  
        if all(isinstance(o, Point) for o in objs):
            return objs
  
        elif all(isinstance(o, HalfPlane) for o in objs):
            if len(objs) == 1:
                return objs[0].sample_within_halfplanes(existing_points,[])
            else:
                return objs[0].sample_within_halfplanes(existing_points,objs[1:])

        elif len(essential_objs) == 1:
            if not halfplane_objs:
                return objs[0].sample_within(existing_points)
            else:
                return objs[0].sample_within_halfplanes(existing_points,halfplane_objs)
  
        elif len(essential_objs) == 2:
            a, b = essential_objs
            result = a.intersect(b)
            
            if isinstance(result, Point):
                if halfplane_objs and not all(i.contains(result) for i in halfplane_objs):
                    raise Exception()
                return [result]
            
            a, b = result
            
            if halfplane_objs:
                a_correct_side = all(i.contains(a) for i in halfplane_objs)
                b_correct_side = all(i.contains(b) for i in halfplane_objs)
                
                if a_correct_side and not b_correct_side:
                    return [a]
                elif b_correct_side and not a_correct_side:
                    return [b]
                elif not a_correct_side and not b_correct_side:
                    raise Exception()
                        
            a_close = any([a.close(x) for x in existing_points])
            b_close = any([b.close(x) for x in existing_points])
            
            if a_close and not b_close:
                return [b]
            
            elif b_close and not a_close:
                return [a]
            else:
                return [np.random.choice([a, b])]
    
    def draw(self, new_points, construction):
        func = getattr(self, 'draw_' + construction.__class__.__name__[10:])
        args = [arg if isinstance(arg, float) else self.name2point[arg.name] for arg in construction.arguments()]
        func(*new_points, *args)
    
    def draw_angle_bisector(self, *args):
        x, a, b, c = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(b, x))
    
    def draw_angle_mirror(self, *args):
        x, a, b, c = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(b, x))
    
    def draw_circle(self, *args):
        x, a, b, c = args
        # self.segments.append(Segment(a, x))
        # self.segments.append(Segment(b, x))
        # self.segments.append(Segment(c, x))
        self.circles.append(Circle(x, x.distance(a)))
        
    def draw_circumcenter(self, *args):
        x, a, b, c = args
        # self.segments.append(Segment(a, x))
        # self.segments.append(Segment(b, x))
        # self.segments.append(Segment(c, x))
        self.circles.append(Circle(x, x.distance(a)))
        
    def draw_eq_quadrangle(self, *args):
        a, b, c, d = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(c, d))
        self.segments.append(Segment(d, a))
        
    def draw_eq_trapezoid(self, *args):
        a, b, c, d = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(c, d))
        self.segments.append(Segment(d, a))
        
    def draw_eq_triangle(self, *args):
        x, b, c = args
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(c, x))
        self.segments.append(Segment(x, b))
    
    def draw_eqangle2(self, *args):
        x, a, b, c = args
        self.segments.append(Segment(b, a))
        self.segments.append(Segment(a, x))
        self.segments.append(Segment(c, b))
        self.segments.append(Segment(b, b))
    
    def draw_eqdia_quadrangle(self, *args):
        a, b, c, d = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(c, d))
        self.segments.append(Segment(d, a))
        self.segments.append(Segment(b, d))
        self.segments.append(Segment(a, c))
        
    def draw_eqdistance(self, *args):
        x, a, b, c = args
        self.segments.append(Segment(x, a))
        self.segments.append(Segment(b, c))
    
    def draw_eqdistance2(self, *args):
        x, a, b, c, alpha = args
        self.segments.append(Segment(x, a))
        self.segments.append(Segment(b, c))
        
    def draw_eqdistance2(self, *args):
        x, a, alpha = args
        self.segments.append(Segment(x, a))
    
    def draw_foot(self, *args):
        x, a, b, c = args
        self.segments.append(Segment(x, a))
        self.segments.append(Segment(x, b))
        self.segments.append(Segment(x, c))
        self.segments.append(Segment(b, c))
    
    def draw_free(self, *args):
        x = args
        
    def draw_incenter(self, *args):
        i, a, b, c = args
        x = i.foot(Line(b, c))
        y = i.foot(Line(c, a))
        z = i.foot(Line(a, b))
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(c, a))
        self.circles.append(Circle(p1=x, p2=y, p3=z))
        
    def draw_incenter2(self, *args):
        x, y, z, i, a, b, c = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(c, a))
        self.circles.append(Circle(p1=x, p2=y, p3=z))
    
    def draw_excenter(self, *args):
        i, a, b, c = args
        x = i.foot(Line(b, c))
        y = i.foot(Line(c, a))
        z = i.foot(Line(a, b))
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(c, a))
        self.circles.append(Circle(p1=x, p2=y, p3=z))
        
    def draw_excenter2(self, *args):
        x, y, z, i, a, b, c = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(c, a))
        self.circles.append(Circle(p1=x, p2=y, p3=z))
        
    def draw_centroid(self, *args):
        x, y, z, i, a, b, c = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(c, a))
        self.segments.append(Segment(a, x))
        self.segments.append(Segment(b, y))
        self.segments.append(Segment(c, z))
    
    def draw_intersection_cc(self, *args):
        x, o, w, a = args
        self.segments.append(Segment(o, a))
        self.segments.append(Segment(o, x))
        self.segments.append(Segment(w, a))
        self.segments.append(Segment(w, x))
        self.circles.append(Circle(o, o.distance(a)))
        self.circles.append(Circle(w, w.distance(a)))
    
    def draw_intersection_lc(self, *args):
        x, a, o, b = args
        self.segments.append(Segment(x, a))
        self.segments.append(Segment(x, b))
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(o, b))
        self.segments.append(Segment(o, x))
        self.circles.append(Circle(o, o.distance(b)))
        
    def draw_intersection_ll(self, *args):
        x, a, b, c, d = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(c, d))
        self.segments.append(Segment(a, x))
        self.segments.append(Segment(b, x))
        self.segments.append(Segment(c, x))
        self.segments.append(Segment(d, x))
        
    def draw_intersection_lp(self, *args):
        x, a, b, c, m, n = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(m, n))
        self.segments.append(Segment(a, x))
        self.segments.append(Segment(b, x))
        self.segments.append(Segment(c, x))
        
    def draw_intersection_lp(self, *args):
        x, a, b, c, m, n = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(m, n))
        self.segments.append(Segment(a, x))
        self.segments.append(Segment(b, x))
        self.segments.append(Segment(c, x))
        
    def draw_intersection_lt(self, *args):
        x, a, b, c, d, e = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(d, e))
        self.segments.append(Segment(a, x))
        self.segments.append(Segment(b, x))
        self.segments.append(Segment(c, x))
        
    def draw_intersection_pp(self, *args):
        x, a, b, c, d, e, f = args
        self.segments.append(Segment(a, x))
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(d, x))
        self.segments.append(Segment(e, f))
    
    def draw_intersection_tt(self, *args):
        x, a, b, c, d, e, f = args
        self.segments.append(Segment(a, x))
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(d, x))
        self.segments.append(Segment(e, f))
    
    def draw_iso_triangle(self, *args):
        a, b, c = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(c, a))
        
    def draw_lc_tangent(self, *args):
        x, a, o = args
        self.segments.append(Segment(a, x))
        self.segments.append(Segment(a, o))
        self.circles.append(Circle(o, o.distance(a)))
    
    def draw_midpoint(self, *args):
        x, a, b = args
        self.segments.append(Segment(a, x))
        self.segments.append(Segment(b, x))
    
    def draw_mirror(self, *args):
        x, a, b = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, x))
        
    def draw_nsquare(self, *args):
        x, a, b = args
        self.segments.append(Segment(x, a))
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, x))
    
    def draw_on_aline(self, *args):
        x, a, b, c, d, e = args
        self.segments.append(Segment(e, d))
        self.segments.append(Segment(d, c))
        self.segments.append(Segment(b, a))
        self.segments.append(Segment(a, x))
    
    def draw_on_bline(self, *args):
        x, a, b = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(a, x))
        self.segments.append(Segment(b, x))
    
    def draw_on_circle(self, *args):
        x, o, a = args
        self.segments.append(Segment(o, a))
        self.segments.append(Segment(o, x))
        self.circles.append(Circle(o, o.distance(x)))
        
    def draw_on_line(self, *args):
        x, a, b = args
        self.segments.append(Segment(x, a))
        self.segments.append(Segment(x, b))
        self.segments.append(Segment(a, b))
        
    def draw_on_pline(self, *args):
        x, a, b, c = args
        self.segments.append(Segment(x, a))
        self.segments.append(Segment(b, c))
    
    def draw_on_tline(self, *args):
        x, a, b, c = args
        self.segments.append(Segment(x, a))
        self.segments.append(Segment(b, c))
    
    def draw_orthocenter(self, *args):
        x, a, b, c = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(c, a))
    
    def draw_parallelogram(self, *args):
        x, a, b, c = args
        self.segments.append(Segment(x, a))
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(c, x))
    
    def draw_parallelogram(self, *args):
        x, a, b, c = args
        self.segments.append(Segment(x, a))
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(c, x))
    
    def draw_pentagon(self, *args):
        a, b, c, d, e = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(c, d))
        self.segments.append(Segment(d, e))
        self.segments.append(Segment(e, a))
    
    def draw_psquare(self, *args):
        x, a, b = args
        self.segments.append(Segment(x, a))
        self.segments.append(Segment(a, b))
        
    def draw_quadrangle(self, *args):
        a, b, c, d = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(c, d))
        self.segments.append(Segment(d, a))
    
    def draw_r_trapezoid(self, *args):
        a, b, c, d = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(c, d))
        self.segments.append(Segment(d, a))
    
    def draw_r_triangle(self, *args):
        a, b, c = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(c, a))
        
    def draw_rectangle(self, *args):
        a, b, c, d = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(c, d))
        self.segments.append(Segment(d, a))
    
    def draw_reflect(self, *args):
        x, a, b, c = args
        self.segments.append(Segment(b, c))
    
    def draw_risos(self, *args):
        a, b, c = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(c, a))
    
    def draw_s_angle(self, *args):
        x, a, b, alpha = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, x))
    
    def draw_segment(self, *args):
        a, b = args
        self.segments.append(Segment(a, b))
    
    def draw_s_segment(self, *args):
        a, b, alpha = args
        self.segments.append(Segment(a, b))
        
    def draw_shift(self, *args):
        x, b, c, d = args
        self.segments.append(Segment(x, b))
        self.segments.append(Segment(c, d))
        self.segments.append(Segment(x, c))
        self.segments.append(Segment(b, d))
    
    def draw_square(self, *args):
        x, y, a, b = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, x))
        self.segments.append(Segment(x, y))
        self.segments.append(Segment(y, a))
    
    def draw_isquare(self, *args):
        a, b, c, d = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(c, d))
        self.segments.append(Segment(d, a))
    
    def draw_trapezoid(self, *args):
        a, b, c, d = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(c, d))
        self.segments.append(Segment(d, a))
    
    def draw_triangle(self, *args):
        a, b, c = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(c, a))
    
    def draw_triangle12(self, *args):
        a, b, c = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(c, a))
    
    def draw_2l1c(self, *args):
        x, y, z, i, a, b, c, o = args
        self.segments.append(Segment(a, c))
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(a, o))
        self.segments.append(Segment(b, o))
        
        self.segments.append(Segment(i, x))
        self.segments.append(Segment(i, y))
        self.segments.append(Segment(i, z))
        
        self.segments.append(Segment(c, x))
        self.segments.append(Segment(a, x))
        self.segments.append(Segment(c, y))
        self.segments.append(Segment(b, y))
        self.segments.append(Segment(o, z))
        
        self.circles.append(Circle(i, i.distance(x)))
        self.circles.append(Circle(o, o.distance(a)))
    
    def draw_e5128(self, *args):
        x, y, a, b, c, d = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(c, d))
        self.segments.append(Segment(d, a))
        
        self.segments.append(Segment(a, x))
        self.segments.append(Segment(x, y))
        self.segments.append(Segment(c, x))
    
    def draw_3peq(self, *args):
        x, y, z, a, b, c = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(c, a))
        
        self.segments.append(Segment(a, x))
        self.segments.append(Segment(b, x))
        
        self.segments.append(Segment(a, y))
        self.segments.append(Segment(c, y))
        
        self.segments.append(Segment(c, z))
        self.segments.append(Segment(b, z))
        
        self.segments.append(Segment(x, y))
        self.segments.append(Segment(y, z))
        self.segments.append(Segment(z, x))
    
    def draw_trisect(self, *args):
        x, y, a, b, c = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, c))
        
        self.segments.append(Segment(b, x))
        self.segments.append(Segment(b, y))
        
        self.segments.append(Segment(a, x))
        self.segments.append(Segment(x, y))
        self.segments.append(Segment(y, c))
        
    def draw_trisegment(self, *args):
        x, y, a, b = args
        self.segments.append(Segment(a, x))
        self.segments.append(Segment(x, y))
        self.segments.append(Segment(y, b))
    
    def draw_on_dia(self, *args):
        x, a, b = args
        self.segments.append(Segment(x, a))
        self.segments.append(Segment(x, b))
        
    def draw_ieq_triangle(self, *args):
        a, b, c = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(b, c))
        self.segments.append(Segment(c, a))
    
    def draw_on_opline(self, *args):
        x, a, b = args
        self.segments.append(Segment(a, b))
        self.segments.append(Segment(x, a))
        self.segments.append(Segment(x, b))
    
    def draw_cc_tangent0(self, *args):
        x, y, o, a, w, b = args
        self.segments.append(Segment(o, a))
        self.segments.append(Segment(o, x))
        
        self.segments.append(Segment(w, b))
        self.segments.append(Segment(w, y))
        
        self.segments.append(Segment(x, y))
        
        self.circles.append(Circle(o, o.distance(a)))
        self.circles.append(Circle(w, w.distance(b)))
    
    def draw_cc_tangent(self, *args):
        x, y, z, i, o, a, w, b = args
        self.segments.append(Segment(o, a))
        self.segments.append(Segment(o, x))
        self.segments.append(Segment(o, z))
        
        self.segments.append(Segment(w, b))
        self.segments.append(Segment(w, y))
        self.segments.append(Segment(w, i))
        
        self.segments.append(Segment(x, y))
        self.segments.append(Segment(z, i))
        
        self.circles.append(Circle(o, o.distance(a)))
        self.circles.append(Circle(w, w.distance(b)))
    
    def draw_eqangle3(self, *args):
        x, a, b, d, e, f = args
        self.segments.append(Segment(f, d))
        self.segments.append(Segment(d, e))
        
        self.segments.append(Segment(a, x))
        self.segments.append(Segment(x, b))
    
    def draw_tangent(self, *args):
        x, y, a, o, b = args
        self.segments.append(Segment(o, b))
        self.segments.append(Segment(o, x))
        self.segments.append(Segment(o, y))
        self.segments.append(Segment(a, x))
        self.segments.append(Segment(a, y))
        
        self.circles.append(Circle(o, o.distance(b)))
    
    def draw_on_circum(self, *args):
        x, a, b, c = args
        self.circles.append(Circle(p1=a, p2=b, p3=c))
    
    def draw_sameside(self, *args):
        x, a, b, c = args
    
    def draw_opposingsides(self, *args):
        x, a, b, c = args
        
    def draw_diagram(self, show=False):
        """Draw the current diagram; optionally display the matplotlib figure."""
        imsize = 512 / 100
        self.fig, self.ax = plt.subplots(figsize=(imsize, imsize), dpi=300)
        self.ax.set_facecolor((1.0, 1.0, 1.0))
        
        for segment in self.segments:
            p1, p2 = segment.p1, segment.p2
            lx, ly = (p1.x, p2.x), (p1.y, p2.y)
            self.ax.plot(lx, ly, color='black', lw=1.2, alpha=0.8, ls='-')
        
        for circle in self.circles:
            self.ax.add_patch(
                plt.Circle(
                    (circle.center.x, circle.center.y),
                    circle.radius,
                    color='red',
                    alpha=0.8,
                    fill=False,
                    lw=1.2,
                    ls='-'
                )
            )
        
        for p in self.points:
            self.ax.scatter(p.x, p.y, color='black', s=15)
            self.ax.annotate(self.point2name[p], (p.x+0.015, p.y+0.015), color='black', fontsize=8)
        
        self.ax.set_aspect('equal')
        self.ax.set_axis_off()
        self.fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05, wspace=0, hspace=0)
        xmin = min([p.x for p in self.points])
        xmax = max([p.x for p in self.points])
        ymin = min([p.y for p in self.points])
        ymax = max([p.y for p in self.points])
        x_margin = (xmax - xmin) * 0.1
        y_margin = (ymax - ymin) * 0.1
        
        self.ax.margins(x_margin, y_margin)
        
        self.save_diagram()
        
        if show:
            plt.show()
            
        plt.close(self.fig)
    
    def save_diagram(self):
        if self.save_path is not None:
            parent_dir = os.path.dirname(self.save_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir)
            self.fig.savefig(self.save_path)
        