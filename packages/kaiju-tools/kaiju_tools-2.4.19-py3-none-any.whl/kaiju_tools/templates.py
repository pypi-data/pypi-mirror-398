"""Data templates and data conditions."""

import abc
from ast import literal_eval
from collections.abc import Container, Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from fnmatch import fnmatch
from numbers import Real
from os import urandom
from random import randint, random
from typing import Any, ClassVar, Union
from uuid import uuid4

from kaiju_tools.encoding import Serializable
from kaiju_tools.mapping import get_field
from kaiju_tools.registry import ClassRegistry


__all__ = [
    "COMPARISON_FUNCTIONS",
    "Condition",
    "Operator",
    "TEMPLATE_FUNCTIONS",
    "OPERATORS",
    "OperatorEval",
    "OperatorFormat",
    "OperatorSelect",
    "OperatorExec",
    "Template",
    "Operators",
]

# >> comparison_functions
COMPARISON_FUNCTIONS = {
    "gt": lambda args: isinstance(args[0], Real) and isinstance(args[1], Real) and args[0] > args[1],
    "lt": lambda args: isinstance(args[0], Real) and isinstance(args[1], Real) and args[0] < args[1],
    "ge": lambda args: isinstance(args[0], Real) and isinstance(args[1], Real) and args[0] >= args[1],
    "le": lambda args: isinstance(args[0], Real) and isinstance(args[1], Real) and args[0] <= args[1],
    "eq": lambda args: args[0] == args[1],
    "ne": lambda args: args[0] != args[1],
    "has": lambda args: isinstance(args[0], Container) and args[1] in args[0],
    "in": lambda args: isinstance(args[1], Container) and args[0] in args[1],
    "match": lambda args: fnmatch(str(args[0]), str(args[1])),
    "like": lambda args: fnmatch(str(args[0]), str(args[1]).replace("%", "*")),
}  #: comparison functions for conditions
# << comparison_functions


# >> agg_functions
AGG_FUNCTIONS = {
    "sum": sum,
    "min": min,
    "max": max,
    "all": all,
    "any": any,
    "len": len,
}  #: aggregate functions for conditions
# << agg_functions


# >> template_functions
TEMPLATE_FUNCTIONS = {
    "true": lambda args: True,
    "str": lambda args: str(args[0]),
    "len": lambda args: len(args[0]),
    "int": lambda args: int(args[0]),
    "bool": lambda args: bool(args[0]),
    "not": lambda args: not bool(args[0]),
    "datetime": lambda args: datetime.fromisoformat(args[0]),
    "date": lambda args: datetime.fromisoformat(args[0]).date(),
    "sum": sum,
    "diff": lambda args: args[0] - args[1],
    "max": max,
    "min": min,
    "all": all,
    "any": any,
    "first": lambda args: args[0],
    "last": lambda args: args[-1],
    "uuid4": lambda args: uuid4(),
    "utcnow": lambda args: datetime.utcnow(),
    "now": lambda args: datetime.now(),
    "now_date": lambda args: datetime.now().date(),
    "timestamp": lambda args: datetime.now().timestamp(),
    "random": lambda args: random(),
    "randint": lambda args: randint(args[0], args[1]),
    "urandom": lambda args: urandom(args[0]),
    "capitalize": lambda args: args[0].capitalize(),
    "upper": lambda args: args[0].upper(),
    "lower": lambda args: args[0].lower(),
    "split": lambda args: args[1].split(args[0]),
    "join": lambda args: args[0].join(args[1:]),
}  #: functions available for template exec (?x:) operator
# << template_functions


_Data = dict[str, Any]
_DataLike = _Data | Iterable[_Data]


