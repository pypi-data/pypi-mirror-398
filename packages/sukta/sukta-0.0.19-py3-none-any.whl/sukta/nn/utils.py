from typing import Optional, Sequence, Union

import jax.random as jr
from jaxtyping import Key

OKey = Optional[Key]


def split_support_none(key: Union[OKey, Sequence[OKey]], num: int = 2):
    if isinstance(key, Sequence):
        key = key[0]
    if key is None:
        return (None,) * num
    return jr.split(key, num)
