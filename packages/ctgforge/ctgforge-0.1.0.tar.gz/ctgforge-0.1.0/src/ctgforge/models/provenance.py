from typing import Any, Union

from pydantic import BaseModel


class ProvenancedValue(BaseModel):
    value: Any
    source_path: Union[str, None] = None
    source_module: Union[str, None] = None
