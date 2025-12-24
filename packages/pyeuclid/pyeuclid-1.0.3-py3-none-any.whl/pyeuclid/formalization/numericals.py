from __future__ import annotations
import math
from pyeuclid.formalization.relation import *

from typing import Any, Optional, Union
import numpy as np
from numpy.random import uniform as unif

ATOM = 0.0001


class Point:
    """Numerical point."""

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __lt__(self, other: Point) -> bool:
        return (self.x, self.y) < (other.x, other.y)

    def __gt__(self, other: Point) -> bool:
        return (self.x, self.y) > (other.x, other.y)

    def __add__(self, p: Point) -> Point:
        return Point(self.x + p.x, self.y + p.y)

    def __sub__(self, p: Point) -> Point:
        return Point(self.x - p.x, self.y - p.y)

    def __mul__(self, f: float) -> Point:
        return Point(self.x * f, self.y * f)

    def __rmul__(self, f: float) -> Point:
        return self * f

    def __truediv__(self, f: float) -> Point:
        return Point(self.x / f, self.y / f)

    def __floordiv__(self, f: float) -> Point:
        div = self / f  # true div
        return Point(int(div.x), int(div.y))

    def __str__(self) -> str:
        return "P({},{})".format(self.x, self.y)
    
    def close(self, point: Point, tol: float = 1e-12) -> bool:
        return abs(self.x - point.x) < tol and abs(self.y - point.y) < tol

    def distance(self, p) -> float:
        if isinstance(p, Line):
            return p.distance(self)
        if isinstance(p, Circle):
            return abs(p.radius - self.distance(p.center))
        dx = self.x - p.x
        dy = self.y - p.y
        return np.sqrt(dx * dx + dy * dy)
    
    def rotatea(self, ang: float) -> Point:
        sinb, cosb = np.sin(ang), np.cos(ang)
        return self.rotate(sinb, cosb)
    
    def rotate(self, sinb: float, cosb: float) -> Point:
        x, y = self.x, self.y
        return Point(x * cosb - y * sinb, x * sinb + y * cosb)
    
    def flip(self) -> Point:
        return Point(-self.x, self.y)
     
    def foot(self, line: Line) -> Point:
        l = line.perpendicular_line(self)
        return line_line_intersection(l, line)

    def perpendicular_line(self, line: Line) -> Line:
        return line.perpendicular_line(self)
    
    def parallel_line(self, line: Line) -> Line:
        return line.parallel_line(self)
    
    def dot(self, other: Point) -> float:
        return self.x * other.x + self.y * other.y
    
    def sign(self, line: Line) -> int:
        return line.sign(self)


