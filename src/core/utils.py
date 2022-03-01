
import ast
import copy
import functools
import inspect
import re

from collections import OrderedDict
from itertools import groupby
from typing import Any, Callable, Dict, Sequence, Tuple


def flatten(l):
    if l is None:
        return None
    return [item for sublist in l for item in sublist]


def rgetattr(obj, attr, *args):
    """
    Recursive getattr function.
    """
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return functools.reduce(_getattr, [obj] + attr.split('.'))


def rget(obj, attr, *args, default=None):
    """
    Recursive dict get function.
    """
    get_from_dict = dict.get

    def _get(obj, attr, *args):
        if obj:
            return get_from_dict(obj, attr, *args)
        return default
    return functools.reduce(_get, [obj] + attr.split('.'))


def get_index_or_default(item, order, default=9999):
    try:
        return order.index(item)
    except ValueError:
        return default


def inherit_from(Child, Parent, persist_meta=False):
    """Return a class that is equivalent to Child(Parent) including Parent bases."""
    PersistMeta = copy(Child.Meta) if hasattr(Child, 'Meta') else None

    if persist_meta:
        Child.Meta = PersistMeta

    # Prepare bases
    child_bases = inspect.getmro(Child)
    parent_bases = inspect.getmro(Parent)
    bases = tuple([item for item in parent_bases if item not in child_bases]) + child_bases

    # Construct the new return type
    try:
        Child = type(Child.__name__, bases, Child.__dict__.copy())
    except AttributeError as e:
        if str(e) == 'Meta':
            raise AttributeError('Attribute Error in graphene library. Try setting persist_meta=True in the inherit_from method call.')
        raise e
    except TypeError as e:
        e.message = f"Likely a meta class mismatch. {type(Child)} and {type(Parent)} not compatible for inheritance."
        raise e

    if persist_meta:
        Child.Meta = PersistMeta

    return Child


def eval_or_none(expression):
    """Safely evaluate a python expression including strings and None"""
    if type(expression) is not str:
        return expression
    elif not expression:
        return None
    elif expression in ('True', 'False'):
        return ast.literal_eval(expression)
    elif re.match(r'^[a-zA-Z0-9_-]+$', expression):
        return str(expression)
    else:
        return ast.literal_eval(expression)


def where(iterable, default=None, **conditions):
    """For condition a=1 return the first item in iterable where item.a==1."""
    conditions = {key.replace('__', '.'): val for key, val in conditions.items()}
    for item in iterable:
        for attr, val in conditions.items():
            if rgetattr(item, attr, None) != val:
                break
        else:
            return item

    return default


def aggregate_to_dict(
    values: Sequence[Tuple[Any, ...]], idx: int, fnc: Callable[..., Any] = sum
) -> Dict[Any, Any]:
    """
    Takes a list of lists, groups by idx and aggregates by fnc

    Example: [('a', 1, 10), ('b', 2, 3), ('a', 2, 20)] -> {'a': [3, 30], 'b': [2, 3]}
    """
    index_function = lambda x: x[idx]
    if len(values[0]) == 2:  # We assume all values have same length
        return {key: fnc(item[1] for item in group) for key, group in groupby(
            sorted(values, key=index_function), key=index_function
        )}

    indices = list(range(len(values[0])))
    indices.pop(idx)
    grouped = {key: [[item[i] for i in indices] for item in group] for key, group in groupby(
        sorted(values, key=index_function), key=index_function
    )}

    return {key: [fnc(item[i] for item in group) for i in range(len(group[0]))] for key, group in grouped.items()}


def decapitalize(string):
    return string[0].lower() + string[1:]


def group_by(data, attribute):

    def _get_final_attribute(item, attributes):
        attributes = attributes.split('.')
        out = getattr(item, attributes[0])

        for attribute in attributes[1:]:
            out = getattr(out, attribute)
        return out

    out = OrderedDict()

    for item in data:
        if type(attribute) == str:
            key = _get_final_attribute(item, attribute)
            out[key] = out.get(key, []) + [item]
        if type(attribute) == int:
            key = item[attribute]
            item = item[:attribute] + item[attribute + 1:]
            out[key] = out.get(key, []) + [item]
    return out


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
