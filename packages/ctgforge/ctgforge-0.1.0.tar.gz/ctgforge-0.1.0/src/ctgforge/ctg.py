from collections.abc import Iterator
from typing import Any, Optional

from .client.httpx_client import CTGHttpxClient
from .query.compiler import compile_to_params
from .query.expr import Expr


class CTG:
    def __init__(self, client: Optional[CTGHttpxClient] = None) -> None:
        self.client = client or CTGHttpxClient()

    def close(self) -> None:
        self.client.close()

    def get(self, nct_id: str) -> dict[str, Any]:
        return self.client.get(nct_id)

    def search(
        self,
        query: Optional[Expr] = None,
        *,
        fields: Optional[list[str]] = None,
        page_size: int = 100,
        max_studies: Optional[int] = None,
        **params: Any,
    ) -> Iterator[dict[str, Any]]:
        compiled = compile_to_params(query).params if query is not None else {}

        # user-supplied params override compiled params
        merged = {**compiled, **params}

        return self.client.search(
            None,  # backend should accept raw params; keep query arg for compatibility
            fields=fields,
            page_size=page_size,
            max_studies=max_studies,
            **merged,
        )
