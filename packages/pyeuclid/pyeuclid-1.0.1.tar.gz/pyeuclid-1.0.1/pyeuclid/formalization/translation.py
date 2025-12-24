"""Parsing utilities for benchmark text descriptions into constructions/goals."""

from collections import Counter

from pyeuclid.formalization.relation import *
from pyeuclid.formalization.construction_rule import *
from pyeuclid.formalization.utils import is_float


def get_constructions_list_from_text(text):
    """Parse the constructions section of a text instance into rule objects.

    Args:
        text (str): Full benchmark line containing constructions and goal separated by ' ? '.

    Returns:
        list[list[ConstructionRule]]: Nested list of construction batches.
    """
    parts = text.split(' ? ')
    constructions_text_list = parts[0].split('; ')
    constructions_list = []
    
    for constructions_text in constructions_text_list:
        constructions_text = constructions_text.split(' = ')[1]
        construction_text_list = constructions_text.split(', ')
        constructions = []
        for construction_text in construction_text_list:
            construction_text = construction_text.split(' ')
            rule_name = construction_text[0]
            arg_names = [name.replace('_', '') for name in construction_text[1:]]
            rule = globals()['construct_'+rule_name]
            args = [float(arg_name) if is_float(arg_name) else Point(arg_name) for arg_name in arg_names]
            construction = rule(*args)
            constructions.append(construction)
        constructions_list.append(constructions)
    
    return constructions_list

def get_goal_from_text(text):
    """Parse the goal portion of a text instance into a Relation or expression.

    Args:
        text (str): Full benchmark line containing constructions and goal.

    Returns:
        Relation | sympy.Expr | tuple[Relation, Relation] | None: Parsed goal or None.
    """
    parts = text.split(' ? ')
    goal_text = parts[1] if len(parts) > 1 else None
    goal = None
    if goal_text:
        goal_text = goal_text.split(' ')
        goal_name = goal_text[0]
        arg_names = [name.replace('_', '') for name in goal_text[1:]]
        args = [Point(arg_name) for arg_name in arg_names]
        if goal_name == 'cong':
            goal = Length(*args[:2]) - Length(*args[2:])
        elif goal_name == 'cyclic':
            goal = Concyclic(*args)
        elif goal_name == 'coll':
            goal = Collinear(*args)
        elif goal_name == 'perp':
            goal = Perpendicular(*args)
        elif goal_name == 'para':
            goal = Parallel(*args)
        elif goal_name == 'eqratio':
            goal = Length(*args[:2])/Length(*args[2:4]) - Length(*args[4:6])/Length(*args[6:8])
        elif goal_name == 'eqangle':
            def extract_angle(points):
                count = Counter(points)
                repeating = next(p for p, c in count.items() if c == 2)
                singles = [p for p, c in count.items() if c == 1]
                return singles[0], repeating, singles[1]
            angle1 = Angle(*extract_angle(args[:4]))
            angle2 = Angle(*extract_angle(args[4:]))
            # The goal may involve either equal angles or supplementary angles
            goal = (angle1 - angle2, angle1 + angle2 - pi)
        elif goal_name == 'midp':
            goal = Midpoint(*args)
        elif goal_name == 'simtri':
            goal = Similar(*args)
        elif goal_name == 'contri':
            goal = Congruent(*args)
    
    return goal


def parse_texts_from_file(file_name):
    """Load every other line from a benchmark file as a problem description.

    Args:
        file_name (str): Path to benchmark text file.

    Returns:
        list[str]: Problem description strings.
    """
    with open(file_name, "r") as f:
        lines = f.readlines()
    
    texts = [lines[i].strip() for i in range(1, len(lines), 2)]
    return texts
            