class Line:
    """Numerical line."""
    def __init__(self,
          p1: Point = None,
          p2: Point = None,
          coefficients: tuple[int, int, int] = None
    ):        
        a, b, c = coefficients or (
            p1.y - p2.y,
            p2.x - p1.x,
            p1.x * p2.y - p2.x * p1.y,
        )
        
        if a < 0.0 or a == 0.0 and b > 0.0:
            a, b, c = -a, -b, -c
        
        self.coefficients = a, b, c
    
    def same(self, other: Line) -> bool:
        a, b, c = self.coefficients
        x, y, z = other.coefficients
        return close_enough(a * y, b * x) and close_enough(b * z, c * y)
        
    def parallel_line(self, p: Point) -> Line:
        a, b, _ = self.coefficients
        return Line(coefficients=(a, b, -a * p.x - b * p.y))
    
    def perpendicular_line(self, p: Point) -> Line:
        a, b, _ = self.coefficients
        return Line(p, p + Point(a, b))
   
    def intersect(self, obj):
        if isinstance(obj, Line):
            return line_line_intersection(self, obj)

        if isinstance(obj, Circle):
            return line_circle_intersection(self, obj)
    
    def distance(self, p: Point) -> float:
        a, b, c = self.coefficients
        return abs(self(p.x, p.y)) / math.sqrt(a * a + b * b)
    
    def __call__(self, x: Point, y: Point = None) -> float:
        if isinstance(x, Point) and y is None:
            return self(x.x, x.y)
        a, b, c = self.coefficients
        return x * a + y * b + c
    
    def is_parallel(self, other: Line) -> bool:
        a, b, _ = self.coefficients
        x, y, _ = other.coefficients
        return abs(a * y - b * x) < ATOM
    
    def is_perp(self, other: Line) -> bool:
        a, b, _ = self.coefficients
        x, y, _ = other.coefficients
        return abs(a * x + b * y) < ATOM
    
    def diff_side(self, p1: Point, p2: Point) -> Optional[bool]:
        d1 = self(p1.x, p1.y)
        d2 = self(p2.x, p2.y)
        if abs(d1) < ATOM or abs(d2) < ATOM:
            return None
        return d1 * d2 < 0
    
    def same_side(self, p1: Point, p2: Point) -> Optional[bool]:
        d1 = self(p1.x, p1.y)
        d2 = self(p2.x, p2.y)
        if abs(d1) < ATOM or abs(d2) < ATOM:
            return None
        return d1 * d2 > 0
    
    def sign(self, point: Point) -> int:
        s = self(point.x, point.y)
        if s > 0:
            return 1
        elif s < 0:
            return -1
        return 0
    
    def sample_within(self, points: list[Point], n: int = 5) -> list[Point]:
        """Sample a point within the boundary of points."""
        center = sum(points, Point(0.0, 0.0)) * (1.0 / len(points))
        radius = max([p.distance(center) for p in points])
        if close_enough(center.distance(self), radius):
            center = center.foot(self)
        a, b = line_circle_intersection(self, Circle(center.foot(self), radius))
        result = None
        best = -1.0
        for _ in range(n):
            rand = unif(0.0, 1.0)
            x = a + (b - a) * rand
            mind = min([x.distance(p) for p in points])
            if mind > best:
                best = mind
                result = x
        return [result]
    
    def sample_within_halfplanes(self, points: list[Point], halfplanes: list[HalfPlane], n: int = 5) -> list[Point]:
        """Sample points on the line within the intersection of half-plane constraints and near existing points."""
        # Parameterize the line: L(t) = P0 + t * d
        # P0 is a point on the line, d is the direction vector
        # # Get the direction vector (dx, dy) of the line
        a, b, c = self.coefficients
        if abs(a) > ATOM and abs(b) > ATOM:
            # General case: direction vector perpendicular to normal vector (a, b)
            d = Point(-b, a)
        elif abs(a) > ATOM:
            # Vertical line 
            d = Point(0, 1)
        elif abs(b) > ATOM:
            # Horizontal line
            d = Point(1, 0)
        else:
            raise ValueError("Invalid line with zero coefficients")
        
        # Find a point P0 on the line
        
        if abs(a) > ATOM:
            x0 = (-c - b * 0) / a  # Set y = 0
            y0 = 0
        elif abs(b) > ATOM:
            x0 = 0
            y0 = (-c - a * 0) / b  # Set x = 0
        else:
            raise ValueError("Invalid line with zero coefficients")
        
        P0 = Point(x0, y0)
        
        # Project existing points onto the line to get an initial interval
        t_points = []
        for p in points:
            # Vector from P0 to p
            vec = p - P0
            # Project vec onto d
            t = (vec.x * d.x + vec.y * d.y) / (d.x ** 2 + d.y ** 2)
            t_points.append(t)
        if not t_points:
            raise ValueError("No existing points provided for sampling")
        
        # Determine the interval based on existing points
        t_points.sort()
        t_center = sum(t_points) / len(t_points)
        t_radius = max(abs(t - t_center) for t in t_points)
        
        # Define an initial interval around the existing points
        t_init_min = t_center - t_radius
        t_init_max = t_center + t_radius
        
        # Initialize the interval as [t_init_min, t_init_max]
        t_min = t_init_min
        t_max = t_init_max
        
        # Process half-plane constraints
        for hp in halfplanes:
            # For each half-plane, compute K and H0
            a_h, b_h, c_h = hp.line.coefficients
            sign_h = hp.sign  # +1 or -1
            # Compute K = a_h * dx + b_h * dy
            K = a_h * d.x + b_h * d.y
            # Compute H0 = a_h * x0 + b_h * y0 + c_h
            H0 = a_h * P0.x + b_h * P0.y + c_h
            # The half-plane inequality is sign_h * (K * t + H0) >= 0
            S = sign_h
            if abs(K) < ATOM:
                # K is zero
                if S * H0 >= 0:
                    # The entire line satisfies the constraint
                    continue
                else:
                    # The line is entirely outside the half-plane
                    return []
            else:
                t0 = -H0 / K
                if K * S > 0:
                    # Inequality is t >= t0
                    t_min = max(t_min, t0)
                else:
                    # Inequality is t <= t0
                    t_max = min(t_max, t0)
        # After processing all half-planes, check if the interval is valid
        if t_min > t_max:
            # Empty interval
            return []
        else:
            # The intersection is [t_min, t_max]
            # Sample n points within this interval
            result = None
            best = -1.0
            for _ in range(n):
                t = unif(t_min, t_max)
                p = Point(P0.x + t * d.x, P0.y + t * d.y)
                # Calculate the minimum distance to existing points
                mind = min(p.distance(q) for q in points)
                if mind > best:
                    best = mind
                    result = p
            if result is None:
                raise ValueError("Cannot find a suitable point within the constraints")
            return [result]
    

