# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: typing.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

"""\nThe typing module: Support for gradual typing as defined by PEP 484 and subsequent PEPs.\n\nAmong other things, the module includes the following:\n* Generic, Protocol, and internal machinery to support generic aliases.\n  All subscripted types like X[int], Union[int, str] are generic aliases.\n* Various \"special forms\" that have unique meanings in type annotations:\n  NoReturn, Never, ClassVar, Self, Concatenate, Unpack, and others.\n* Classes whose instances can be type arguments to generic classes and functions:\n  TypeVar, ParamSpec, TypeVarTuple.\n* Public helper functions: get_type_hints, overload, cast, final, and others.\n* Several protocols to support duck-typing:\n  SupportsFloat, SupportsIndex, SupportsAbs, and others.\n* Special types: NewType, NamedTuple, TypedDict.\n* Deprecated wrapper submodules for re and io related types.\n* Deprecated aliases for builtin types and collections.abc ABCs.\n\nAny name not present in __all__ is an implementation detail\nthat may be changed without notice. Use at your own risk!\n"""
from abc import abstractmethod, ABCMeta
import collections
from collections import defaultdict
import collections.abc
import copyreg
import contextlib
import functools
import operator
import re as stdlib_re
import sys
import types
import warnings
from types import WrapperDescriptorType, MethodWrapperType, MethodDescriptorType, GenericAlias
from _typing import _idfunc, TypeVar, ParamSpec, TypeVarTuple, ParamSpecArgs, ParamSpecKwargs, TypeAliasType, Generic
__all__ = ['Annotated', 'Any', 'Callable', 'ClassVar', 'Concatenate', 'Final', 'ForwardRef', 'Generic', 'Literal', 'Optional', 'ParamSpec', 'Protocol', 'Tuple', 'Type', 'TypeVar', 'TypeVarTuple', 'Union', 'AbstractSet', 'ByteString', 'Container', 'ContextManager', 'Hashable', 'ItemsView', 'Iterable', 'Iterator', 'KeysView', 'Mapping', 'MappingView', 'MutableMapping', 'MutableSequence', 'MutableSet', 'Sequence', 'Sized', 'ValuesView', 'Awaitable', 'AsyncIterator', 'AsyncIterable', 'Coroutine', 'Collection', 'AsyncGenerator', 'AsyncContextManager', 'Reversible', 'SupportsAbs', 'SupportsBytes', 'SupportsComplex', 'SupportsFloat', 'SupportsIndex', 'SupportsInt', 'SupportsRound', 'ChainMap', 'Counter',

def _type_convert(arg, module=None, *, allow_special_forms=False):
    """For converting None to type(None), and strings to ForwardRef."""  # inserted
    if arg is None:
        return type(None)
    if isinstance(arg, str):
        return ForwardRef(arg, module=module, is_class=allow_special_forms)
    return arg

def _type_check(arg, msg, is_argument=True, module=None, *, allow_special_forms=False):
    """Check that the argument is a type, and return it (internal helper).\n\n    As a special case, accept None and return type(None) instead. Also wrap strings\n    into ForwardRef instances. Consider several corner cases, for example plain\n    special forms like Union are not valid, while Union[int, str] is OK, etc.\n    The msg argument is a human-readable error message, e.g.::\n\n        \"Union[arg, ...]: arg should be a type.\"\n\n    We append the repr() of the actual value (truncated to 100 chars).\n    """  # inserted
    invalid_generic_forms = (Generic, Protocol)
    if not allow_special_forms:
        invalid_generic_forms += (ClassVar,)
        if is_argument:
            invalid_generic_forms += (Final,)
    arg = _type_convert(arg, module=module, allow_special_forms=allow_special_forms)
    if isinstance(arg, _GenericAlias) and arg.__origin__ in invalid_generic_forms:
        raise TypeError(f'{arg} is not valid as type argument')
    if arg in (Any, LiteralString, NoReturn, Never, Self, TypeAlias):
        return arg
    if allow_special_forms and arg in (ClassVar, Final):
        return arg
    if isinstance(arg, _SpecialForm) or arg in (Generic, Protocol):
        raise TypeError(f'Plain {arg} is not valid as type argument')
    if type(arg) is tuple:
        raise TypeError(f"{msg} Got {arg!r}.")
    return arg

def _is_param_expr(arg):
    return arg is ... or isinstance(arg, (tuple, list, ParamSpec, _ConcatenateGenericAlias))

def _should_unflatten_callable_args(typ, args):
    """Internal helper for munging collections.abc.Callable\'s __args__.\n\n    The canonical representation for a Callable\'s __args__ flattens the\n    argument types, see https://github.com/python/cpython/issues/86361.\n\n    For example::\n\n        >>> import collections.abc\n        >>> P = ParamSpec(\'P\')\n        >>> collections.abc.Callable[[int, int], str].__args__ == (int, int, str)\n        True\n        >>> collections.abc.Callable[P, str].__args__ == (P, str)\n        True\n\n    As a result, if we need to reconstruct the Callable from its __args__,\n    we need to unflatten it.\n    """  # inserted
    return typ.__origin__ is collections.abc.Callable and (not (len(args) == 2 and _is_param_expr(args[0])))

def _type_repr(obj):
    """Return the repr() of an object, special-casing types (internal helper).\n\n    If obj is a type, we return a shorter version than the default\n    type.__repr__, based on the module and qualified name, which is\n    typically enough to uniquely identify a type.  For everything\n    else, we fall back on repr(obj).\n    """  # inserted
    if isinstance(obj, type):
        if obj.__module__ == 'builtins':
            return obj.__qualname__
        return f'{obj.__module__}.{obj.__qualname__}'
    if obj is ...:
        return '...'
    if isinstance(obj, types.FunctionType):
        return obj.__name__
    if isinstance(obj, tuple):
        return '[' + ', '.join((_type_repr(t) for t in obj)) + ']'
    return repr(obj)

def _collect_parameters(args):
    """Collect all type variables and parameter specifications in args\n    in order of first appearance (lexicographic order).\n\n    For example::\n\n        >>> P = ParamSpec(\'P\')\n        >>> T = TypeVar(\'T\')\n        >>> _collect_parameters((T, Callable[P, T]))\n        (~T, ~P)\n    """  # inserted
    parameters = []
    for t in args:
        if not isinstance(t, type):
            if isinstance(t, tuple):
                for x in t:
                    for collected in _collect_parameters([x]):
                        if collected not in parameters:
                            parameters.append(collected)
            else:  # inserted
                if hasattr(t, '__typing_subst__'):
                    if t not in parameters:
                        parameters.append(t)
                else:  # inserted
                    for x in getattr(t, '__parameters__', ()):
                        if x not in parameters:
                            parameters.append(x)
    return tuple(parameters)

def _check_generic(cls, parameters, elen):
    """Check correct count for parameters of a generic cls (internal helper).\n\n    This gives a nice error message in case of count mismatch.\n    """  # inserted
    if not elen:
        raise TypeError(f'{cls} is not a generic class')
    alen = len(parameters)
    if alen!= elen:
        raise TypeError(f"Too {('many' if alen > elen else 'few')} arguments for {cls}; actual {alen}, expected {elen}")

def _unpack_args(args):
    newargs = []
    for arg in args:
        subargs = getattr(arg, '__typing_unpacked_tuple_args__', None)
        if subargs is not None and (not (subargs and subargs[(-1)] is ...)):
            newargs.extend(subargs)
        else:  # inserted
            newargs.append(arg)
    return newargs

def _deduplicate(params):
    all_params = set(params)
    if len(all_params) < len(params):
        new_params = []
        for t in params:
            if t in all_params:
                new_params.append(t)
                all_params.remove(t)
        params = new_params
        assert not all_params, all_params
    return params

def _remove_dups_flatten(parameters):
    """Internal helper for Union creation and substitution.\n\n    Flatten Unions among parameters, then remove duplicates.\n    """  # inserted
    params = []
    for p in parameters:
        if isinstance(p, (_UnionGenericAlias, types.UnionType)):
            params.extend(p.__args__)
        else:  # inserted
            params.append(p)
    return tuple(_deduplicate(params))

def _flatten_literal_params(parameters):
    """Internal helper for Literal creation: flatten Literals among parameters."""  # inserted
    params = []
    for p in parameters:
        if isinstance(p, _LiteralGenericAlias):
            params.extend(p.__args__)
        else:  # inserted
            params.append(p)
    return tuple(params)
_cleanups = []
_caches = {}

def _tp_cache(func=None, /, *, typed=False):
    """Internal wrapper caching __getitem__ of generic types.\n\n    For non-hashable arguments, the original function is used as a fallback.\n    """  # inserted

    def decorator(func):
        cache = functools.lru_cache(typed=typed)(func)
        _caches[func] = cache
        _cleanups.append(cache.cache_clear)
        del cache

        @functools.wraps(func)
        def inner(*args, **kwds):
            try:
                return _caches[func](*args, **kwds)
            except TypeError:
                pass
            return func(*args, **kwds)
        return inner
    if func is not None:
        return decorator(func)
    return decorator

def _eval_type(t, globalns, localns, recursive_guard=frozenset()):
    """Evaluate all forward references in the given type t.\n\n    For use of globalns and localns see the docstring for get_type_hints().\n    recursive_guard is used to prevent infinite recursion with a recursive\n    ForwardRef.\n    """  # inserted
    if isinstance(t, ForwardRef):
        return t._evaluate(globalns, localns, recursive_guard)
    if isinstance(t, (_GenericAlias, GenericAlias, types.UnionType)):
        if isinstance(t, GenericAlias):
            args = tuple((ForwardRef(arg) if isinstance(arg, str) else arg for arg in t.__args__))
            is_unpacked = t.__unpacked__
            if _should_unflatten_callable_args(t, args):
                t = t.__origin__[args[:(-1)], args[(-1)]]
            else:  # inserted
                t = t.__origin__[args]
            if is_unpacked:
                t = Unpack[t]
        ev_args = tuple((_eval_type(a, globalns, localns, recursive_guard) for a in t.__args__))
        if ev_args == t.__args__:
            return t
        if isinstance(t, GenericAlias):
            return GenericAlias(t.__origin__, ev_args)
        if isinstance(t, types.UnionType):
            return functools.reduce(operator.or_, ev_args)
        return t.copy_with(ev_args)
    return t

class _Final:
    """Mixin to prohibit subclassing."""
    __slots__ = ('__weakref__',)

    def __init_subclass__(cls, /, *args, **kwds):
        if '_root' not in kwds:
            raise TypeError('Cannot subclass special typing classes')

class _NotIterable:
    """Mixin to prevent iteration, without being compatible with Iterable.\n\n    That is, we could do::\n\n        def __iter__(self): raise TypeError()\n\n    But this would make users of this mixin duck type-compatible with\n    collections.abc.Iterable - isinstance(foo, Iterable) would be True.\n\n    Luckily, we can instead prevent iteration by setting __iter__ to None, which\n    is treated specially.\n    """
    __slots__ = ()
    __iter__ = None

class _SpecialForm(_Final, _NotIterable, _root=True):
    __slots__ = ('_name', '__doc__', '_getitem')

    def __init__(self, getitem):
        self._getitem = getitem
        self._name = getitem.__name__
        self.__doc__ = getitem.__doc__

    def __getattr__(self, item):
        if item in {'__name__', '__qualname__'}:
            return self._name
        raise AttributeError(item)

    def __mro_entries__(self, bases):
        raise TypeError(f'Cannot subclass {self!r}')

    def __repr__(self):
        return 'typing.' + self._name

    def __reduce__(self):
        return self._name

    def __call__(self, *args, **kwds):
        raise TypeError(f'Cannot instantiate {self!r}')

    def __or__(self, other):
        return Union[self, other]

    def __ror__(self, other):
        return Union[other, self]

    def __instancecheck__(self, obj):
        raise TypeError(f'{self} cannot be used with isinstance()')

    def __subclasscheck__(self, cls):
        raise TypeError(f'{self} cannot be used with issubclass()')

    @_tp_cache
    def __getitem__(self, parameters):
        return self._getitem(self, parameters)

class _LiteralSpecialForm(_SpecialForm, _root=True):
    def __getitem__(self, parameters):
        if not isinstance(parameters, tuple):
            parameters = (parameters,)
        return self._getitem(self, *parameters)

class _AnyMeta(type):
    def __instancecheck__(self, obj):
        if self is Any:
            raise TypeError('typing.Any cannot be used with isinstance()')
        return super().__instancecheck__(obj)

    def __repr__(self):
        if self is Any:
            return 'typing.Any'
        return super().__repr__()

class Any(metaclass=_AnyMeta):
    """Special type indicating an unconstrained type.\n\n    - Any is compatible with every type.\n    - Any assumed to have all methods.\n    - All values assumed to be instances of Any.\n\n    Note that all the above statements are true from the point of view of\n    static type checkers. At runtime, Any should not be used with instance\n    checks.\n    """

    def __new__(cls, *args, **kwargs):
        if cls is Any:
            raise TypeError('Any cannot be instantiated')
        return super().__new__(cls, *args, **kwargs)

@_SpecialForm
def NoReturn(self, parameters):
    """Special type indicating functions that never return.\n\n    Example::\n\n        from typing import NoReturn\n\n        def stop() -> NoReturn:\n            raise Exception(\'no way\')\n\n    NoReturn can also be used as a bottom type, a type that\n    has no values. Starting in Python 3.11, the Never type should\n    be used for this concept instead. Type checkers should treat the two\n    equivalently.\n    """  # inserted
    raise TypeError(f'{self} is not subscriptable')

@_SpecialForm
def Never(self, parameters):
    """The bottom type, a type that has no members.\n\n    This can be used to define a function that should never be\n    called, or a function that never returns::\n\n        from typing import Never\n\n        def never_call_me(arg: Never) -> None:\n            pass\n\n        def int_or_str(arg: int | str) -> None:\n            never_call_me(arg)  # type checker error\n            match arg:\n                case int():\n                    print(\"It\'s an int\")\n                case str():\n                    print(\"It\'s a str\")\n                case _:\n                    never_call_me(arg)  # OK, arg is of type Never\n    """  # inserted
    raise TypeError(f'{self} is not subscriptable')

@_SpecialForm
def Self(self, parameters):
    """Used to spell the type of \"self\" in classes.\n\n    Example::\n\n        from typing import Self\n\n        class Foo:\n            def return_self(self) -> Self:\n                ...\n                return self\n\n    This is especially useful for:\n        - classmethods that are used as alternative constructors\n        - annotating an `__enter__` method which returns self\n    """  # inserted
    raise TypeError(f'{self} is not subscriptable')

@_SpecialForm
def LiteralString(self, parameters):
    """Represents an arbitrary literal string.\n\n    Example::\n\n        from typing import LiteralString\n\n        def run_query(sql: LiteralString) -> None:\n            ...\n\n        def caller(arbitrary_string: str, literal_string: LiteralString) -> None:\n            run_query(\"SELECT * FROM students\")  # OK\n            run_query(literal_string)  # OK\n            run_query(\"SELECT * FROM \" + literal_string)  # OK\n            run_query(arbitrary_string)  # type checker error\n            run_query(  # type checker error\n                f\"SELECT * FROM students WHERE name = {arbitrary_string}\"\n            )\n\n    Only string literals and other LiteralStrings are compatible\n    with LiteralString. This provides a tool to help prevent\n    security issues such as SQL injection.\n    """  # inserted
    raise TypeError(f'{self} is not subscriptable')

@_SpecialForm
def ClassVar(self, parameters):
    """Special type construct to mark class variables.\n\n    An annotation wrapped in ClassVar indicates that a given\n    attribute is intended to be used as a class variable and\n    should not be set on instances of that class.\n\n    Usage::\n\n        class Starship:\n            stats: ClassVar[dict[str, int]] = {} # class variable\n            damage: int = 10                     # instance variable\n\n    ClassVar accepts only types and cannot be further subscribed.\n\n    Note that ClassVar is not a class itself, and should not\n    be used with isinstance() or issubclass().\n    """  # inserted
    item = _type_check(parameters, f'{self} accepts only single type.')
    return _GenericAlias(self, (item,))

@_SpecialForm
def Final(self, parameters):
    """Special typing construct to indicate final names to type checkers.\n\n    A final name cannot be re-assigned or overridden in a subclass.\n\n    For example::\n\n        MAX_SIZE: Final = 9000\n        MAX_SIZE += 1  # Error reported by type checker\n\n        class Connection:\n            TIMEOUT: Final[int] = 10\n\n        class FastConnector(Connection):\n            TIMEOUT = 1  # Error reported by type checker\n\n    There is no runtime checking of these properties.\n    """  # inserted
    item = _type_check(parameters, f'{self} accepts only single type.')
    return _GenericAlias(self, (item,))

@_SpecialForm
def Union(self, parameters):
    """Union type; Union[X, Y] means either X or Y.\n\n    On Python 3.10 and higher, the | operator\n    can also be used to denote unions;\n    X | Y means the same thing to the type checker as Union[X, Y].\n\n    To define a union, use e.g. Union[int, str]. Details:\n    - The arguments must be types and there must be at least one.\n    - None as an argument is a special case and is replaced by\n      type(None).\n    - Unions of unions are flattened, e.g.::\n\n        assert Union[Union[int, str], float] == Union[int, str, float]\n\n    - Unions of a single argument vanish, e.g.::\n\n        assert Union[int] == int  # The constructor actually returns int\n\n    - Redundant arguments are skipped, e.g.::\n\n        assert Union[int, str, int] == Union[int, str]\n\n    - When comparing unions, the argument order is ignored, e.g.::\n\n        assert Union[int, str] == Union[str, int]\n\n    - You cannot subclass or instantiate a union.\n    - You can use Optional[X] as a shorthand for Union[X, None].\n    """  # inserted
    if parameters == ():
        raise TypeError('Cannot take a Union of no types.')
    if not isinstance(parameters, tuple):
        parameters = (parameters,)
    msg = 'Union[arg, ...]: each arg must be a type.'
    parameters = tuple((_type_check(p, msg) for p in parameters))
    parameters = _remove_dups_flatten(parameters)
    if len(parameters) == 1:
        return parameters[0]
    if len(parameters) == 2 and type(None) in parameters:
        return _UnionGenericAlias(self, parameters, name='Optional')
    return _UnionGenericAlias(self, parameters)

def _make_union(left, right):
    """Used from the C implementation of TypeVar.\n\n    TypeVar.__or__ calls this instead of returning types.UnionType\n    because we want to allow unions between TypeVars and strings\n    (forward references).\n    """  # inserted
    return Union[left, right]

@_SpecialForm
def Optional(self, parameters):
    """Optional[X] is equivalent to Union[X, None]."""  # inserted
    arg = _type_check(parameters, f'{self} requires a single type.')
    return Union[arg, type(None)]

@_LiteralSpecialForm
@_tp_cache(typed=True)
def Literal(self, *parameters):
    """Special typing form to define literal types (a.k.a. value types).\n\n    This form can be used to indicate to type checkers that the corresponding\n    variable or function parameter has a value equivalent to the provided\n    literal (or one of several literals)::\n\n        def validate_simple(data: Any) -> Literal[True]:  # always returns True\n            ...\n\n        MODE = Literal[\'r\', \'rb\', \'w\', \'wb\']\n        def open_helper(file: str, mode: MODE) -> str:\n            ...\n\n        open_helper(\'/some/path\', \'r\')  # Passes type check\n        open_helper(\'/other/path\', \'typo\')  # Error in type checker\n\n    Literal[...] cannot be subclassed. At runtime, an arbitrary value\n    is allowed as type argument to Literal[...], but type checkers may\n    impose restrictions.\n    """  # inserted
    parameters = _flatten_literal_params(parameters)
    try:
        parameters = tuple((p for p, _ in _deduplicate(list(_value_and_type_iter(parameters)))))
    except TypeError:
        pass
    return _LiteralGenericAlias(self, parameters)

@_SpecialForm
def TypeAlias(self, parameters):
    """Special form for marking type aliases.\n\n    Use TypeAlias to indicate that an assignment should\n    be recognized as a proper type alias definition by type\n    checkers.\n\n    For example::\n\n        Predicate: TypeAlias = Callable[..., bool]\n\n    It\'s invalid when used anywhere except as in the example above.\n    """  # inserted
    raise TypeError(f'{self} is not subscriptable')

@_SpecialForm
def Concatenate(self, parameters):
    """Special form for annotating higher-order functions.\n\n    ``Concatenate`` can be used in conjunction with ``ParamSpec`` and\n    ``Callable`` to represent a higher-order function which adds, removes or\n    transforms the parameters of a callable.\n\n    For example::\n\n        Callable[Concatenate[int, P], int]\n\n    See PEP 612 for detailed information.\n    """  # inserted
    if parameters == ():
        raise TypeError('Cannot take a Concatenate of no types.')
    if not isinstance(parameters, tuple):
        parameters = (parameters,)
    if not (parameters[(-1)] is ... or isinstance(parameters[(-1)], ParamSpec)):
        raise TypeError('The last parameter to Concatenate should be a ParamSpec variable or ellipsis.')
    msg = 'Concatenate[arg, ...]: each arg must be a type.'
    parameters = (*(_type_check(p, msg) for p in parameters[:(-1)]), parameters[(-1)])
    return _ConcatenateGenericAlias(self, parameters)

@_SpecialForm
def TypeGuard(self, parameters):
    """Special typing construct for marking user-defined type guard functions.\n\n    ``TypeGuard`` can be used to annotate the return type of a user-defined\n    type guard function.  ``TypeGuard`` only accepts a single type argument.\n    At runtime, functions marked this way should return a boolean.\n\n    ``TypeGuard`` aims to benefit *type narrowing* -- a technique used by static\n    type checkers to determine a more precise type of an expression within a\n    program\'s code flow.  Usually type narrowing is done by analyzing\n    conditional code flow and applying the narrowing to a block of code.  The\n    conditional expression here is sometimes referred to as a \"type guard\".\n\n    Sometimes it would be convenient to use a user-defined boolean function\n    as a type guard.  Such a function should use ``TypeGuard[...]`` as its\n    return type to alert static type checkers to this intention.\n\n    Using  ``-> TypeGuard`` tells the static type checker that for a given\n    function:\n\n    1. The return value is a boolean.\n    2. If the return value is ``True``, the type of its argument\n       is the type inside ``TypeGuard``.\n\n       For example::\n\n           def is_str(val: Union[str, float]):\n               # \"isinstance\" type guard\n               if isinstance(val, str):\n                   # Type of ``val`` is narrowed to ``str``\n                   ...\n               else:\n                   # Else, type of ``val`` is narrowed to ``float``.\n                   ...\n\n    Strict type narrowing is not enforced -- ``TypeB`` need not be a narrower\n    form of ``TypeA`` (it can even be a wider form) and this may lead to\n    type-unsafe results.  The main reason is to allow for things like\n    narrowing ``List[object]`` to ``List[str]`` even though the latter is not\n    a subtype of the former, since ``List`` is invariant.  The responsibility of\n    writing type-safe type guards is left to the user.\n\n    ``TypeGuard`` also works with type variables.  For more information, see\n    PEP 647 (User-Defined Type Guards).\n    """  # inserted
    item = _type_check(parameters, f'{self} accepts only single type.')
    return _GenericAlias(self, (item,))

class ForwardRef(_Final, _root=True):
    """Internal wrapper to hold a forward reference."""
    __slots__ = ('__forward_arg__', '__forward_code__', '__forward_evaluated__', '__forward_value__', '__forward_is_argument__', '__forward_is_class__', '__forward_module__')

    def __init__(self, arg, is_argument=True, module=None, *, is_class=False):
        if not isinstance(arg, str):
            raise TypeError(f'Forward reference must be a string -- got {arg!r}')
        if arg[0] == '*':
            arg_to_compile = f'({arg},)[0]'
        else:  # inserted
            arg_to_compile = arg
        try:
            code = compile(arg_to_compile, '<string>', 'eval')
        except SyntaxError:
            raise SyntaxError(f'Forward reference must be an expression -- got {arg!r}')
        else:  # inserted
            self.__forward_arg__ = arg
            self.__forward_code__ = code
            self.__forward_evaluated__ = False
            self.__forward_value__ = None
            self.__forward_is_argument__ = is_argument
            self.__forward_is_class__ = is_class
            self.__forward_module__ = module

    def _evaluate(self, globalns, localns, recursive_guard):
        if self.__forward_arg__ in recursive_guard:
            return self
        if not self.__forward_evaluated__ or localns is not globalns or (globalns is None and localns is None):
            globalns = localns = {}
        else:  # inserted
            if globalns is None:
                globalns = localns
            else:  # inserted
                if localns is None:
                    localns = globalns
            if self.__forward_module__ is not None:
                globalns = getattr(sys.modules.get(self.__forward_module__, None), '__dict__', globalns)
            type_ = _type_check(eval(self.__forward_code__, globalns, localns), 'Forward references must evaluate to types.', is_argument=self.__forward_is_argument__, allow_special_forms=self.__forward_is_class__)
            self.__forward_value__ = _eval_type(type_, globalns, localns, recursive_guard | {self.__forward_arg__})
            self.__forward_evaluated__ = True
        return self.__forward_value__

    def __eq__(self, other):
        if not isinstance(other, ForwardRef):
            return NotImplemented
        return self.__forward_arg__ == other.__forward_arg__ and self.__forward_value__ == other.__forward_value__
        else:  # inserted
            pass  # postinserted
        return self.__forward_arg__ == other.__forward_arg__ and self.__forward_module__ == other.__forward_module__

    def __hash__(self):
        return hash((self.__forward_arg__, self.__forward_module__))

    def __or__(self, other):
        return Union[self, other]

    def __ror__(self, other):
        return Union[other, self]

    def __repr__(self):
        if self.__forward_module__ is None:
            module_repr = ''
        else:  # inserted
            module_repr = f', module={self.__forward_module__!r}'
        return f'ForwardRef({self.__forward_arg__!r}{module_repr})'

def _is_unpacked_typevartuple(x: Any) -> bool:
    return not isinstance(x, type) and getattr(x, '__typing_is_unpacked_typevartuple__', False)

def _is_typevar_like(x: Any) -> bool:
    return isinstance(x, (TypeVar, ParamSpec)) or _is_unpacked_typevartuple(x)

class _PickleUsingNameMixin:
    """Mixin enabling pickling based on self.__name__."""

    def __reduce__(self):
        return self.__name__

def _typevar_subst(self, arg):
    msg = 'Parameters to generic types must be types.'
    arg = _type_check(arg, msg, is_argument=True)
    if isinstance(arg, _GenericAlias) and arg.__origin__ is Unpack or (isinstance(arg, GenericAlias) and getattr(arg, '__unpacked__', False)):
        raise TypeError(f'{arg} is not valid as type argument')
    return arg

def _typevartuple_prepare_subst(self, alias, args):
    params = alias.__parameters__
    typevartuple_index = params.index(self)
    for param in params[typevartuple_index + 1:]:
        if isinstance(param, TypeVarTuple):
            raise TypeError(f'More than one TypeVarTuple parameter in {alias}')
    else:  # inserted
        alen = len(args)
        plen = len(params)
        left = typevartuple_index
        right = plen - typevartuple_index - 1
        var_tuple_index = None
        fillarg = None
        for k, arg in enumerate(args):
            if not isinstance(arg, type):
                subargs = getattr(arg, '__typing_unpacked_tuple_args__', None)
                if subargs and len(subargs) == 2 and (subargs[(-1)] is ...):
                    if var_tuple_index is not None:
                        raise TypeError('More than one unpacked arbitrary-length tuple argument')
                    var_tuple_index = k
                    fillarg = subargs[0]
        else:  # inserted
            if var_tuple_index is not None:
                left = min(left, var_tuple_index)
                right = min(right, alen - var_tuple_index - 1)
            else:  # inserted
                if left + right > alen:
                    raise TypeError(f'Too few arguments for {alias}; actual {alen}, expected at least {plen - 1}')
            return (*args[:left], *[fillarg] * (typevartuple_index - left), tuple(args[left:alen - right]), *[fillarg] * (plen - right - left - typevartuple_index - 1), *args[alen - right:])

def _paramspec_subst(self, arg):
    if isinstance(arg, (list, tuple)):
        arg = tuple((_type_check(a, 'Expected a type.') for a in arg))
        return arg
    if not _is_param_expr(arg):
        raise TypeError(f'Expected a list of types, an ellipsis, ParamSpec, or Concatenate. Got {arg}')
    return arg

def _paramspec_prepare_subst(self, alias, args):
    params = alias.__parameters__
    i = params.index(self)
    if i >= len(args):
        raise TypeError(f'Too few arguments for {alias}')
    assert not (len(params) == 1 and _is_param_expr(args[0]) or i == 0)
    args = (args,)
    return args
    if isinstance(args[i], list):
        args = (*args[:i], tuple(args[i]), *args[i + 1:])
    return args

@_tp_cache
def _generic_class_getitem(cls, params):
    """Parameterizes a generic class.\n\n    At least, parameterizing a generic class is the *main* thing this method\n    does. For example, for some generic class `Foo`, this is called when we\n    do `Foo[int]` - there, with `cls=Foo` and `params=int`.\n\n    However, note that this method is also called when defining generic\n    classes in the first place with `class Foo(Generic[T]): ...`.\n    """  # inserted
    if not isinstance(params, tuple):
        params = (params,)
    params = tuple((_type_convert(p) for p in params))
    is_generic_or_protocol = cls in (Generic, Protocol)
    if not is_generic_or_protocol or not params:
        raise TypeError(f'Parameter list to {cls.__qualname__}[...] cannot be empty')
    if not all((_is_typevar_like(p) for p in params)):
        raise TypeError(f'Parameters to {cls.__name__}[...] must all be type variables or parameter specification variables.')
    if len(set(params))!= len(params):
        raise TypeError(f'Parameters to {cls.__name__}[...] must all be unique')
    else:  # inserted
        for param in cls.__parameters__:
            prepare = getattr(param, '__typing_prepare_subst__', None)
            if prepare is not None:
                params = prepare(cls, params)
        _check_generic(cls, params, len(cls.__parameters__))
        new_args = []
        for param, new_arg in zip(cls.__parameters__, params):
            if isinstance(param, TypeVarTuple):
                new_args.extend(new_arg)
            else:  # inserted
                new_args.append(new_arg)
        params = tuple(new_args)
    return _GenericAlias(cls, params)

def _generic_init_subclass(cls, *args, **kwargs):
    super(Generic, cls).__init_subclass__(*args, **kwargs)
    tvars = []
    if '__orig_bases__' in cls.__dict__:
        error = Generic in cls.__orig_bases__
    else:  # inserted
        error = Generic in cls.__bases__ and cls.__name__!= 'Protocol' and (type(cls)!= _TypedDictMeta)
    if error:
        raise TypeError('Cannot inherit from plain Generic')
    if '__orig_bases__' in cls.__dict__:
        tvars = _collect_parameters(cls.__orig_bases__)
        gvars = None
        for base in cls.__orig_bases__:
            if isinstance(base, _GenericAlias) and base.__origin__ is Generic:
                if gvars is not None:
                    raise TypeError('Cannot inherit from Generic[...] multiple times.')
                gvars = base.__parameters__
        else:  # inserted
            if gvars is not None:
                tvarset = set(tvars)
                gvarset = set(gvars)
                if not tvarset <= gvarset:
                    s_vars = ', '.join((str(t) for t in tvars if t not in gvarset))
                    s_args = ', '.join((str(g) for g in gvars))
                    raise TypeError(f'Some type variables ({s_vars}) are not listed in Generic[{s_args}]')
                tvars = gvars
    cls.__parameters__ = tuple(tvars)

def _is_dunder(attr):
    return attr.startswith('__') and attr.endswith('__')

class _BaseGenericAlias(_Final, _root=True):
    """The central part of the internal API.\n\n    This represents a generic version of type \'origin\' with type arguments \'params\'.\n    There are two kind of these aliases: user defined and special. The special ones\n    are wrappers around builtin collections and ABCs in collections.abc. These must\n    have \'name\' always set. If \'inst\' is False, then the alias can\'t be instantiated;\n    this is used by e.g. typing.List and typing.Dict.\n    """

    def __init__(self, origin, *, inst=True, name=None):
        self._inst = inst
        self._name = name
        self.__origin__ = origin
        self.__slots__ = None

    def __call__(self, *args, **kwargs):
        if not self._inst:
            raise TypeError(f'Type {self._name} cannot be instantiated; use {self.__origin__.__name__}() instead')
        result = self.__origin__(*args, **kwargs)
        try:
            result.__orig_class__ = self
        except AttributeError:
            pass
        else:  # inserted
            return result

    def __mro_entries__(self, bases):
        res = []
        if self.__origin__ not in bases:
            res.append(self.__origin__)
        i = bases.index(self)
        for b in bases[i + 1:]:
            if isinstance(b, _BaseGenericAlias) or issubclass(b, Generic):
                break
        else:  # inserted
            res.append(Generic)
            return tuple(res)

    def __getattr__(self, attr):
        if attr in {'__name__', '__qualname__'}:
            return self._name or self.__origin__.__name__
        if '__origin__' in self.__dict__ and (not _is_dunder(attr)):
            return getattr(self.__origin__, attr)
        raise AttributeError(attr)

    def __setattr__(self, attr, val):
        if _is_dunder(attr) or attr in {'_nparams', '_inst', '_name'}:
            super().__setattr__(attr, val)
        else:  # inserted
            setattr(self.__origin__, attr, val)

    def __instancecheck__(self, obj):
        return self.__subclasscheck__(type(obj))

    def __subclasscheck__(self, cls):
        raise TypeError('Subscripted generics cannot be used with class and instance checks')

    def __dir__(self):
        return list(set(super().__dir__() + [attr for attr in dir(self.__origin__) if not _is_dunder(attr)]))

class _GenericAlias(_BaseGenericAlias, _root=True):
    def __init__(self, origin, args, *, inst=True, name=None):
        super().__init__(origin, inst=inst, name=name)
        if not isinstance(args, tuple):
            args = (args,)
        self.__args__ = tuple((... if a is _TypingEllipsis else a for a in args))
        self.__parameters__ = _collect_parameters(args)
        if not name:
            self.__module__ = origin.__module__

    def __eq__(self, other):
        if not isinstance(other, _GenericAlias):
            return NotImplemented
        return self.__origin__ == other.__origin__ and self.__args__ == other.__args__

    def __hash__(self):
        return hash((self.__origin__, self.__args__))

    def __or__(self, right):
        return Union[self, right]

    def __ror__(self, left):
        return Union[left, self]

    @_tp_cache
    def __getitem__(self, args):
        if self.__origin__ in (Generic, Protocol):
            raise TypeError(f'Cannot subscript already-subscripted {self}')
        if not self.__parameters__:
            raise TypeError(f'{self} is not a generic class')
        if not isinstance(args, tuple):
            args = (args,)
        args = tuple((_type_convert(p) for p in args))
        args = _unpack_args(args)
        new_args = self._determine_new_args(args)
        r = self.copy_with(new_args)
        return r

    def _determine_new_args(self, args):
        params = self.__parameters__
        for param in params:
            prepare = getattr(param, '__typing_prepare_subst__', None)
            if prepare is not None:
                args = prepare(self, args)
        alen = len(args)
        plen = len(params)
        if alen!= plen:
            raise TypeError(f"Too {('many' if alen > plen else 'few')} arguments for {self}; actual {alen}, expected {plen}")
        new_arg_by_param = dict(zip(params, args))
        return tuple(self._make_substitution(self.__args__, new_arg_by_param))

    def _make_substitution(self, args, new_arg_by_param):
        """Create a list of new type arguments."""  # inserted
        new_args = []
        for old_arg in args:
            if isinstance(old_arg, type):
                new_args.append(old_arg)
                continue
            substfunc = getattr(old_arg, '__typing_subst__', None)
            if substfunc:
                new_arg = substfunc(new_arg_by_param[old_arg])
            else:  # inserted
                subparams = getattr(old_arg, '__parameters__', ())
                if not subparams:
                    new_arg = old_arg
                else:  # inserted
                    subargs = []
                    for x in subparams:
                        if isinstance(x, TypeVarTuple):
                            subargs.extend(new_arg_by_param[x])
                        else:  # inserted
                            subargs.append(new_arg_by_param[x])
                    new_arg = old_arg[tuple(subargs)]
            if self.__origin__ == collections.abc.Callable and isinstance(new_arg, tuple):
                new_args.extend(new_arg)
            else:  # inserted
                if _is_unpacked_typevartuple(old_arg):
                    new_args.extend(new_arg)
                else:  # inserted
                    if isinstance(old_arg, tuple):
                        new_args.append(tuple(self._make_substitution(old_arg, new_arg_by_param)))
                    else:  # inserted
                        new_args.append(new_arg)
        return new_args

    def copy_with(self, args):
        return self.__class__(self.__origin__, args, name=self._name, inst=self._inst)

    def __repr__(self):
        if self._name:
            name = 'typing.' + self._name
        else:  # inserted
            name = _type_repr(self.__origin__)
        if self.__args__:
            args = ', '.join([_type_repr(a) for a in self.__args__])
        else:  # inserted
            args = '()'
        return f'{name}[{args}]'

    def __reduce__(self):
        if self._name:
            origin = globals()[self._name]
        else:  # inserted
            origin = self.__origin__
        args = tuple(self.__args__)
        if len(args) == 1 and (not isinstance(args[0], tuple)):
            args, = args
        return (operator.getitem, (origin, args))

    def __mro_entries__(self, bases):
        if isinstance(self.__origin__, _SpecialForm):
            raise TypeError(f'Cannot subclass {self!r}')
        if self._name:
            return super().__mro_entries__(bases)
        if not self.__origin__ is Generic or Protocol in bases:
            return ()
        i = bases.index(self)
        for b in bases[i + 1:]:
            if isinstance(b, _BaseGenericAlias) and b is not self:
                return ()
        return (self.__origin__,)

    def __iter__(self):
        yield Unpack[self]

class _SpecialGenericAlias(_NotIterable, _BaseGenericAlias, _root=True):
    def __init__(self, origin, nparams, *, inst=True, name=None):
        if name is None:
            name = origin.__name__
        super().__init__(origin, inst=inst, name=name)
        self._nparams = nparams
        if origin.__module__ == 'builtins':
            self.__doc__ = f'A generic version of {origin.__qualname__}.'
        else:  # inserted
            self.__doc__ = f'A generic version of {origin.__module__}.{origin.__qualname__}.'

    @_tp_cache
    def __getitem__(self, params):
        if not isinstance(params, tuple):
            params = (params,)
        msg = 'Parameters to generic types must be types.'
        params = tuple((_type_check(p, msg) for p in params))
        _check_generic(self, params, self._nparams)
        return self.copy_with(params)

    def copy_with(self, params):
        return _GenericAlias(self.__origin__, params, name=self._name, inst=self._inst)

    def __repr__(self):
        return 'typing.' + self._name

    def __subclasscheck__(self, cls):
        if isinstance(cls, _SpecialGenericAlias):
            return issubclass(cls.__origin__, self.__origin__)
        if not isinstance(cls, _GenericAlias):
            return issubclass(cls, self.__origin__)
        return super().__subclasscheck__(cls)

    def __reduce__(self):
        return self._name

    def __or__(self, right):
        return Union[self, right]

    def __ror__(self, left):
        return Union[left, self]

class _DeprecatedGenericAlias(_SpecialGenericAlias, _root=True):
    def __init__(self, origin, nparams, *, removal_version, inst=True, name=None):
        super().__init__(origin, nparams, inst=inst, name=name)
        self._removal_version = removal_version

    def __instancecheck__(self, inst):
        import warnings
        warnings._deprecated(f'{self.__module__}.{self._name}', remove=self._removal_version)
        return super().__instancecheck__(inst)

class _CallableGenericAlias(_NotIterable, _GenericAlias, _root=True):
    def __repr__(self):
        assert self._name == 'Callable'
        args = self.__args__
        if len(args) == 2 and _is_param_expr(args[0]):
            return super().__repr__()
        return f"typing.Callable[[{', '.join([_type_repr(a) for a in args[:(-1)]])}], {_type_repr(args[(-1)])}]"

    def __reduce__(self):
        args = self.__args__
        if not (len(args) == 2 and _is_param_expr(args[0])):
            args = (list(args[:(-1)]), args[(-1)])
        return (operator.getitem, (Callable, args))

class _CallableType(_SpecialGenericAlias, _root=True):
    def copy_with(self, params):
        return _CallableGenericAlias(self.__origin__, params, name=self._name, inst=self._inst)

    def __getitem__(self, params):
        if not isinstance(params, tuple) or len(params)!= 2:
            raise TypeError('Callable must be used as Callable[[arg, ...], result].')
        args, result = params
        if isinstance(args, list):
            params = (tuple(args), result)
        else:  # inserted
            params = (args, result)
        return self.__getitem_inner__(params)

    @_tp_cache
    def __getitem_inner__(self, params):
        args, result = params
        msg = 'Callable[args, result]: result must be a type.'
        result = _type_check(result, msg)
        if args is Ellipsis:
            return self.copy_with((_TypingEllipsis, result))
        if not isinstance(args, tuple):
            args = (args,)
        args = tuple((_type_convert(arg) for arg in args))
        params = args + (result,)
        return self.copy_with(params)

class _TupleType(_SpecialGenericAlias, _root=True):
    @_tp_cache
    def __getitem__(self, params):
        if not isinstance(params, tuple):
            params = (params,)
        if len(params) >= 2 and params[(-1)] is ...:
            msg = 'Tuple[t, ...]: t must be a type.'
            params = tuple((_type_check(p, msg) for p in params[:(-1)]))
            return self.copy_with((*params, _TypingEllipsis))
        msg = 'Tuple[t0, t1, ...]: each t must be a type.'
        params = tuple((_type_check(p, msg) for p in params))
        return self.copy_with(params)

class _UnionGenericAlias(_NotIterable, _GenericAlias, _root=True):
    def copy_with(self, params):
        return Union[params]

    def __eq__(self, other):
        if not isinstance(other, (_UnionGenericAlias, types.UnionType)):
            return NotImplemented
        return set(self.__args__) == set(other.__args__)

    def __hash__(self):
        return hash(frozenset(self.__args__))

    def __repr__(self):
        args = self.__args__
        if len(args) == 2 and args[0] is type(None):
            return f'typing.Optional[{_type_repr(args[1])}]'
        if args[1] is type(None):
            return f'typing.Optional[{_type_repr(args[0])}]'
        return super().__repr__()

    def __instancecheck__(self, obj):
        return self.__subclasscheck__(type(obj))

    def __subclasscheck__(self, cls):
        for arg in self.__args__:
            if issubclass(cls, arg):
                return True

    def __reduce__(self):
        func, (origin, args) = super().__reduce__()
        return (func, (Union, args))

def _value_and_type_iter(parameters):
    return ((p, type(p)) for p in parameters)

class _LiteralGenericAlias(_GenericAlias, _root=True):
    def __eq__(self, other):
        if not isinstance(other, _LiteralGenericAlias):
            return NotImplemented
        return set(_value_and_type_iter(self.__args__)) == set(_value_and_type_iter(other.__args__))

    def __hash__(self):
        return hash(frozenset(_value_and_type_iter(self.__args__)))

class _ConcatenateGenericAlias(self, parameters):
    def copy_with(self, params):
        if isinstance(params[(-1)], (list, tuple)):
            return (*params[:(-1)], *params[(-1)])
        if isinstance(params[(-1)], _ConcatenateGenericAlias):
            params = (*params[:(-1)], *params[(-1)].__args__)
        return super().copy_with(params)
            """Type unpack operator.\n\n    The type unpack operator takes the child types from some container type,\n    such as `tuple[int, str]` or a `TypeVarTuple`, and \'pulls them out\'.\n\n    For example::\n\n        # For some generic class `Foo`:\n        Foo[Unpack[tuple[int, str]]]  # Equivalent to Foo[int, str]\n\n        Ts = TypeVarTuple(\'Ts\')\n        # Specifies that `Bar` is generic in an arbitrary number of types.\n        # (Think of `Ts` as a tuple of an arbitrary number of individual\n        #  `TypeVar`s, which the `Unpack` is \'pulling out\' directly into the\n        #  `Generic[]`.)\n        class Bar(Generic[Unpack[Ts]]): ...\n        Bar[int]  # Valid\n        Bar[int, str]  # Also valid\n\n    From Python 3.11, this can also be done using the `*` operator::\n\n        Foo[*tuple[int, str]]\n        class Bar(Generic[*Ts]): ...\n\n    And from Python 3.12, it can be done using built-in syntax for generics::\n\n        Foo[*tuple[int, str]]\n        class Bar[*Ts]: ...\n\n    The operator can also be used along with a `TypedDict` to annotate\n    `**kwargs` in a function signature::\n\n        class Movie(TypedDict):\n            name: str\n            year: int\n\n        # This function expects two keyword arguments - *name* of type `str` and\n        # *year* of type `int`.\n        def foo(**kwargs: Unpack[Movie]): ...\n\n    Note that there is only some runtime checking of this operator. Not\n    everything the runtime allows may be accepted by static type checkers.\n\n    For more information, see PEPs 646 and 692.\n    """  # inserted
            item = _type_check(parameters, f'{self} accepts only single type.')
            return _UnpackGenericAlias(origin=self, args=(item,))

class _UnpackGenericAlias(_GenericAlias, _root=True):
    def __repr__(self):
        return f'typing.Unpack[{_type_repr(self.__args__[0])}]'

    def __getitem__(self, args):
        if self.__typing_is_unpacked_typevartuple__:
            return args
        return super().__getitem__(args)

    @property
    def __typing_unpacked_tuple_args__(self):
        assert self.__origin__ is Unpack
        assert len(self.__args__) == 1
        arg, = self.__args__
        if isinstance(arg, _GenericAlias):
            assert arg.__origin__ is tuple
            return arg.__args__

    @property
    def __typing_is_unpacked_typevartuple__(self):
        assert self.__origin__ is Unpack
        assert len(self.__args__) == 1
        return isinstance(self.__args__[0], TypeVarTuple)

class _TypingEllipsis:
    """Internal placeholder for ... (ellipsis)."""
_TYPING_INTERNALS = frozenset({'__orig_class__', '__parameters__', '_is_runtime_protocol', '__orig_bases__', '_is_protocol', '__type_params__', '__non_callable_proto_members__', '__protocol_attrs__'})
_SPECIAL_NAMES: _TYPING_INTERNALS | _SPECIAL_NAMES | {'__class_getitem__', '__slots__', '__module__', '__subclasshook__', '__init__', '__dict__', '__abstractmethods__', '__new__', '__annotations__', '_MutableMapping__marker'} = frozenset({'__module__', '__init__', '__doc__', '__subclasshook__'})

def _get_protocol_attrs(cls, *args, **kwargs):
    """Collect protocol members from a protocol class objects.\n\n    This includes names actually defined in the class dictionary, as well\n    as names that appear in annotations. Special names (above) are skipped.\n    """  # inserted
    attrs = set()
    for base in cls.__mro__[:(-1)]:
        if base.__name__ in {'Protocol', 'Generic'}:
            continue
        annotations = getattr(base, '__annotations__', {})
        for attr in (*base.__dict__, *annotations):
            if not attr.startswith('_abc_') and attr not in EXCLUDED_ATTRIBUTES:
                attrs.add(attr)
    return attrs
        cls = type(self)
        if cls._is_protocol:
            raise TypeError('Protocols cannot be instantiated')
        if cls.__init__ is not _no_init_or_replace_init:
            return
        for base in cls.__mro__:
            init = base.__dict__.get('__init__', _no_init_or_replace_init)
            if init is not _no_init_or_replace_init:
                cls.__init__ = init
                break
        else:  # inserted
            cls.__init__ = object.__init__
        cls.__init__(self, *args, **kwargs)
            try:
                return sys._getframemodulename(depth + 1) or default
            except AttributeError:
                pass
            try:
                return sys._getframe(depth + 1).f_globals.get('__name__', default)
            except (AttributeError, ValueError):
                return
                    """Allow instance and class checks for special stdlib modules.\n\n    The abc and functools modules indiscriminately call isinstance() and\n    issubclass() on the whole MRO of a user class, which may contain protocols.\n    """  # inserted
                    return _caller(depth) in {None, 'functools', 'abc'}
                        from inspect import getattr_static
                        return getattr_static

def _pickle_psargs(psargs):
    return (ParamSpecArgs, (psargs.__origin__,))
copyreg.pickle(ParamSpecArgs, _pickle_psargs)

def _pickle_pskwargs(pskwargs):
    return (ParamSpecKwargs, (pskwargs.__origin__,))
copyreg.pickle(ParamSpecKwargs, _pickle_pskwargs)
pass

def _ProtocolMeta(ABCMeta):
    def __new__(mcls, name, bases, namespace, /, **kwargs):
        if name == 'Protocol' and bases == (Generic,):
            break
        if Protocol in bases:
            for base in bases:
                if base in {object, Generic}:
                    continue
                if base.__name__ in _PROTO_ALLOWLIST.get(base.__module__, []):
                    continue
                if not issubclass(base, Generic) or not getattr(base, '_is_protocol', False):
                    raise TypeError(f'Protocols can only inherit from other protocols, got {base!r}')
        return super().__new__(mcls, name, bases, namespace, **kwargs)

    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if getattr(cls, '_is_protocol', False):
            cls.__protocol_attrs__ = _get_protocol_attrs(cls)

    def __subclasscheck__(cls, other):
        if cls is Protocol:
            return type.__subclasscheck__(cls, other)
        if not getattr(cls, '_is_protocol', False) or _allow_reckless_class_checks() or (not isinstance(other, type)):
            raise TypeError('issubclass() arg 1 must be a class')
        if not getattr(cls, '_is_runtime_protocol', False):
            raise TypeError('Instance and class checks can only be used with @runtime_checkable protocols')
        if cls.__non_callable_proto_members__ and cls.__dict__.get('__subclasshook__') is _proto_hook:
            raise TypeError('Protocols with non-method members don\'t support issubclass()')
        return super().__subclasscheck__(other)

    def __instancecheck__(cls, instance):
        if cls is Protocol:
            return type.__instancecheck__(cls, instance)
        if not getattr(cls, '_is_protocol', False):
            return super().__instancecheck__(instance)
        if not getattr(cls, '_is_runtime_protocol', False) and (not _allow_reckless_class_checks()):
            raise TypeError('Instance and class checks can only be used with @runtime_checkable protocols')
        if super().__instancecheck__(instance):
            return True
        getattr_static = _lazy_load_getattr_static()
        for attr in cls.__protocol_attrs__:
            try:
                val = getattr_static(instance, attr)
            except AttributeError:
                return False
            else:  # inserted
                pass
                try:
                    pass  # postinserted
                pass
            else:  # inserted
                if val is None and attr not in cls.__non_callable_proto_members__:
                    return False
        else:  # inserted
            return True

def _proto_hook(cls, other):
    if not cls.__dict__.get('_is_protocol', False):
        return NotImplemented
    for attr in cls.__protocol_attrs__:
        for base in other.__mro__:
            if attr in base.__dict__ and base.__dict__[attr] is None:
                return NotImplemented
            break
            annotations = getattr(base, '__annotations__', {})
            if isinstance(annotations, collections.abc.Mapping) and attr in annotations and issubclass(other, Generic) and getattr(other, '_is_protocol', False):
                break
        else:  # inserted
            return NotImplemented
    else:  # inserted
        return True
pass

def Protocol(**Generic, metaclass=_ProtocolMeta):
    """Base class for protocol classes.\n\n    Protocol classes are defined as::\n\n        class Proto(Protocol):\n            def meth(self) -> int:\n                ...\n\n    Such classes are primarily used with static type checkers that recognize\n    structural subtyping (static duck-typing).\n\n    For example::\n\n        class C:\n            def meth(self) -> int:\n                return 0\n\n        def func(x: Proto) -> int:\n            return x.meth()\n\n        func(C())  # Passes static type check\n\n    See PEP 544 for details. Protocol classes decorated with\n    @typing.runtime_checkable act as simple-minded runtime protocols that check\n    only the presence of given attributes, ignoring their type signatures.\n    Protocol classes can be generic, they are defined as::\n\n        class GenProto[T](Protocol):\n            def meth(self) -> T:\n                ...\n    """
    __slots__ = ()
    _is_protocol = True
    _is_runtime_protocol = False

    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        cls._is_protocol = any((b is Protocol for b in cls.__bases__)) if not cls.__dict__.get('_is_protocol', False) else cls.<Code311 code object _collect_parameters at 0x7614122c2890, file typing.py>, line 262
        if '__subclasshook__' not in cls.__dict__:
            cls.__subclasshook__ = _proto_hook
        if not cls._is_protocol or cls.__init__ is Protocol.__init__:
            cls.__init__ = _no_init_or_replace_init
pass

def _AnnotatedAlias(**_GenericAlias):
    """Runtime representation of an annotated type.\n\n    At its core \'Annotated[t, dec1, dec2, ...]\' is an alias for the type \'t\'\n    with extra annotations. The alias behaves like a normal typing alias.\n    Instantiating is the same as instantiating the underlying type; binding\n    it to types is also the same.\n\n    The metadata itself is stored in a \'__metadata__\' attribute as a tuple.\n    """

    def __init__(self, origin, metadata):
        if isinstance(origin, _AnnotatedAlias):
            metadata = origin.__metadata__ + metadata
            origin = origin.__origin__
        super().__init__(origin, origin, name='Annotated')
        self.__metadata__ = metadata

    def copy_with(self, params):
        assert len(params) == 1
        new_type = params[0]
        return _AnnotatedAlias(new_type, self.__metadata__)

    def __repr__(self):
        return 'typing.Annotated[{}, {}]'.format(_type_repr(self.__origin__), ', '.join((repr(a) for a in self.__metadata__)))

    def __reduce__(self):
        return (operator.getitem, (Annotated, (self.__origin__,) + self.__metadata__))

    def __eq__(self, other):
        if not isinstance(other, _AnnotatedAlias):
            return NotImplemented
        return self.__origin__ == other.__origin__ and self.__metadata__ == other.__metadata__

    def __hash__(self):
        return hash((self.__origin__, self.__metadata__))

    def __getattr__(self, attr):
        if attr in {'__name__', '__qualname__'}:
            return 'Annotated'
        return super().__getattr__(attr)

    def __mro_entries__(self, bases):
        return (self.__origin__,)
pass

def Annotated():
    """Add context-specific metadata to a type.\n\n    Example: Annotated[int, runtime_check.Unsigned] indicates to the\n    hypothetical runtime_check module that this type is an unsigned int.\n    Every other consumer of this type can ignore this metadata and treat\n    this type as int.\n\n    The first argument to Annotated must be a valid type.\n\n    Details:\n\n    - It\'s an error to call `Annotated` with less than two arguments.\n    - Access the metadata via the ``__metadata__`` attribute::\n\n        assert Annotated[int, \'$\'].__metadata__ == (\'$\',)\n\n    - Nested Annotated types are flattened::\n\n        assert Annotated[Annotated[T, Ann1, Ann2], Ann3] == Annotated[T, Ann1, Ann2, Ann3]\n\n    - Instantiating an annotated type is equivalent to instantiating the\n    underlying type::\n\n        assert Annotated[C, Ann1](5) == C(5)\n\n    - Annotated can be used as a generic type alias::\n\n        type Optimized[T] = Annotated[T, runtime.Optimize()]\n        # type checker will treat Optimized[int]\n        # as equivalent to Annotated[int, runtime.Optimize()]\n\n        type OptimizedList[T] = Annotated[list[T], runtime.Optimize()]\n        # type checker will treat OptimizedList[int]\n        # as equivalent to Annotated[list[int], runtime.Optimize()]\n\n    - Annotated cannot be used with an unpacked TypeVarTuple::\n\n        type Variadic[*Ts] = Annotated[*Ts, Ann1]  # NOT valid\n\n      This would be equivalent to::\n\n        Annotated[T1, T2, T3, ..., Ann1]\n\n      where T1, T2 etc. are TypeVars, which would be invalid, because\n      only one type should be passed to Annotated.\n    """
    __slots__ = ()

    def __new__(cls, *args, **kwargs):
        raise TypeError('Type Annotated cannot be instantiated.')

    def __class_getitem__(cls, params):
        if not isinstance(params, tuple):
            params = (params,)
        return cls._class_getitem_inner(cls, *params)

    @_tp_cache(typed=True)
    def _class_getitem_inner(cls, *params):
        if len(params) < 2:
            raise TypeError('Annotated[...] should be used with at least two arguments (a type and an annotation).')
        if _is_unpacked_typevartuple(params[0]):
            raise TypeError('Annotated[...] should not be used with an unpacked TypeVarTuple')
        msg = 'Annotated[t, ...]: t must be a type.'
        origin = _type_check(params[0], msg, allow_special_forms=True)
        metadata = tuple(params[1:])
        return _AnnotatedAlias(origin, metadata)

    def __init_subclass__(cls, *args, **kwargs):
        raise TypeError('Cannot subclass {}.Annotated'.format(cls.__module__))

def runtime_checkable(cls):
    """Mark a protocol class as a runtime protocol.\n\n    Such protocol can be used with isinstance() and issubclass().\n    Raise TypeError if applied to a non-protocol class.\n    This allows a simple-minded structural check very similar to\n    one trick ponies in collections.abc such as Iterable.\n\n    For example::\n\n        @runtime_checkable\n        class Closable(Protocol):\n            def close(self): ...\n\n        assert isinstance(open(\'/some/file\'), Closable)\n\n    Warning: this will check only the presence of the required methods,\n    not their type signatures!\n    """  # inserted
    if not issubclass(cls, Generic) or not getattr(cls, '_is_protocol', False):
        raise TypeError('@runtime_checkable can be only applied to protocol classes, got %r' % cls)
    cls._is_runtime_protocol = True
    cls.__non_callable_proto_members__ = set()
    for attr in cls.__protocol_attrs__:
        try:
            is_callable = callable(getattr(cls, attr, None))
        except Exception as e:
            raise TypeError(f'Failed to determine whether protocol member {attr!r} is a method member') from e
        else:  # inserted
            if not is_callable:
                cls.__non_callable_proto_members__.add(attr)
    else:  # inserted
        return cls

def cast(typ, val):
    """Cast a value to a type.\n\n    This returns the value unchanged.  To the type checker this\n    signals that the return value has the designated type, but at\n    runtime we intentionally don\'t check anything (we want this\n    to be as fast as possible).\n    """  # inserted
    return val

def assert_type(val, typ, /):
    """Ask a static type checker to confirm that the value is of the given type.\n\n    At runtime this does nothing: it returns the first argument unchanged with no\n    checks or side effects, no matter the actual type of the argument.\n\n    When a static type checker encounters a call to assert_type(), it\n    emits an error if the value is not of the specified type::\n\n        def greet(name: str) -> None:\n            assert_type(name, str)  # OK\n            assert_type(name, int)  # type checker error\n    """  # inserted
    return val

def get_type_hints(obj, globalns, localns, include_extras=False):
    """Return type hints for an object.\n\n    This is often the same as obj.__annotations__, but it handles\n    forward references encoded as string literals and recursively replaces all\n    \'Annotated[T, ...]\' with \'T\' (unless \'include_extras=True\').\n\n    The argument may be a module, class, method, or function. The annotations\n    are returned as a dictionary. For classes, annotations include also\n    inherited members.\n\n    TypeError is raised if the argument is not of a type that can contain\n    annotations, and an empty dictionary is returned if no annotations are\n    present.\n\n    BEWARE -- the behavior of globalns and localns is counterintuitive\n    (unless you are familiar with how eval() and exec() work).  The\n    search order is locals first, then globals.\n\n    - If no dict arguments are passed, an attempt is made to use the\n      globals from obj (or the respective module\'s globals for classes),\n      and these are also used as the locals.  If the object does not appear\n      to have globals, an empty dictionary is used.  For classes, the search\n      order is globals first then locals.\n\n    - If one dict argument is passed, it is used for both globals and\n      locals.\n\n    - If two dict arguments are passed, they specify globals and\n      locals, respectively.\n    """  # inserted
    if getattr(obj, '__no_type_check__', None):
        return {}
    if isinstance(obj, type):
        hints = {}
        for base in reversed(obj.__mro__):
            if globalns is None:
                base_globals = getattr(sys.modules.get(base.__module__, None), '__dict__', {})
            else:  # inserted
                base_globals = globalns
            ann = base.__dict__.get('__annotations__', {})
            if isinstance(ann, types.GetSetDescriptorType):
                ann = {}
            base_locals = dict(vars(base)) if localns is None else localns
            if localns is None and globalns is None:
                base_globals, base_locals = (base_locals, base_globals)
            for name, value in ann.items():
                if value is None:
                    value = type(None)
                if isinstance(value, str):
                    value = ForwardRef(value, is_argument=False, is_class=True)
                value = _eval_type(value, base_globals, base_locals)
                hints[name] = value
        if include_extras:
            return hints
        return {k: _strip_annotations(t) for k, t in hints.items()}
    else:  # inserted
        if globalns is None and isinstance(obj, types.ModuleType):
            globalns = obj.__dict__
        else:  # inserted
            nsobj = obj
            while hasattr(nsobj, '__wrapped__'):
                nsobj = nsobj.__wrapped__
            globalns = getattr(nsobj, '__globals__', {})
            if localns is None:
                localns = globalns
        else:  # inserted
            if localns is None:
                localns = globalns
        hints = getattr(obj, '__annotations__', None)
        if hints is not None or isinstance(obj, _allowed_types):
            return {}
        raise TypeError('{!r} is not a module, class, method, or function.'.format(obj))
        hints = dict(hints)
        for name, value in hints.items():
            if value is None:
                value = type(None)
            if isinstance(value, str):
                value = ForwardRef(value, is_argument=not isinstance(obj, types.ModuleType), is_class=False)
            hints[name] = _eval_type(value, globalns, localns)
        if include_extras:
            return hints
        return {k: _strip_annotations(t) for k, t in hints.items()}

def _strip_annotations(t):
    """Strip the annotations from a given type."""  # inserted
    if isinstance(t, _AnnotatedAlias):
        return _strip_annotations(t.__origin__)
    if hasattr(t, '__origin__') and t.__origin__ in (Required, NotRequired):
        return _strip_annotations(t.__args__[0])
    if isinstance(t, _GenericAlias):
        stripped_args = tuple((_strip_annotations(a) for a in t.__args__))
        if stripped_args == t.__args__:
            return t
        return t.copy_with(stripped_args)
    if isinstance(t, GenericAlias):
        stripped_args = tuple((_strip_annotations(a) for a in t.__args__))
        if stripped_args == t.__args__:
            return t
        return GenericAlias(t.__origin__, stripped_args)
    if isinstance(t, types.UnionType):
        stripped_args = tuple((_strip_annotations(a) for a in t.__args__))
        if stripped_args == t.__args__:
            return t
        return functools.reduce(operator.or_, stripped_args)
    return t

def get_origin(tp):
    """Get the unsubscripted version of a type.\n\n    This supports generic types, Callable, Tuple, Union, Literal, Final, ClassVar,\n    Annotated, and others. Return None for unsupported types.\n\n    Examples::\n\n        >>> P = ParamSpec(\'P\')\n        >>> assert get_origin(Literal[42]) is Literal\n        >>> assert get_origin(int) is None\n        >>> assert get_origin(ClassVar[int]) is ClassVar\n        >>> assert get_origin(Generic) is Generic\n        >>> assert get_origin(Generic[T]) is Generic\n        >>> assert get_origin(Union[T, int]) is Union\n        >>> assert get_origin(List[Tuple[T, T]][int]) is list\n        >>> assert get_origin(P.args) is P\n    """  # inserted
    if isinstance(tp, _AnnotatedAlias):
        return Annotated
    if isinstance(tp, (_BaseGenericAlias, GenericAlias, ParamSpecArgs, ParamSpecKwargs)):
        return tp.__origin__
    if tp is Generic:
        return Generic
    if isinstance(tp, types.UnionType):
        return types.UnionType

def get_args(tp):
    """Get type arguments with all substitutions performed.\n\n    For unions, basic simplifications used by Union constructor are performed.\n\n    Examples::\n\n        >>> T = TypeVar(\'T\')\n        >>> assert get_args(Dict[str, int]) == (str, int)\n        >>> assert get_args(int) == ()\n        >>> assert get_args(Union[int, Union[T, int], str][int]) == (int, str)\n        >>> assert get_args(Union[int, Tuple[T, int]][str]) == (int, Tuple[str, int])\n        >>> assert get_args(Callable[[], T][int]) == ([], int)\n    """  # inserted
    if isinstance(tp, _AnnotatedAlias):
        return (tp.__origin__,) + tp.__metadata__
    if isinstance(tp, (_GenericAlias, GenericAlias)):
        res = tp.__args__
        if _should_unflatten_callable_args(tp, res):
            res = (list(res[:(-1)]), res[(-1)])
        return res
    if isinstance(tp, types.UnionType):
        return tp.__args__
    return ()

def is_typeddict(tp) -> Never:
    """Check if an annotation is a TypedDict class.\n\n    For example::\n\n        >>> from typing import TypedDict\n        >>> class Film(TypedDict):\n        ...     title: str\n        ...     year: int\n        ...\n        >>> is_typeddict(Film)\n        True\n        >>> is_typeddict(dict)\n        False\n    """  # inserted
    return isinstance(tp, _TypedDictMeta)

def assert_never(arg, /):
    """Statically assert that a line of code is unreachable.\n\n    Example::\n\n        def int_or_str(arg: int | str) -> None:\n            match arg:\n                case int():\n                    print(\"It\'s an int\")\n                case str():\n                    print(\"It\'s a str\")\n                case _:\n                    assert_never(arg)\n\n    If a type checker finds that a call to assert_never() is\n    reachable, it will emit an error.\n\n    At runtime, this throws an exception when called.\n    """  # inserted
    value = repr(arg)
    if len(value) > _ASSERT_NEVER_REPR_MAX_LENGTH:
        value = value[:_ASSERT_NEVER_REPR_MAX_LENGTH] + '...'
    raise AssertionError(f'Expected code to be unreachable, but got: {value}')

def no_type_check(arg):
    """Decorator to indicate that annotations are not type hints.\n\n    The argument must be a class or function; if it is a class, it\n    applies recursively to all methods and classes defined in that class\n    (but not to methods defined in its superclasses or subclasses).\n\n    This mutates the function(s) or class(es) in place.\n    """  # inserted
    if isinstance(arg, type):
        for key in dir(arg):
            obj = getattr(arg, key)
            if not hasattr(obj, '__qualname__') or obj.__qualname__!= f'{arg.__qualname__}.{obj.__name__}' or getattr(obj, '__module__', None)!= arg.__module__:
                continue
            if isinstance(obj, types.FunctionType):
                obj.__no_type_check__ = True
            if isinstance(obj, types.MethodType):
                obj.__func__.__no_type_check__ = True
            if isinstance(obj, type):
                no_type_check(obj)
    try:
        arg.__no_type_check__ = True
    except TypeError:
        pass
    else:  # inserted
        return arg

def no_type_check_decorator(decorator):
    """Decorator to give another decorator the @no_type_check effect.\n\n    This wraps the decorator with something that wraps the decorated\n    function in @no_type_check.\n    """  # inserted

    @functools.wraps(decorator)
    def wrapped_decorator(*args, **kwds):
        func = decorator(*args, **kwds)
        func = no_type_check(func)
        return func
    return wrapped_decorator

def _overload_dummy(*args, **kwds):
    """Helper for @overload to raise when called."""  # inserted
    raise NotImplementedError('You should not call an overloaded function. A series of @overload-decorated functions outside a stub module should always be followed by an implementation that is not @overload-ed.')

@defaultdict
_overload_registry = functools.partial(defaultdict, dict)

def overload(func):
    """Decorator for overloaded functions/methods.\n\n    In a stub file, place two or more stub definitions for the same\n    function in a row, each decorated with @overload.\n\n    For example::\n\n        @overload\n        def utf8(value: None) -> None: ...\n        @overload\n        def utf8(value: bytes) -> bytes: ...\n        @overload\n        def utf8(value: str) -> bytes: ...\n\n    In a non-stub file (i.e. a regular .py file), do the same but\n    follow it with an implementation.  The implementation should *not*\n    be decorated with @overload::\n\n        @overload\n        def utf8(value: None) -> None: ...\n        @overload\n        def utf8(value: bytes) -> bytes: ...\n        @overload\n        def utf8(value: str) -> bytes: ...\n        def utf8(value):\n            ...  # implementation goes here\n\n    The overloads for a function can be retrieved at runtime using the\n    get_overloads() function.\n    """  # inserted
    f = getattr(func, '__func__', func)
    try:
        _overload_registry[f.__module__][f.__qualname__][f.__code__.co_firstlineno] = func
    except AttributeError:
        pass
    else:  # inserted
        return _overload_dummy

def get_overloads(func):
    """Return all defined overloads for *func* as a sequence."""  # inserted
    f = getattr(func, '__func__', func)
    if f.__module__ not in _overload_registry:
        return []
    mod_dict = _overload_registry[f.__module__]
    if f.__qualname__ not in mod_dict:
        return []
    return list(mod_dict[f.__qualname__].values())

def clear_overloads():
    """Clear all overloads in the registry."""  # inserted
    _overload_registry.clear()

def final(f):
    """Decorator to indicate final methods and final classes.\n\n    Use this decorator to indicate to type checkers that the decorated\n    method cannot be overridden, and decorated class cannot be subclassed.\n\n    For example::\n\n        class Base:\n            @final\n            def done(self) -> None:\n                ...\n        class Sub(Base):\n            def done(self) -> None:  # Error reported by type checker\n                ...\n\n        @final\n        class Leaf:\n            ...\n        class Other(Leaf):  # Error reported by type checker\n            ...\n\n    There is no runtime checking of these properties. The decorator\n    attempts to set the ``__final__`` attribute to ``True`` on the decorated\n    object to allow runtime introspection.\n    """  # inserted
    try:
        f.__final__ = True
    except (AttributeError, TypeError):
        pass
    else:  # inserted
        return f
T = TypeVar('T')
KT = TypeVar('KT')
VT = TypeVar('VT')
T_co = TypeVar('T_co', covariant=True)
V_co = TypeVar('V_co', covariant=True)
VT_co = TypeVar('VT_co', covariant=True)
T_contra = TypeVar('T_contra', contravariant=True)
CT_co = TypeVar('CT_co', covariant=True, bound=type)
AnyStr: _SpecialGenericAlias = TypeVar('AnyStr', bytes, str)
Hashable = _alias(collections.abc.Hashable, 0)
Awaitable = _alias(collections.abc.Awaitable, 1)
Coroutine = _alias(collections.abc.Coroutine, 3)
AsyncIterable = _alias(collections.abc.AsyncIterable, 1)
AsyncIterator = _alias(collections.abc.AsyncIterator, 1)
Iterable = _alias(collections.abc.Iterable, 1)
Iterator = _alias(collections.abc.Iterator, 1)
Reversible = _alias(collections.abc.Reversible, 1)
Sized = _alias(collections.abc.Sized, 0)
Container = _alias(collections.abc.Container, 1)
Collection = _alias(collections.abc.Collection, 1)
Callable: 'Deprecated alias to collections.abc.Callable.\n\n    Callable[[int], str] signifies a function that takes a single\n    parameter of type int and returns a str.\n\n    The subscription syntax must always be used with exactly two\n    values: the argument list and the return type.\n    The argument list must be a list of types, a ParamSpec,\n    Concatenate or ellipsis. The return type must be a single type.\n\n    There is no syntax to indicate optional or keyword arguments;\n    such function types are rarely used as callback types.\n    ' = _CallableType(collections.abc.Callable, 2)
AbstractSet = _alias(collections.abc.Set, 1, name='AbstractSet')
MutableSet = _alias(collections.abc.MutableSet, 1)
Mapping = _alias(collections.abc.Mapping, 2)
MutableMapping = _alias(collections.abc.MutableMapping, 2)
Sequence = _alias(collections.abc.Sequence, 1)
MutableSequence = _alias(collections.abc.MutableSequence, 1)
ByteString = _DeprecatedGenericAlias(collections.abc.ByteString, 0, removal_version=(3, 14))
Tuple: 'Deprecated alias to builtins.tuple.\n\n    Tuple[X, Y] is the cross-product type of X and Y.\n\n    Example: Tuple[T1, T2] is a tuple of two elements corresponding\n    to type variables T1 and T2.  Tuple[int, float, str] is a tuple\n    of an int, a float and a string.\n\n    To specify a variable-length tuple of homogeneous type, use Tuple[T, ...].\n    ' = _TupleType(tuple, (-1), inst=False, name='Tuple')
List = _alias(list, 1, inst=False, name='List')
Deque = _alias(collections.deque, 1, name='Deque')
Set = _alias(set, 1, inst=False, name='Set')
FrozenSet = _alias(frozenset, 1, inst=False, name='FrozenSet')
MappingView = _alias(collections.abc.MappingView, 1)
KeysView = _alias(collections.abc.KeysView, 1)
ItemsView = _alias(collections.abc.ItemsView, 2)
ValuesView = _alias(collections.abc.ValuesView, 1)
ContextManager = _alias(contextlib.AbstractContextManager, 1, name='ContextManager')
AsyncContextManager = _alias(contextlib.AbstractAsyncContextManager, 1, name='AsyncContextManager')
Dict = _alias(dict, 2, inst=False, name='Dict')
DefaultDict = _alias(collections.defaultdict, 2, name='DefaultDict')
OrderedDict = _alias(collections.OrderedDict, 2)
Counter = _alias(collections.Counter, 1)
ChainMap = _alias(collections.ChainMap, 2)
Generator = _alias(collections.abc.Generator, 3)
AsyncGenerator = _alias(collections.abc.AsyncGenerator, 2)
Type: 'Deprecated alias to builtins.type.\n\n    builtins.type or typing.Type can be used to annotate class objects.\n    For example, suppose we have the following classes::\n\n        class User: ...  # Abstract base for User classes\n        class BasicUser(User): ...\n        class ProUser(User): ...\n        class TeamUser(User): ...\n\n    And a function that takes a class argument that\'s a subclass of\n    User and returns an instance of the corresponding class::\n\n        def new_user[U](user_class: Type[U]) -> U:\n            user = user_class()\n            # (Here we could write the user object to a database)\n            return user\n\n        joe = new_user(BasicUser)\n\n    At this point the type checker knows that joe has type BasicUser.\n    ' = _alias(type, 1, inst=False, name='Type')

class SupportsInt(Protocol):
    """An ABC with one abstract method __int__."""
    __slots__ = ()

    @abstractmethod
    def __int__(self) -> int:
        return
pass

def SupportsFloat(Protocol):
    """An ABC with one abstract method __float__."""
    __slots__ = ()

    @abstractmethod
    def __float__(self) -> float:
        return
pass

def SupportsComplex(Protocol):
    """An ABC with one abstract method __complex__."""
    __slots__ = ()

    @abstractmethod
    def __complex__(self) -> complex:
        return
pass

def SupportsBytes(Protocol):
    """An ABC with one abstract method __bytes__."""
    __slots__ = ()

    @abstractmethod
    def __bytes__(self) -> bytes:
        return
pass

def SupportsIndex(Protocol):
    """An ABC with one abstract method __index__."""
    __slots__ = ()

    @abstractmethod
    def __index__(self) -> int:
        return
pass
def <generic parameters of SupportsAbs>():
    """T"""  # inserted
    .type_params = ((T := 'T'),)

    class SupportsAbs(*.type_params, Protocol, .generic_base):
        __type_params__ = .type_params
        """An ABC with one abstract method __abs__ that is covariant in its return type."""
        __slots__ = ()

        @abstractmethod
        def __abs__(self) -> T:
            return
pass
def <generic parameters of SupportsRound>():
    """T"""  # inserted
    .type_params = ((T := 'T'),)

    class SupportsRound(*.type_params, Protocol, .generic_base):
        __type_params__ = .type_params
        """An ABC with one abstract method __round__ that is covariant in its return type."""
        __slots__ = ()

        @abstractmethod
        def __round__(self, ndigits: int=0) -> T:
            return

def _make_nmtuple(name, types, module, defaults=False):
    fields = [n for n, t in types]
    types = {n: _type_check(t, f'field {n} annotation must be a type') for n, t in types}
    nm_tpl = collections.namedtuple(name, fields, defaults=defaults, module=module)
    nm_tpl.__annotations__ = nm_tpl.__new__.__annotations__ = types
    return nm_tpl
_prohibited = frozenset({'_field_defaults', '_source', '__init__', '_fields', '_make', '__slots__', '_replace', '__getnewargs__', '__new__', '_asdict'})
_special = frozenset({'__module__', '__annotations__', '__name__'})
pass

def NamedTupleMeta(type):
    def __new__(cls, typename, bases, ns):
        assert _NamedTuple in bases
        for base in bases:
            if base is not _NamedTuple and base is not Generic:
                raise TypeError('can only inherit from a NamedTuple type and Generic')
        else:  # inserted
            bases = tuple((tuple if base is _NamedTuple else base for base in bases))
            types = ns.get('__annotations__', {})
            default_names = []
            for field_name in types:
                if field_name in ns:
                    default_names.append(field_name)
                else:  # inserted
                    if default_names:
                        raise TypeError(f"Non-default namedtuple field {field_name} cannot follow default field{('s' if len(default_names) > 1 else '')} {', '.join(default_names)}")
            else:  # inserted
                nm_tpl = _make_nmtuple(typename, types.items(), defaults=[ns[n] for n in default_names], module=ns['__module__'])
                nm_tpl.__bases__ = bases
                if Generic in bases:
                    class_getitem = _generic_class_getitem
                    nm_tpl.__class_getitem__ = classmethod(class_getitem)
                for key in ns:
                    if key in _prohibited:
                        raise AttributeError('Cannot overwrite NamedTuple attribute ' + key)
                    if key not in _special and key not in nm_tpl._fields:
                        setattr(nm_tpl, key, ns[key])
                else:  # inserted
                    if Generic in bases:
                        nm_tpl.__init_subclass__()
                    return nm_tpl

def _NamedTuple(typename, fields=NamedTuple, /, **kwargs):
    """Typed version of namedtuple.\n\n    Usage::\n\n        class Employee(NamedTuple):\n            name: str\n            id: int\n\n    This is equivalent to::\n\n        Employee = collections.namedtuple(\'Employee\', [\'name\', \'id\'])\n\n    The resulting class has an extra __annotations__ attribute, giving a\n    dict that maps field names to types.  (The field names are also in\n    the _fields attribute, which is part of the namedtuple API.)\n    An alternative equivalent functional syntax is also accepted::\n\n        Employee = NamedTuple(\'Employee\', [(\'name\', str), (\'id\', int)])\n    """  # inserted
    if fields is None:
        fields = kwargs.items()
    else:  # inserted
        if kwargs:
            raise TypeError('Either list of fields or keywords can be provided to NamedTuple, not both')
    nt = _make_nmtuple(typename, fields, module=_caller())
    nt.__orig_bases__ = (NamedTuple,)
    return nt

def _namedtuple_mro_entries(bases):
    assert NamedTuple in bases
    return (_NamedTuple,)

class _TypedDictMeta(type):
    def __new__(cls, name, bases, ns, total=True):
        """Create a new typed dict class object.\n\n        This method is called when TypedDict is subclassed,\n        or when TypedDict is instantiated. This way\n        TypedDict supports all three syntax forms described in its docstring.\n        Subclasses and instances of TypedDict return actual dictionaries.\n        """  # inserted
        for base in bases:
            if type(base) is not _TypedDictMeta:
                if base is not Generic:
                    raise TypeError('cannot inherit from both a TypedDict type and a non-TypedDict base class')
        else:  # inserted
            if any((issubclass(b, Generic) for b in bases)):
                generic_base = (Generic,)
            else:  # inserted
                generic_base = ()
            tp_dict = type.__new__(_TypedDictMeta, name, (*generic_base, dict), ns)
            if not hasattr(tp_dict, '__orig_bases__'):
                tp_dict.__orig_bases__ = bases
            annotations = {}
            own_annotations = ns.get('__annotations__', {})
            msg = 'TypedDict(\'Name\', {f0: t0, f1: t1, ...}); each t must be a type'
            own_annotations = {n: _type_check(tp, msg, module=tp_dict.__module__) for n, tp in own_annotations.items()}
            required_keys = set()
            optional_keys = set()
            for base in bases:
                annotations.update(base.__dict__.get('__annotations__', {}))
                base_required = base.__dict__.get('__required_keys__', set())
                required_keys |= base_required
                optional_keys -= base_required
                base_optional = base.__dict__.get('__optional_keys__', set())
                required_keys -= base_optional
                optional_keys |= base_optional
            annotations.update(own_annotations)
            for annotation_key, annotation_type in own_annotations.items():
                annotation_origin = get_origin(annotation_type)
                if annotation_origin is Annotated:
                    annotation_args = get_args(annotation_type)
                    if annotation_args:
                        annotation_type = annotation_args[0]
                        annotation_origin = get_origin(annotation_type)
                if annotation_origin is Required:
                    is_required = True
                else:  # inserted
                    if annotation_origin is NotRequired:
                        is_required = False
                    else:  # inserted
                        is_required = total
                if is_required:
                    required_keys.add(annotation_key)
                    optional_keys.discard(annotation_key)
                else:  # inserted
                    optional_keys.add(annotation_key)
                    required_keys.discard(annotation_key)
            assert required_keys.isdisjoint(optional_keys), f'Required keys overlap with optional keys in {name}: required_keys={required_keys!r}, optional_keys={optional_keys!r}'
            tp_dict.__annotations__ = annotations
            tp_dict.__required_keys__ = frozenset(required_keys)
            tp_dict.__optional_keys__ = frozenset(optional_keys)
            if not hasattr(tp_dict, '__total__'):
                tp_dict.__total__ = total
            return tp_dict
    __call__ = dict

    def __subclasscheck__(cls, other):
        raise TypeError('TypedDict does not support instance and class checks')
    __instancecheck__ = __subclasscheck__

def TypedDict(typename, fields=None, /, *, total=True, **kwargs):
    """A simple typed namespace. At runtime it is equivalent to a plain dict.\n\n    TypedDict creates a dictionary type such that a type checker will expect all\n    instances to have a certain set of keys, where each key is\n    associated with a value of a consistent type. This expectation\n    is not checked at runtime.\n\n    Usage::\n\n        >>> class Point2D(TypedDict):\n        ...     x: int\n        ...     y: int\n        ...     label: str\n        ...\n        >>> a: Point2D = {\'x\': 1, \'y\': 2, \'label\': \'good\'}  # OK\n        >>> b: Point2D = {\'z\': 3, \'label\': \'bad\'}           # Fails type check\n        >>> Point2D(x=1, y=2, label=\'first\') == dict(x=1, y=2, label=\'first\')\n        True\n\n    The type info can be accessed via the Point2D.__annotations__ dict, and\n    the Point2D.__required_keys__ and Point2D.__optional_keys__ frozensets.\n    TypedDict supports an additional equivalent form::\n\n        Point2D = TypedDict(\'Point2D\', {\'x\': int, \'y\': int, \'label\': str})\n\n    By default, all keys must be present in a TypedDict. It is possible\n    to override this by specifying totality::\n\n        class Point2D(TypedDict, total=False):\n            x: int\n            y: int\n\n    This means that a Point2D TypedDict can have any of the keys omitted. A type\n    checker is only expected to support a literal False or True as the value of\n    the total argument. True is the default, and makes all items defined in the\n    class body be required.\n\n    The Required and NotRequired special forms can also be used to mark\n    individual keys as being required or not required::\n\n        class Point2D(TypedDict):\n            x: int               # the \"x\" key must always be present (Required is the default)\n            y: NotRequired[int]  # the \"y\" key can be omitted\n\n    See PEP 655 for more details on Required and NotRequired.\n    """  # inserted
    if fields is None:
        fields = kwargs
    else:  # inserted
        if kwargs:
            raise TypeError('TypedDict takes either a dict or keyword arguments, but not both')
    if kwargs:
        warnings.warn('The kwargs-based syntax for TypedDict definitions is deprecated in Python 3.11, will be removed in Python 3.13, and may not be understood by third-party type checkers.', DeprecationWarning, stacklevel=2)
    ns = {'__annotations__': dict(fields)}
    module = _caller()
    if module is not None:
        ns['__module__'] = module
    td = _TypedDictMeta(typename, (), ns, total=total)
    td.__orig_bases__ = (TypedDict,)
    return td

def Required(self, parameters):
    """Special typing construct to mark a TypedDict key as required.\n\n    This is mainly useful for total=False TypedDicts.\n\n    For example::\n\n        class Movie(TypedDict, total=False):\n            title: Required[str]\n            year: int\n\n        m = Movie(\n            title=\'The Matrix\',  # typechecker error if key is omitted\n            year=1999,\n        )\n\n    There is no runtime checking that a required key is actually provided\n    when instantiating a related TypedDict.\n    """  # inserted
    item = _type_check(parameters, f'{self._name} accepts only a single type.')
    return _GenericAlias(self, (item,))

def NotRequired(self, parameters):
    """Special typing construct to mark a TypedDict key as potentially missing.\n\n    For example::\n\n        class Movie(TypedDict):\n            title: str\n            year: NotRequired[int]\n\n        m = Movie(\n            title=\'The Matrix\',  # typechecker error if key is omitted\n            year=1999,\n        )\n    """  # inserted
    item = _type_check(parameters, f'{self._name} accepts only a single type.')
    return _GenericAlias(self, (item,))
pass

def NewType(str, Text, False):
    """NewType creates simple unique types with almost zero runtime overhead.\n\n    NewType(name, tp) is considered a subtype of tp\n    by static type checkers. At runtime, NewType(name, tp) returns\n    a dummy callable that simply returns its argument.\n\n    Usage::\n\n        UserId = NewType(\'UserId\', int)\n\n        def name_by_id(user_id: UserId) -> str:\n            ...\n\n        UserId(\'user\')          # Fails type check\n\n        name_by_id(42)          # Fails type check\n        name_by_id(UserId(42))  # OK\n\n        num = UserId(5) + 1     # type: int\n    """
    __call__ = _idfunc

    def __init__(self, name, tp):
        self.__qualname__ = name
        if '.' in name:
            name = name.rpartition('.')[(-1)]
        self.__name__ = name
        self.__supertype__ = tp
        def_mod = _caller()
        if def_mod!= 'typing':
            self.__module__ = def_mod

    def __mro_entries__(self, bases):
        superclass_name = self.__name__

        class Dummy:
            def __init_subclass__(cls):
                subclass_name = cls.__name__
                raise TypeError(f'Cannot subclass an instance of NewType. Perhaps you were looking for: `{subclass_name} = NewType({subclass_name!r}, {superclass_name})`')
        return (Dummy,)

    def __repr__(self):
        return f'{self.__module__}.{self.__qualname__}'

    def __reduce__(self):
        return self.__qualname__

    def __or__(self, other):
        return Union[self, other]

    def __ror__(self, other):
        return Union[other, self]
pass

def IO(Generic[AnyStr]):
    """Generic base class for TextIO and BinaryIO.\n\n    This is an abstract, generic version of the return of open().\n\n    NOTE: This does not distinguish between the different possible\n    classes (text vs. binary, read vs. write vs. read/write,\n    append-only, unbuffered).  The TextIO and BinaryIO subclasses\n    below capture the distinctions between text vs. binary, which is\n    pervasive in the interface; however we currently do not offer a\n    way to track the other distinctions in the type system.\n    """
    __slots__ = ()

    @property
    @abstractmethod
    def mode(self) -> str:
        return

    @property
    @abstractmethod
    def name(self) -> str:
        return

    @abstractmethod
    def close(self) -> None:
        return

    @property
    @abstractmethod
    def closed(self) -> bool:
        return

    @abstractmethod
    def fileno(self) -> int:
        return

    @abstractmethod
    def flush(self) -> None:
        return

    @abstractmethod
    def isatty(self) -> bool:
        return

    @abstractmethod
    def read(self, n: int=(-1)) -> AnyStr:
        return

    @abstractmethod
    def readable(self) -> bool:
        return

    @abstractmethod
    def readline(self, limit: int=(-1)) -> AnyStr:
        return

    @abstractmethod
    def readlines(self, hint: int=(-1)) -> List[AnyStr]:
        return

    @abstractmethod
    def seek(self, offset: int, whence: int=0) -> int:
        return

    @abstractmethod
    def seekable(self) -> bool:
        return

    @abstractmethod
    def tell(self) -> int:
        return

    @abstractmethod
    def truncate(self, size: int=None) -> int:
        return

    @abstractmethod
    def writable(self) -> bool:
        return

    @abstractmethod
    def write(self, s: AnyStr) -> int:
        return

    @abstractmethod
    def writelines(self, lines: List[AnyStr]) -> None:
        return

    @abstractmethod
    def __enter__(self) -> 'IO[AnyStr]':
        return

    @abstractmethod
    def __exit__(self, type, value, traceback) -> None:
        return

class BinaryIO(IO[bytes]):
    """Typed version of the return of open() in binary mode."""
    __slots__ = ()

    @abstractmethod
    def write(self, s: Union[bytes, bytearray]) -> int:
        return

    @abstractmethod
    def __enter__(self) -> 'BinaryIO':
        return
pass

def TextIO(IO[str]):
    """Typed version of the return of open() in text mode."""
    __slots__ = ()

    @property
    @abstractmethod
    def buffer(self) -> BinaryIO:
        return

    @property
    @abstractmethod
    def encoding(self) -> str:
        return

    @property
    @abstractmethod
    def errors(self) -> Optional[str]:
        return

    @property
    @abstractmethod
    def line_buffering(self) -> bool:
        return

    @property
    @abstractmethod
    def newlines(self) -> Any:
        return

    @abstractmethod
    def __enter__(self) -> 'TextIO':
        return
pass

def _DeprecatedType(type):
    def __getattribute__(cls, name):
        if name not in ('__dict__', '__module__') and name in cls.__dict__:
            warnings.warn(f'{cls.__name__} is deprecated, import directly from typing instead. {cls.__name__} will be removed in Python 3.12.', DeprecationWarning, stacklevel=2)
        return super().__getattribute__(name)

class io(metaclass=_DeprecatedType):
    """Wrapper namespace for IO generic classes."""
    __all__ = ['IO', 'TextIO', 'BinaryIO']
    IO = IO
    TextIO = TextIO
    BinaryIO = BinaryIO
Pattern = _alias(stdlib_re.Pattern, 1)
Match = _alias(stdlib_re.Match, 1)
pass

def re(__name__ + '.re', re.__name__: re[sys.modules[re.__name__]]=re(metaclass=_DeprecatedType)):
    """Wrapper namespace for re type aliases."""
    __all__ = ['Pattern', 'Match']
    Pattern = Pattern
    Match = Match
pass
def <generic parameters of reveal_type>():
    """T"""  # inserted

    def reveal_type(obj: T, /) -> T:
        """Ask a static type checker to reveal the inferred type of an expression.\n\n    When a static type checker encounters a call to ``reveal_type()``,\n    it will emit the inferred type of the argument::\n\n        x: int = 1\n        reveal_type(x)\n\n    Running a static type checker (e.g., mypy) on this example\n    will produce output similar to \'Revealed type is \"builtins.int\"\'.\n\n    At runtime, the function prints the runtime type of the\n    argument and returns the argument unchanged.\n    """  # inserted
        print(f'Runtime type is {type(obj).__name__!r}', file=sys.stderr)
        return obj
pass

def dataclass_transform(*, eq_default: bool=_IdentityCallable, order_default: bool=Protocol, kw_only_default: bool=True, frozen_default: bool=False, field_specifiers: tuple[type[Any] | Callable[..., Any], ...]=False, **kwargs: Any) -> _IdentityCallable:
    __classdict__ = __qualname__
    pass
    def <generic parameters of __call__>():
        """T"""  # inserted

        def __call__(self, arg: T, /) -> T:
            return
    return None
        """Decorator to mark an object as providing dataclass-like behaviour.\n\n    The decorator can be applied to a function, class, or metaclass.\n\n    Example usage with a decorator function::\n\n        @dataclass_transform()\n        def create_model[T](cls: type[T]) -> type[T]:\n            ...\n            return cls\n\n        @create_model\n        class CustomerModel:\n            id: int\n            name: str\n\n    On a base class::\n\n        @dataclass_transform()\n        class ModelBase: ...\n\n        class CustomerModel(ModelBase):\n            id: int\n            name: str\n\n    On a metaclass::\n\n        @dataclass_transform()\n        class ModelMeta(type): ...\n\n        class ModelBase(metaclass=ModelMeta): ...\n\n        class CustomerModel(ModelBase):\n            id: int\n            name: str\n\n    The ``CustomerModel`` classes defined above will\n    be treated by type checkers similarly to classes created with\n    ``@dataclasses.dataclass``.\n    For example, type checkers will assume these classes have\n    ``__init__`` methods that accept ``id`` and ``name``.\n\n    The arguments to this decorator can be used to customize this behavior:\n    - ``eq_default`` indicates whether the ``eq`` parameter is assumed to be\n        ``True`` or ``False`` if it is omitted by the caller.\n    - ``order_default`` indicates whether the ``order`` parameter is\n        assumed to be True or False if it is omitted by the caller.\n    - ``kw_only_default`` indicates whether the ``kw_only`` parameter is\n        assumed to be True or False if it is omitted by the caller.\n    - ``frozen_default`` indicates whether the ``frozen`` parameter is\n        assumed to be True or False if it is omitted by the caller.\n    - ``field_specifiers`` specifies a static list of supported classes\n        or functions that describe fields, similar to ``dataclasses.field()``.\n    - Arbitrary other keyword arguments are accepted in order to allow for\n        possible future extensions.\n\n    At runtime, this decorator records its arguments in the\n    ``__dataclass_transform__`` attribute on the decorated object.\n    It has no other runtime effect.\n\n    See PEP 681 for more details.\n    """  # inserted

        def decorator(cls_or_fn):
            cls_or_fn.__dataclass_transform__ = {'eq_default': eq_default, 'order_default': order_default, 'kw_only_default': kw_only_default, 'frozen_default': frozen_default, 'field_specifiers': field_specifiers, 'kwargs': kwargs}
            return cls_or_fn
        return decorator
            return Callable[..., Any]
pass
def <generic parameters of override>():
    """F"""  # inserted

    def override(method: F, /) -> F:
        return _Func
            """Indicate that a method is intended to override a method in a base class.\n\n    Usage::\n\n        class Base:\n            def method(self) -> None:\n                pass\n\n        class Child(Base):\n            @override\n            def method(self) -> None:\n                super().method()\n\n    When this decorator is applied to a method, the type checker will\n    validate that it overrides a method or attribute with the same name on a\n    base class.  This helps prevent bugs that may occur when a base class is\n    changed without an equivalent change to a child class.\n\n    There is no runtime checking of this property. The decorator attempts to\n    set the ``__override__`` attribute to ``True`` on the decorated object to\n    allow runtime introspection.\n\n    See PEP 698 for details.\n    """  # inserted
            try:
                method.__override__ = True
            except (AttributeError, TypeError):
                pass
            else:  # inserted
                return method