@dataclass
class Condition(Serializable):
    """Condition object.

    Check a dictionary structures against a defined condition schema.

    Note that it uses :py:func:`~kaiju_tools.mapping.get_field` to select nested dictionary values and also to aggregate
    dictionary values inside lists.

    Suppose you have a data structure which you want to check against a certaing condition.

    >>> data = {
    ...     'value': True,
    ...     'number': 10,
    ...     'nested': {'value': 42, 'list': [1, 2, 3]},
    ...     'objects': [{'id': 0, 'val': 5}, {'id': 2, 'val': 3}, {'id': 9, 'val': 0}]
    ... }

    You can create a condition object for specific keys and call it for your data.

    >>> cond = Condition({'value': True})
    >>> cond(data)  # ~ data['value'] == True
    True

    Nested values can be accessed using :py:func:`~kaiju_tools.mapping.get_field` syntax.

    >>> Condition({'nested.value': 42})(data)  # ~ data['nested']['value'] == 42
    True

    Similarly, you can aggregate values across a list of object before comparing them to your condition.

    >>> Condition({'objects.id': {'has': 9}})(data)  # ~ [o['id'] for o in data['objects']] == [0, 2, 9]
    True

    If there is no value, `None` will be returned.

    >>> Condition({'not_a_value': None})(data)
    True

    If you want to use a more specific comparison instead of just eq, use a nested {<operator>: <value>} object to
    specify a comparison function from :py:obj:`~kaiju_tools.templates.COMPARISON_FUNCTIONS`.

    >>> Condition({'number': {'gt': 5}})(data)  # ~ data['number'] > 5
    True

    You can combine multiple AND conditions for a single key.

    >>> Condition({'number': {'gt': 5, 'lt': 20}})(data)  # ~ data['number'] > 5 and data['number'] < 20
    True

    Same for multiple keys.

    >>> Condition({'number': {'gt': 5}, 'value': True})(data)  # ~ data['number'] > 5 and data['value'] == True
    True

    Use a list to create an OR condition.

    >>> Condition({'number': [{'gt': 100}, {'lt': 20}]})(data)  # ~ data['number'] > 100 or data['number'] < 20
    True

    Same for multiple keys.

    >>> Condition([{'number': {'gt': 100}}, {'value': True}])(data)  # ~ data['number'] > 100 or data['value'] == True
    True

    Obviously you can combine these features in any way possible to create even more complex conditions.

    >>> Condition([
    ...     {'number': [{'gt': 100}, {'lt': 20, 'gt': 5}]},
    ...     {'value': False}
    ... ])(data)  # ~ data['number'] > 100 or (data['number'] < 20 and data['number'] < 5) or data['value'] == False
    True

    Negation is possible using the nested 'not' operator.

    >>> Condition({'number': {'not': {'ge': 100}}})(data)  # ~ not data['number'] >= 100
    True

    You can make simple aggregations across list values using one of the :py:obj:`~kaiju_tools.templates.AGG_FUNCTIONS`.
    To do this you need to use the nested 'agg' operator.

    >>> Condition({'objects.val': {'agg': {'max': 5}}})(data)  # ~ max([o['val'] for o in data['objects']]) == 5
    True

    Obviously you can use more complex conditions inside aggregations.

    >>> Condition({'objects.key': {'agg': {'len': {'lt': 5}}}})(data)  # ~ len(([o['key'] for o in data['objects']]) < 5
    True

    Aggregations also work for simple lists.

    >>> Condition({'nested.list': {'agg': {'sum': {'ge': 6}}}})(data)  # ~ sum(data['nested']['list']) >= 6
    True

    .. note::

        There's no extensive validation in aggregated and compared values. You must ensure that the data types
        are correct to get consistent and useful results.

    Now you know everything about conditions!
    """

    class Definitions:
        """Conditional operators."""

        operator_not: str = "not"
        operator_agg: str = "agg"
        default_condition: str = "eq"

    functions = COMPARISON_FUNCTIONS
    aggs = AGG_FUNCTIONS

    schema: Union[dict, list[dict], "Template"]
    """Condition schema."""

    def __call__(self, data: _DataLike, /) -> bool:
        """Check condition for provided data."""
        schema = self.schema.fill(data) if isinstance(self.schema, Template) else self.schema
        return self._check_conditions(schema, data)

    def check(self, data: _DataLike, /) -> bool:
        """Check condition for provided data."""
        return self.__call__(data)

    def _check_conditions(self, conditions: _DataLike, data: _DataLike) -> bool:
        if type(conditions) is dict:
            if self.Definitions.operator_not in conditions:
                return not self._check_conditions(conditions[self.Definitions.operator_not], data)
            else:
                return all(
                    (
                        self._check_condition(condition, get_field(data, key, default=None))
                        for key, condition in conditions.items()
                    )
                )
        else:
            return any(self._check_conditions(sub_cond, data) for sub_cond in conditions)

    def _check_condition(self, condition: Any, value: Any, reverse: bool = False) -> bool:
        if type(condition) is dict:
            if self.Definitions.operator_not in condition:
                condition = condition[self.Definitions.operator_not]
                result = self._check_condition(condition, value, reverse=True)
            elif self.Definitions.operator_agg in condition:
                condition = condition[self.Definitions.operator_agg]
                op, condition = next(iter(condition.items()))
                return self._check_condition(condition, self.aggs[op](value))  # noqa ???
            else:
                result = all((self.functions[op]((value, comp)) for op, comp in condition.items()))
        elif type(condition) in {list, tuple}:
            result = any(self._check_condition(sub_cond, value) for sub_cond in condition)
        else:
            result = self.functions[self.Definitions.default_condition]((value, condition))
        return not result if reverse else result