class Ray(Line):
    """Numerical ray."""

    def __init__(self, tail: Point, head: Point):
        self.line = Line(tail, head)
        self.coefficients = self.line.coefficients
        self.tail = tail
        self.head = head
        
    def intersect(self, obj) -> Point:
        if isinstance(obj, (Ray, Line)):
            return line_line_intersection(self.line, obj)
        
        a, b = line_circle_intersection(self.line, obj)
        
        if a.close(self.tail):
            return b
        if b.close(self.tail):
            return a
        
        v = self.head - self.tail
        va = a - self.tail
        vb = b - self.tail
        
        if v.dot(va) > 0:
            return a
        if v.dot(vb) > 0:
            return b
        
        raise Exception()
    
    def sample_within_halfplanes(self, points: list[Point], halfplanes: list[HalfPlane], n: int = 5) -> list[Point]:
        """Sample points on the half-line within the intersection of half-plane constraints and near existing points."""

        # Parameterize the half-line: L(t) = tail + t * d, t >= 0
        d = self.head - self.tail
        d_norm_sq = d.x ** 2 + d.y ** 2
        if d_norm_sq < ATOM:
            raise ValueError("Invalid HalfLine with zero length")

        # Project existing points onto the half-line to get an initial interval
        t_points = []
        for p in points:
            # Vector from tail to p
            vec = p - self.tail
            # Project vec onto d
            t = (vec.x * d.x + vec.y * d.y) / d_norm_sq
            if t >= 0:
                t_points.append(t)
        if not t_points:
            # If no existing points project onto the half-line, define a default interval
            t_init_min = 0
            t_init_max = 1  # For example, length 1 along the half-line
        else:
            # Determine the interval based on existing points
            t_points.sort()
            t_center = sum(t_points) / len(t_points)
            t_radius = max(abs(t - t_center) for t in t_points)
            # Define an initial interval around the existing points
            t_init_min = max(0, t_center - t_radius)
            t_init_max = t_center + t_radius

        # Initialize the interval as [t_init_min, t_init_max]
        t_min = t_init_min
        t_max = t_init_max

        # Process half-plane constraints
        for hp in halfplanes:
            a_h, b_h, c_h = hp.line.coefficients
            sign_h = hp.sign  # +1 or -1

            # Compute K = a_h * dx + b_h * dy
            K = a_h * d.x + b_h * d.y

            # Compute H0 = a_h * tail.x + b_h * tail.y + c_h
            H0 = a_h * self.tail.x + b_h * self.tail.y + c_h

            # The half-plane inequality is sign_h * (K * t + H0) >= 0
            S = sign_h

            if abs(K) < ATOM:
                # K is zero
                if S * H0 >= 0:
                    # The entire half-line satisfies the constraint
                    continue
                else:
                    # The half-line is entirely outside the half-plane
                    return []
            else:
                t0 = -H0 / K
                if K * S > 0:
                    # Inequality is t >= t0
                    if t0 >= 0:
                        t_min = max(t_min, t0)
                    else:
                        t_min = t_min  # t_min remains as is (t >= 0)
                else:
                    # Inequality is t <= t0
                    t_max = min(t_max, t0)
                    if t_max < 0:
                        # Entire interval is before the tail (t < 0), no valid t
                        return []

        # After processing all half-planes, check if the interval is valid
        if t_min > t_max:
            # Empty interval
            return []
        else:
            # The intersection is [t_min, t_max]
            # Ensure t_min >= 0
            t_min = max(t_min, 0)
            if t_min > t_max:
                # No valid t
                return []
            # Sample n points within this interval
            result = None
            best = -1.0
            for _ in range(n):
                t = unif(t_min, t_max)
                p = Point(self.tail.x + t * d.x, self.tail.y + t * d.y)
                # Calculate the minimum distance to existing points
                mind = min(p.distance(q) for q in points)
                if mind > best:
                    best = mind
                    result = p
            if result is None:
                raise ValueError("Cannot find a suitable point within the constraints")
            return [result]

