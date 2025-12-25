from decimal import Decimal
import multiprocessing
from typing import Optional, Tuple, Type, TypeVar, Union

from .parser import Parser


C = TypeVar('C', bound=Union[float, Decimal])


__all__: Tuple[str, ...] = (
    'evaluate',
    'create_state',
    'state'
)

state: Optional[Parser] = None


def evaluate(expr: str, max_safe_number_input: float = float('inf'), max_exponent_input: float = float('inf'), max_factorial_input: float = float('inf'), /, *, cls: Type[C] = Decimal, **kwargs) -> C:
    global state

    if not state:
        state = Parser(max_safe_number=max_safe_number_input, max_exponent=max_exponent_input, max_factorial=max_factorial_input,**kwargs)

    return state.evaluate(expr, cls=cls)


def create_state(**kwargs) -> Parser:
    return Parser(**kwargs)