@dataclass
class Operator(abc.ABC):
    """Base operator object.

    All operators must inherit from this base class.
    """

    sign: ClassVar[str]
    template: "Template"
    args: Sequence

    def __post_init__(self):
        self.template = self.template
        if not self.args:
            raise ValueError("No arguments provided")

    def __call__(self, data: dict):
        """Call an operator with dynamic data."""
        args = tuple(self._eval_args(data))
        return self._eval(args, data)

    @abc.abstractmethod
    def _eval(self, args: tuple, data: dict):
        """Evaluate arguments using provided data.

        This method should contain operator-specific evaluation logic.

        :param args: a tuple of already evaluated arguments
        :param data: dynamic data
        :returns: evaluated operator value
        """
        ...

    def _eval_args(self, data: dict):
        for arg in self.args:
            if isinstance(arg, Operator):
                arg = arg(data)
            yield arg


@dataclass
class OperatorSelect(Operator):
    """Selection operator."""

    sign = "s"

    def _eval(self, args: tuple, data: dict):
        arg = args[0]
        if len(args) > 1:
            default = args[1]
            if not isinstance(self.args[1], Operator):
                try:
                    default = literal_eval(default)
                except ValueError:
                    pass  # allow not to use quotes for default strings
        else:
            default = self.template.Definitions.empty_default
        result = get_field(data, arg, delimiter=self.template.Definitions.key_delimiter, default=default)
        return result


@dataclass
class OperatorFormat(Operator):
    """String format operator."""

    class _FormatDict(dict):
        def __init__(self, *args, template: "Template", **kws):
            super().__init__(*args, **kws)
            self.default = template.Definitions.fmt_empty_default
            self.delimiter = template.Definitions.fmt_key_delimiter

        def __getitem__(self, item):
            if item in self:
                return dict.__getitem__(self, item)
            return get_field(self, item, default=self.default, delimiter=self.delimiter)

    sign = "f"

    def _eval(self, args: tuple, data: dict):
        data = self._FormatDict(data, template=self.template)
        result = self.template.Definitions.fmt_join_delimiter.join(arg.format_map(data) for arg in args)
        return result


@dataclass
class OperatorEval(Operator):
    """Literal evaluation operator."""

    sign = "e"

    def _eval(self, args: tuple, data: dict):
        result = tuple(literal_eval(arg) for arg in args)
        if len(args) == 1:
            result = result[0]
        return result


@dataclass
class OperatorExec(Operator):
    """Function execution operator."""

    sign = "x"

    # >> functions_call
    def _eval(self, args: tuple, data: dict):
        func_name, args = args[0], args[1:]
        func_args = []
        for arg, value in zip(self.args[1:], args):
            if isinstance(arg, str):
                value = literal_eval(value)
            func_args.append(value)
        f = self.template.functions[func_name]
        return f(func_args)


class Operators(ClassRegistry[str, type[Operator]]):
    """Operators registry."""

    @classmethod
    def get_base_classes(cls) -> tuple[type, ...]:
        return (Operator,)

    def get_key(self, obj: type[Operator]) -> str:
        return obj.sign


OPERATORS = Operators()
OPERATORS.register_from_namespace(locals())