class Segment(Line):
    def __init__(self, p1: Point, p2: Point):
        if p2.x < p1.x or p2.x == p1.x and p2.y < p1.y:
            p1, p2 = p2, p1
        self.line = Line(p1, p2)
        self.coefficients = self.line.coefficients
        self.p1 = p1
        self.p2 = p2

class Circle:
    """Numerical circle."""

    def __init__(
        self,
        center: Optional[Point] = None,
        radius: Optional[float] = None,
        p1: Optional[Point] = None,
        p2: Optional[Point] = None,
        p3: Optional[Point] = None,
    ):
        if not center:
            l12 = perpendicular_bisector(p1, p2)
            l23 = perpendicular_bisector(p2, p3)
            center = line_line_intersection(l12, l23)
            
        if not radius:
            p = p1 or p2 or p3
            radius = center.distance(p)
        
        self.center = center
        self.radius = radius
    
    def intersect(self, obj: Union[Line, Circle]) -> tuple[Point, ...]:
        if isinstance(obj, Line):
            return obj.intersect(self)
        
        if isinstance(obj, Circle):
            return circle_circle_intersection(self, obj)
        
    def sample_within(self, points: list[Point], n: int = 5) -> list[Point]:
        """Sample a point within the boundary of points."""
        result = None
        best = -1.0
        for _ in range(n):
            ang = unif(0.0, 2.0) * np.pi
            x = self.center + Point(np.cos(ang), np.sin(ang)) * self.radius
            mind = min([x.distance(p) for p in points])
            if mind > best:
                best = mind
                result = x
        return [result]


class HalfPlane:
    """Numerical HalfPlane."""

    def __init__(self, a: Point, b: Point, c: Point, opposingsides=False):
        self.line = Line(b, c)
        assert abs(self.line(a)) > ATOM
        self.sign = self.line.sign(a)
        if opposingsides:
            self.sign = -self.sign


def perpendicular_bisector(p1: Point, p2: Point) -> Line:
    midpoint = (p1 + p2) * 0.5
    return Line(midpoint, midpoint + Point(p2.y - p1.y, p1.x - p2.x))


