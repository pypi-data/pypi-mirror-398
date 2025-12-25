import random
import time
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, Optional

import httpx


class CTGTransportError(RuntimeError):
    """Raised when ClinicalTrials.gov transport layer fails."""


@dataclass(frozen=True)
class RetryConfig:
    max_retries: int = 5
    backoff_base: float = 0.6  # in seconds
    backoff_cap: float = 15.0  # in seconds
    jitter: float = 0.25  # +/- jitter fraction
    retry_statuses: tuple[int, ...] = (429, 500, 502, 503, 504)


class CTGHttpxClient:
    """
    Thin HTTP transport for ClinicalTrials.gov v2.

    Provides:
      - search() returning an iterator of raw study dicts
      - get(nct_id) returning a raw study dict
      - built-in pagination
      - retry/backoff on transient failures / rate limits
    """

    BASE_URL = "https://clinicaltrials.gov/api/v2"
    SEARCH_PATH = "/studies"
    STUDY_PATH = "/studies/{nct_id}"

    def __init__(
        self,
        *,
        timeout: float = 30.0,
        headers: Optional[dict[str, str]] = None,
        retry: Optional[RetryConfig] = None,
        client: Optional[httpx.Client] = None,
        user_agent: str = "ctgforge/0.1 (https://pypi.org/project/ctgforge",
    ) -> None:
        self._retry = retry or RetryConfig()

        default_headers = {
            "Accept": "application/json",
            "User-Agent": user_agent,
        }
        if headers:
            default_headers.update(headers)

        self._client = client or httpx.Client(
            base_url=self.BASE_URL,
            timeout=httpx.Timeout(timeout),
            headers=default_headers,
            follow_redirects=True,
        )
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    # ------ public API ------

    def get(self, nct_id: str) -> dict[str, Any]:
        """Fetch a single study by NCT ID."""
        path = self.STUDY_PATH.format(nctId=nct_id)
        return self._request_json("GET", path)

    def search(
        self,
        query: Optional[str] = None,
        *,
        fields: Optional[list[str]] = None,
        page_size: int = 100,
        max_studies: Optional[int] = None,
        **extra_params: Any,
    ) -> Iterator[dict[str, Any]]:
        """
        Search studies with pagination.

        Args:
            query: compiled query string
            fields: list of fields to return
            page_size: number of studies per page
            max_studies: maximum number of studies to return
            extra_params: additional query parameters
        """
        params: dict[str, Any] = dict(extra_params)
        if query:
            # CTG v2 commonly uses "query.term" for free text/expression.
            params["query.term"] = query
        if fields:
            params["fields"] = ",".join(fields)

        params["pageSize"] = int(page_size)

        yielded = 0
        next_token: Optional[str] = None

        while True:
            if next_token:
                params["pageToken"] = next_token

            payload = self._request_json("GET", self.SEARCH_PATH, params=params)

            studies = payload.get("studies") or payload.get("StudyFieldsResponse", {}).get(
                "StudyFields", []
            )
            for s in studies:
                yield s
                yielded += 1
                if max_studies is not None and yielded >= max_studies:
                    return

            next_token = payload.get("nextPageToken")
            if not next_token:
                return

    # ------ internal helpers ------

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json: Any = None,
    ) -> dict[str, Any]:
        last_exc: Optional[Exception] = None

        # Convert dict-type params to httpx's QueryParams to keep "+" unescaped
        str_params = []
        if params is not None:
            for k, v in params.items():
                str_params.append(f"{k}={v}")
        qp = httpx.QueryParams("&".join(str_params))

        for attempt in range(self._retry.max_retries + 1):
            try:
                resp = self._client.request(
                    method,
                    path,
                    params=qp,
                    json=json,
                )
                if resp.status_code in self._retry.retry_statuses:
                    self._sleep_backoff(attempt, resp)
                    continue

                resp.raise_for_status()
                data = resp.json()
                if not isinstance(data, dict):
                    raise CTGTransportError(f"Expected JSON object, got: {type(data)}")
                return data

            except (httpx.TimeoutException, httpx.NetworkError) as e:
                last_exc = e
                self._sleep_backoff(attempt, None)
                continue
            except httpx.HTTPStatusError as e:
                # Non-retryable HTTP error
                raise CTGTransportError(
                    f"HTTP error: {e.response.status_code} calling {path}: {e.response.text[:300]}"
                ) from e
            except ValueError as e:
                # JSON decoding errors
                raise CTGTransportError(f"Invalid JSON response from {path}") from e

        raise CTGTransportError(f"Exhausted retries calling {path}") from last_exc

    def _sleep_backoff(self, attempt: int, resp: Optional[httpx.Response]) -> None:
        if attempt >= self._retry.max_retries:
            return

        # honor Retry-After header if present
        retry_after = None
        if resp is not None:
            ra = resp.headers.get("Retry-After")
            if ra:
                try:
                    retry_after = float(ra)
                except ValueError:
                    retry_after = None

        if retry_after is not None:
            time.sleep(min(retry_after, self._retry.backoff_cap))
            return

        base = min(self._retry.backoff_cap, self._retry.backoff_base * (2**attempt))
        jitter = base * self._retry.jitter * (2 * random.random() - 1)
        time.sleep(max(0.0, base + jitter))
