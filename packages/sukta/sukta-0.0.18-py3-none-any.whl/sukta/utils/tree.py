from typing import Any, Callable, Dict, List, Optional, Type, Union


def iter_path(
    data: Any,
    prefix: Optional[List[str]] = None,
    delim: Optional[str] = None,
    dict_type: Type = dict,
    list_type: Type = list | tuple,
    match_key: Optional[str] = None,
):
    """Generator to iterate over (key_path, value) of a nested dict/list structure (PyTree)."""
    if prefix is None:
        prefix = []
    if isinstance(data, dict_type):
        for k, v in data.items():
            if k == match_key:
                if delim is None:
                    yield prefix, v
                else:
                    yield delim.join(prefix), v
            else:
                yield from iter_path(
                    v, prefix + [k], delim, dict_type, list_type, match_key
                )
    elif isinstance(data, list_type):
        for i, v in enumerate(data):
            yield from iter_path(
                v, prefix + [str(i)], delim, dict_type, list_type, match_key
            )
    else:
        if match_key is None:
            if delim is None:
                yield prefix, data
            else:
                yield delim.join(prefix), data


def apply_vfunc(
    vfunc: Callable[[Any], Any],
    data: Any,
    dict_type: Type = dict,
    list_type: Type = list | tuple,
    preserve_ret_type: bool = True,
):
    """Apply a function on each leaf of a nested dict/list structure (PyTree)."""
    if isinstance(data, dict_type):
        ret_type = type(data) if preserve_ret_type else dict
        return ret_type(
            {k: apply_vfunc(vfunc, v, dict_type, list_type) for k, v in data.items()}
        )
    elif isinstance(data, list_type):
        ret_type = type(data) if preserve_ret_type else list
        return ret_type([apply_vfunc(vfunc, v, dict_type, list_type) for v in data])
    return vfunc(data)


def apply_pfunc(
    pfunc: Callable[[List[str], Any], Any],
    data: Any,
    prefix: Optional[List[str]] = None,
    delim: Optional[str] = None,
    dict_type: Type = dict,
    list_type: Type = list | tuple,
    preserve_ret_type: bool = True,
):
    """Apply a function on each leaf of a nested dict/list structure (PyTree), takes in path and leaf node as input."""
    if prefix is None:
        prefix = []
    if isinstance(data, dict_type):
        ret_type = type(data) if preserve_ret_type else dict
        return ret_type(
            {
                k: apply_pfunc(pfunc, v, prefix + [k], delim, dict_type, list_type)
                for k, v in data.items()
            }
        )
    elif isinstance(data, list_type):
        ret_type = type(data) if preserve_ret_type else dict
        return ret_type(
            [
                apply_pfunc(pfunc, v, prefix + [str(i)], delim, dict_type, list_type)
                for i, v in enumerate(data)
            ]
        )
    if delim is None:
        return pfunc(prefix, data)
    else:
        return pfunc(delim.join(prefix), data)


def type_cond_func(funcs: Dict[Type, Callable], fallback: Optional[Callable] = None):
    """Apply function based on the type of the input data."""

    def f(x):
        for tp, func in funcs.items():
            if isinstance(x, tp):
                return func(x)
        if fallback is not None:
            return fallback(x)
        else:
            raise ValueError(f"no function support for type {type(x)}")

    return f


def resolve_path(path: Union[str, List[str]], delim: str):
    """Convert path to list of strings if it is a string."""
    if isinstance(path, str):
        return path.split(delim)
    return path


def set_path(
    data: Any,
    path: str | List[str],
    value,
    dict_type: Type = dict,
    list_type: Type = list | tuple,
    delim: str = ".",
):
    """Set value at the given path of a nested dict/list structure (PyTree)."""
    x = data
    path = resolve_path(path, delim)
    path_len = len(path)
    for i, p in enumerate(path):
        # check if nonnegative integer
        if p.isdigit():
            p = int(p)
            if not isinstance(x, list_type):
                raise ValueError(f"Expect list/tuple type at {p}, got {type(x)}")
            if p >= len(x):
                raise IndexError(f"Index {p} out of range for list of length {len(x)}")
        else:
            if not isinstance(x, dict_type):
                raise ValueError(f"Expect dict type at {p}, got {type(x)}")
            if p not in x:
                raise KeyError(f"Key {p} not found in dict {x}")
        if i == path_len - 1:
            x[p] = value
            break
        x = x[p]
    return data


def get_path(data: Any, path: str | List[str], delim: str = "."):
    """Get value at the given path of a nested dict/list structure (PyTree)."""
    x = data
    path = resolve_path(path, delim)
    for p in path:
        x = x[p]
    return x


def has_path(data: Any, path: str | List[str], delim: str = "."):
    """Check if the given path exists in a nested dict/list structure (PyTree)."""
    x = data
    path = resolve_path(path, delim)
    for p in path:
        if p.isdigit():
            p = int(p)
            if not isinstance(x, (list, tuple)):
                return False
            if p >= len(x):
                return False
        elif p not in x:
            return False
        x = x[p]
    return True