def circle_circle_intersection(c1: Circle, c2: Circle) -> tuple[Point, Point]:
    """Returns a pair of Points as intersections of c1 and c2."""
    # circle 1: (x0, y0), radius r0
    # circle 2: (x1, y1), radius r1
    x0, y0, r0 = c1.center.x, c1.center.y, c1.radius
    x1, y1, r1 = c2.center.x, c2.center.y, c2.radius

    d = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)
    if d == 0:
        raise Exception()

    a = (r0**2 - r1**2 + d**2) / (2 * d)
    h = r0**2 - a**2
    if h < 0:
        raise Exception()
    h = np.sqrt(h)
    x2 = x0 + a * (x1 - x0) / d
    y2 = y0 + a * (y1 - y0) / d
    x3 = x2 + h * (y1 - y0) / d
    y3 = y2 - h * (x1 - x0) / d
    x4 = x2 - h * (y1 - y0) / d
    y4 = y2 + h * (x1 - x0) / d

    return Point(x3, y3), Point(x4, y4)


def solve_quad(a: float, b: float, c: float) -> tuple[float, float]:
    """Solve a x^2 + bx + c = 0."""
    a = 2 * a
    d = b * b - 2 * a * c
    if d < 0:
        return None  # the caller should expect this result.

    y = math.sqrt(d)
    return (-b - y) / a, (-b + y) / a


def line_circle_intersection(line: Line, circle: Circle) -> tuple[Point, Point]:
    """Returns a pair of points as intersections of line and circle."""
    a, b, c = line.coefficients
    r = float(circle.radius)
    center = circle.center
    p, q = center.x, center.y

    if b == 0:
        x = -c / a
        x_p = x - p
        x_p2 = x_p * x_p
        y = solve_quad(1, -2 * q, q * q + x_p2 - r * r)
        if y is None:
            raise Exception()
        y1, y2 = y
        return (Point(x, y1), Point(x, y2))

    if a == 0:
        y = -c / b
        y_q = y - q
        y_q2 = y_q * y_q
        x = solve_quad(1, -2 * p, p * p + y_q2 - r * r)
        if x is None:
            raise Exception()
        x1, x2 = x
        return (Point(x1, y), Point(x2, y))

    c_ap = c + a * p
    a2 = a * a
    y = solve_quad(
        a2 + b * b, 2 * (b * c_ap - a2 * q), c_ap * c_ap + a2 * (q * q - r * r)
    )
    if y is None:
        raise Exception()
    y1, y2 = y

    return Point(-(b * y1 + c) / a, y1), Point(-(b * y2 + c) / a, y2)


def line_line_intersection(l1: Line, l2: Line) -> Point:
    a1, b1, c1 = l1.coefficients
    a2, b2, c2 = l2.coefficients
    # a1x + b1y + c1 = 0
    # a2x + b2y + c2 = 0
    d = a1 * b2 - a2 * b1
    if d == 0:
        raise Exception()
    return Point((c2 * b1 - c1 * b2) / d, (c1 * a2 - c2 * a1) / d)


def head_from(tail: Point, ang: float, length: float = 1) -> Point:
    vector = Point(np.cos(ang) * length, np.sin(ang) * length)
    return tail + vector


def ang_of(tail: Point, head: Point) -> float:
    vector = head - tail
    arctan = np.arctan2(vector.y, vector.x) % (2 * np.pi)
    return arctan


def ang_between(tail: Point, head1: Point, head2: Point) -> float:
    ang1 = ang_of(tail, head1)
    ang2 = ang_of(tail, head2)
    diff = ang1 - ang2
    # return diff % (2*np.pi)
    if diff > np.pi:
        return diff - 2 * np.pi
    if diff < -np.pi:
        return 2 * np.pi + diff
    return diff


def random_rfss(*points: list[Point]) -> list[Point]:
    """Random rotate-flip-scale-shift a point cloud."""
    # center point cloud.
    average = sum(points, Point(0.0, 0.0)) * (1.0 / len(points))
    points = [p - average for p in points]

    # rotate
    ang = unif(0.0, 2 * np.pi)
    sin, cos = np.sin(ang), np.cos(ang)
    # scale and shift
    scale = unif(0.5, 2.0)
    shift = Point(unif(-1, 1), unif(-1, 1))
    points = [p.rotate(sin, cos) * scale + shift for p in points]

    # randomly flip
    if np.random.rand() < 0.5:
        points = [p.flip() for p in points]

    return points


