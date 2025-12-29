from __future__ import annotations

from typing import Any

import httpx

from arp_standard_client.errors import ArpApiError
from arp_standard_model import (
    Health,
    NodeRun,
    NodeRunCompleteRequest,
    NodeRunEvaluationReportRequest,
    NodeRunsCreateRequest,
    NodeRunsCreateResponse,
    Run,
    RunCoordinatorCancelRunRequest,
    RunCoordinatorCompleteNodeRunRequest,
    RunCoordinatorCreateNodeRunsRequest,
    RunCoordinatorGetNodeRunRequest,
    RunCoordinatorGetRunRequest,
    RunCoordinatorHealthRequest,
    RunCoordinatorReportNodeRunEvaluationRequest,
    RunCoordinatorStartRunRequest,
    RunCoordinatorStreamNodeRunEventsRequest,
    RunCoordinatorStreamRunEventsRequest,
    RunCoordinatorVersionRequest,
    RunStartRequest,
    VersionInfo,
)

from .api.health import (
    health,
)

from .api.node_runs import (
    complete_node_run,
    create_node_runs,
    get_node_run,
    report_node_run_evaluation,
    stream_node_run_events,
)

from .api.runs import (
    cancel_run,
    get_run,
    start_run,
    stream_run_events,
)

from .api.version import (
    version,
)

from .client import AuthenticatedClient as _AuthenticatedClient
from .client import Client as _LowLevelClient
from arp_standard_model import ErrorEnvelope as _ErrorEnvelope
from .types import Response as _Response
from .types import Unset as _Unset

def _raise_for_error_envelope(*, envelope: _ErrorEnvelope, status_code: int | None, raw: Any | None) -> None:
    details: Any | None = None
    if not isinstance(envelope.error.details, _Unset):
        details = envelope.error.details
    raise ArpApiError(
        code=str(envelope.error.code),
        message=str(envelope.error.message),
        details=details,
        status_code=status_code,
        raw=raw,
    )

def _unwrap(response: _Response[Any], *, allow_none: bool = False) -> Any:
    parsed = response.parsed
    if parsed is None:
        if allow_none:
            return None
        raise ArpApiError(
            code="unexpected_empty_response",
            message="API returned an empty response",
            status_code=int(response.status_code),
            raw=response.content,
        )
    if isinstance(parsed, _ErrorEnvelope):
        _raise_for_error_envelope(
            envelope=parsed,
            status_code=int(response.status_code),
            raw=parsed.model_dump(exclude_none=True),
        )
    return parsed

class RunCoordinatorClient:
    def __init__(
        self,
        base_url: str | None = None,
        *,
        client: _LowLevelClient | _AuthenticatedClient | None = None,
        bearer_token: str | None = None,
        timeout: httpx.Timeout | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        verify_ssl: Any = True,
        follow_redirects: bool = False,
        raise_on_unexpected_status: bool = False,
        httpx_args: dict[str, Any] | None = None,
    ) -> None:
        if client is None:
            if base_url is None:
                raise ValueError("base_url is required when client is not provided")
            headers_dict = {} if headers is None else dict(headers)
            cookies_dict = {} if cookies is None else dict(cookies)
            httpx_args_dict = {} if httpx_args is None else dict(httpx_args)
            if bearer_token is None:
                client = _LowLevelClient(
                    base_url=base_url,
                    timeout=timeout,
                    headers=headers_dict,
                    cookies=cookies_dict,
                    verify_ssl=verify_ssl,
                    follow_redirects=follow_redirects,
                    raise_on_unexpected_status=raise_on_unexpected_status,
                    httpx_args=httpx_args_dict,
                )
            else:
                client = _AuthenticatedClient(
                    base_url=base_url,
                    token=bearer_token,
                    timeout=timeout,
                    headers=headers_dict,
                    cookies=cookies_dict,
                    verify_ssl=verify_ssl,
                    follow_redirects=follow_redirects,
                    raise_on_unexpected_status=raise_on_unexpected_status,
                    httpx_args=httpx_args_dict,
                )
        self._client = client

    @property
    def raw_client(self) -> _LowLevelClient | _AuthenticatedClient:
        return self._client

    def cancel_run(self, request: RunCoordinatorCancelRunRequest) -> Run:
        params = request.params
        resp = cancel_run.sync_detailed(client=self._client, run_id=params.run_id)
        return _unwrap(resp)

    def complete_node_run(self, request: RunCoordinatorCompleteNodeRunRequest) -> None:
        params = request.params
        resp = complete_node_run.sync_detailed(client=self._client, node_run_id=params.node_run_id, body=request.body)
        _unwrap(resp, allow_none=True)
        return None

    def create_node_runs(self, request: RunCoordinatorCreateNodeRunsRequest) -> NodeRunsCreateResponse:
        resp = create_node_runs.sync_detailed(client=self._client, body=request.body)
        return _unwrap(resp)

    def get_node_run(self, request: RunCoordinatorGetNodeRunRequest) -> NodeRun:
        params = request.params
        resp = get_node_run.sync_detailed(client=self._client, node_run_id=params.node_run_id)
        return _unwrap(resp)

    def get_run(self, request: RunCoordinatorGetRunRequest) -> Run:
        params = request.params
        resp = get_run.sync_detailed(client=self._client, run_id=params.run_id)
        return _unwrap(resp)

    def health(self, request: RunCoordinatorHealthRequest) -> Health:
        _ = request
        resp = health.sync_detailed(client=self._client)
        return _unwrap(resp)

    def report_node_run_evaluation(self, request: RunCoordinatorReportNodeRunEvaluationRequest) -> None:
        params = request.params
        resp = report_node_run_evaluation.sync_detailed(client=self._client, node_run_id=params.node_run_id, body=request.body)
        _unwrap(resp, allow_none=True)
        return None

    def start_run(self, request: RunCoordinatorStartRunRequest) -> Run:
        resp = start_run.sync_detailed(client=self._client, body=request.body)
        return _unwrap(resp)

    def stream_node_run_events(self, request: RunCoordinatorStreamNodeRunEventsRequest) -> str:
        params = request.params
        resp = stream_node_run_events.sync_detailed(client=self._client, node_run_id=params.node_run_id)
        return _unwrap(resp)

    def stream_run_events(self, request: RunCoordinatorStreamRunEventsRequest) -> str:
        params = request.params
        resp = stream_run_events.sync_detailed(client=self._client, run_id=params.run_id)
        return _unwrap(resp)

    def version(self, request: RunCoordinatorVersionRequest) -> VersionInfo:
        _ = request
        resp = version.sync_detailed(client=self._client)
        return _unwrap(resp)

__all__ = [
    'RunCoordinatorClient',
]
