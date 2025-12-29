from typing import Any, Callable, Type, Dict, Tuple, Set, List
from collections import deque
import inspect
import traceback
from pydantic import BaseModel
from typing_extensions import get_origin, get_args

def is_type(value, dst_type):
    origin = get_origin(dst_type)
    if origin is None:
        return isinstance(value, dst_type)
    
    if not isinstance(value, origin):
        return False
    
    args = get_args(dst_type)
    if not args:
        return True
    
    if origin is list:
        elem_type = args[0]
        return all(is_type(item, elem_type) for item in value)
    elif origin is dict:
        key_type, value_type = args
        return all(
            is_type(k, key_type) and is_type(v, value_type)
            for k, v in value.items()
        )
    
    return True

class TypeConverter:
    def __init__(self):
        self._registry: Dict[Tuple[Type, Type], Callable[..., Any]] = {}

    def register(self, src_type: Type, dst_type: Type, func: Callable[..., Any]):
        self._registry[(src_type, dst_type)] = func

    def can_convert(self, src_type: Type, dst_type: Type) -> bool:
        return self._find_path(src_type, dst_type) is not None

    def convert(self, value: Any, dst_type: Type, **kwargs) -> Any:
        if value is None:
            return None
        
        if dst_type == Any:
            return value

        src_type = type(value)

        if is_type(value, dst_type):
            return value

        if (src_type, dst_type) in self._registry:
            return self._call_func(self._registry[(src_type, dst_type)], value, **kwargs)

        try:
            return dst_type(value)
        except Exception:
            pass

        if issubclass(dst_type, BaseModel) and isinstance(value, dict):
            return dst_type(**value)

        path = self._find_path(src_type, dst_type)
        if not path:
            raise TypeError(f"No conversion path found from {src_type.__name__} to {dst_type.__name__}.")

        result = value
        for i in range(len(path) - 1):
            func = self._registry[(path[i], path[i + 1])]
            result = self._call_func(func, result, **kwargs)
        return result

    def _call_func(self, func: Callable[..., Any], value: Any, **kwargs) -> Any:
        sig = inspect.signature(func)
        if len(sig.parameters) == 1:
            return func(value)
        else:
            return func(value, **kwargs)

    def _find_path(self, src_type: Type, dst_type: Type) -> List[Type] | None:
        if src_type == dst_type:
            return [src_type]

        graph: Dict[Type, Set[Type]] = {}
        for (s, d) in self._registry.keys():
            graph.setdefault(s, set()).add(d)

        queue = deque([[src_type]])
        visited = {src_type}

        while queue:
            path = queue.popleft()
            current = path[-1]
            for neighbor in graph.get(current, []):
                if neighbor in visited:
                    continue
                new_path = path + [neighbor]
                if neighbor == dst_type:
                    return new_path
                queue.append(new_path)
                visited.add(neighbor)
        return None