def close_enough(a: float, b: float, tol: float = 1e-12) -> bool:
    return abs(a - b) < tol


def check_too_close(
    newpoints: list[Point], points: list[Point], tol: int = 0.1  # was 0.1
) -> bool:

    if not points:
        return False
    avg = sum(points, Point(0.0, 0.0)) * 1.0 / len(points)
    mindist = min([p.distance(avg) for p in points])
    for p0 in newpoints:
        for p1 in points:
            if p0.distance(p1) < tol * mindist:
                return True
    return False


def check_too_far(newpoints: list[Point], points: list[Point], tol: int = 4) -> bool:
    if len(points) < 2:
        return False
    avg = sum(points, Point(0.0, 0.0)) * 1.0 / len(points)
    maxdist = max([p.distance(avg) for p in points])
    for p in newpoints:
        if p.distance(avg) > maxdist * tol:
            return True
    return False


def calculate_angle(a, b, c):
    ab = Point(a.x - b.x, a.y - b.y)
    bc = Point(c.x - b.x, c.y - b.y)

    dot_product = ab.x * bc.x + ab.y * bc.y
    magnitude_ab = math.sqrt(ab.x ** 2 + ab.y ** 2)
    magnitude_bc = math.sqrt(bc.x ** 2 + bc.y ** 2)

    angle = math.acos(dot_product / (magnitude_ab * magnitude_bc))
    return angle

def calculate_length(a, b):
    return a.distance(b)

def check_collinear(points):
    a, b = points[:2]
    l = Line(a, b)
    for p in points[2:]:
        if abs(l(p.x, p.y)) > ATOM:
            return False
    return True

def check_notcollinear(points):
    return not check_collinear(points)

def check_between(points):
    p, a, b = points
    if check_notcollinear([a, b, p]):
        return False
      
    if a.distance(p) < ATOM or b.distance(p) < ATOM:
      return False

    return min(a.x, b.x)-ATOM <= p.x <= max(a.x, b.x)+ATOM and min(a.y, b.y)-ATOM <= p.y <= max(a.y, b.y)+ATOM

def check_sameside(points):
    a, b, c, d = points
    l = Line(c, d)
    if l.same_side(a, b):
        return True
    else:
        return False
    
def check_oppositeside(points):
    a, b, c, d = points
    l = Line(c, d)
    if l.diff_side(a, b):
        return True
    else:
        return False
    
def check_concyclic(points):
    points = list(set(points))
    a, b, c, *ps = points
    circle = Circle(p1=a, p2=b, p3=c)
    for d in ps:
        if not close_enough(d.distance(circle.center), circle.radius):
            return False
    return True

def check_parallel(points):
    a, b, c, d = points
    ab = Line(a, b)
    cd = Line(c, d)
    if ab.same(cd):
        return False
    return ab.is_parallel(cd)

def check_perpendicular(points):
    a, b, c, d = points
    ab = Line(a, b)
    cd = Line(c, d)
    return ab.is_perp(cd)

def check_midpoint(points):
    a, b, c = points
    return check_collinear(points) and close_enough(a.distance(b), a.distance(c))

def check_similar(points):
    a, b, c, x, y, z = points
    ab = a.distance(b)
    bc = b.distance(c)
    ca = c.distance(a)
    xy = x.distance(y)
    yz = y.distance(z)
    zx = z.distance(x)
    tol = 1e-9
    return close_enough(ab * yz, bc * xy, tol) and close_enough(
        bc * zx, ca * yz, tol
    )

def check_congruent(points):
    a, b, c, x, y, z = points
    ab = a.distance(b)
    bc = b.distance(c)
    ca = c.distance(a)
    xy = x.distance(y)
    yz = y.distance(z)
    zx = z.distance(x)
    tol = 1e-9
    return (
        close_enough(ab, xy, tol)
        and close_enough(bc, yz, tol)
        and close_enough(ca, zx, tol)
    )