@dataclass
class Template(Serializable):
    """Template object is able to fill a template with arbitrary data.

    Examples
    ________

    Basic templating:

    >>> t = Template({
    ... 'value': '[test]',
    ... 'values': ['[inner.value]', '[inner.value]'],
    ... 'default': '[unknown:42]',
    ... 'default_str': '[unknown:"test"]',
    ... 'default_op': '[unknown:[!x:bool:0]]'
    ... })
    >>> t({'test': 42, 'inner': {'value': 41}})
    {'value': 42, 'values': (41, 41), 'default': 42, 'default_str': 'test', 'default_op': False}

    Nested templates:

    >>> t = Template('[[inner.key]]')
    >>> t({'inner': {'key': 'me'}, 'me': 'dogs'})
    'dogs'

    Eval:

    >>> t = Template('[!e:[key]]')
    >>> t({'key': 'True'})
    True

    Format:

    >>> t = Template('[!f:{obj-name} price is {obj-price}]')
    >>> t({'obj': {'name': 'dogs', 'price': 42}})
    'dogs price is 42'

    Format join:

    >>> t = Template('[!f:this is {obj_1}:and this is {obj_2}]')
    >>> t({'obj_1': 'dogs', 'obj_2': 'cats'})
    'this is dogs,and this is cats'

    Functions:

    >>> t = Template({'all': '[!x:all:[a]:[b]:0]', 'any': '[!x:any:[a]:[b]:0]'})
    >>> t({'a': 1, 'b': 2})
    {'all': False, 'any': True}

    Nested functions:

    >>> t = Template('[!x:sum:[a]:[!x:int:[b]]:0]')
    >>> t({'a': 1, 'b': 3.14})
    4

    Quotation:

    >>> t = Template("[!f:`[{obj-name}]: {obj-price}`]")
    >>> t({'obj': {'name': 'dogs', 'price': 42}})
    '[dogs]: 42'

    """

    class Definitions:
        """Template definitions."""

        operator_brackets: str = "[]"
        operator_sign: str = "!"
        operator_delimiter: str = ":"
        key_delimiter: str = "."
        fmt_key_delimiter: str = "-"
        empty_default: Exception | str = KeyError
        fmt_empty_default: Exception | str = "???"
        fmt_join_delimiter: str = ","
        default_operator: str = "s"
        escape_quote = "`"

    functions = TEMPLATE_FUNCTIONS
    operators = OPERATORS

    schema: dict | list | tuple | str
    """Template schema."""

    def __post_init__(self):
        keys = []
        self._schema = self._parse_value(self.schema, keys)
        self.keys = frozenset(keys)  #: set of (potentially) used data keys

    def __call__(self, data: _DataLike, /):
        """Fill the template with dynamic data."""
        return self._fill_value(self._schema, data)

    def fill(self, data: _DataLike, /):
        """Fill the template with dynamic data."""
        return self.__call__(data)

    def _fill_value(self, value, data: dict):
        if isinstance(value, dict):
            return {k: self._fill_value(v, data) for k, v in value.items()}
        elif isinstance(value, Iterable) and not isinstance(value, str):
            return tuple(self._fill_value(v, data) for v in value)
        elif isinstance(value, Operator):
            return value(data)
        else:
            return value

    def _parse_value(self, value, keys: list[str], key: str = None):
        if isinstance(value, dict):
            value = {k: self._parse_value(v, keys, key=k) for k, v in value.items()}
        elif isinstance(value, str):
            value = self._parse_string(value, keys, key=key)
        elif isinstance(value, Iterable):
            value = tuple(self._parse_value(v, keys, key=key) for v in value)
        return value

    def _parse_string(self, s: str, keys: list[str], key: str = None) -> Union["Operator", str]:
        if not s:
            return s

        bl, br = self.Definitions.operator_brackets
        bls, blr = s[0] == bl, s[-1] == br

        if not bls and not blr:
            if s[0] == self.Definitions.escape_quote and s[-1] == self.Definitions.escape_quote:
                s = s[1:-1]
            return s
        elif not bls or not blr:
            raise ValueError(f"Unbalanced brackets in template: key={key}, value={s}.")

        s = s[1:-1]
        counter = 0
        x = 0
        args = []
        quoted = False

        for n, v in enumerate(s):
            if v == self.Definitions.escape_quote:
                quoted = not quoted
            elif v == bl and not quoted:
                counter += 1
            elif v == br and not quoted:
                counter -= 1
            if v == self.Definitions.operator_delimiter and not quoted:
                if counter == 0:
                    args.append(self._parse_string(s[x:n], keys, key=key))
                    x = n + 1

        s = s[x : len(s)]  # noqa
        if s:
            args.append(self._parse_string(s, keys, key=key))

        if isinstance(args[0], str) and args[0].startswith(self.Definitions.operator_sign):
            op = args[0][1:]
            args = args[1:]
        else:
            op = self.Definitions.default_operator

        op = self.operators[op](template=self, args=args)  # noqa pycharm
        if op.sign == OperatorSelect.sign:
            keys.extend(arg for arg in args if type(arg) is str)
        return op
