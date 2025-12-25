from collections.abc import Callable, Mapping, Sequence
from typing import Any, Union

SerializedAsset = list[dict]

# https://stackoverflow.com/questions/51291722/define-a-jsonable-type-using-mypy-pep-526
JsonType = Union[Sequence, Mapping, str, int, float, bool]

Callback = Callable[[Any], Any]
Getter = Union[str, Callback]
