from __future__ import annotations
import hashlib
import json
import logging
import os
import random
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import requests

from .context import set_current_session
from .llm import LLMUsage
from .runtime import BudgetExceededError

ToolCall = Callable[..., Any]
logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.agenttrail.dev"


class CompletionBatcher:
    def __init__(
        self,
        flush_callback: Callable[[List[Dict[str, Any]]], None],
        max_batch_size: int,
        flush_interval_s: float,
    ) -> None:
        self._flush_callback = flush_callback
        self._max_batch_size = max_batch_size
        self._flush_interval_s = flush_interval_s
        self._lock = threading.Lock()
        self._queue: List[Dict[str, Any]] = []
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def add(self, payload: Dict[str, Any]) -> None:
        should_flush = False
        with self._lock:
            self._queue.append(payload)
            if len(self._queue) >= self._max_batch_size:
                should_flush = True
        if should_flush:
            self.flush()

    def flush(self) -> None:
        batch: List[Dict[str, Any]] = []
        with self._lock:
            if not self._queue:
                return
            batch = self._queue[:]
            self._queue.clear()
        try:
            self._flush_callback(batch)
        except Exception:
            logger.warning("Completion batch flush failed; re-queueing items.", exc_info=True)
            with self._lock:
                self._queue = batch + self._queue

    def stop(self) -> None:
        self._stop_event.set()
        self._thread.join(timeout=2)
        self.flush()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            self._stop_event.wait(self._flush_interval_s)
            if self._stop_event.is_set():
                break
            self.flush()


@dataclass
class ExecutedStep:
    tool_name: str
    compensation_tool_name: Optional[str]
    args: tuple
    kwargs: dict


@dataclass
class CloudAgentRuntime:
    """
    Commercial runtime that talks to your HTTP ingestion API.

    Env:
      - AGENTTRAIL_URL
      - AGENTTRAIL_API_KEY
      - AGENTTRAIL_PROJECT (optional)
    """

    base_url: str = DEFAULT_BASE_URL
    api_key: str
    project: Optional[str] = None

    request_timeout_s: float = 10.0
    max_retries: int = 3
    backoff_factor: float = 0.5
    max_backoff_s: float = 6.0
    retry_statuses: tuple = (429, 500, 502, 503, 504)
    claim_poll_ms: int = 30000
    claim_poll_interval_ms: int = 250
    pending_timeout_s: int = 300
    claim_lease_seconds: int = 300
    heartbeat_interval_s: int = 60
    batch_completions: bool = True
    batch_max_size: int = 20
    batch_flush_interval_s: float = 1.0

    tools: Dict[str, ToolCall] = field(default_factory=dict)
    compensations: Dict[str, str] = field(default_factory=dict)
    _http: requests.Session = field(default_factory=requests.Session, repr=False)
    _client_id: str = field(default_factory=lambda: str(uuid.uuid4()), repr=False)
    _completion_batcher: Optional[CompletionBatcher] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.batch_completions:
            self._completion_batcher = CompletionBatcher(
                self._flush_completion_batch,
                self.batch_max_size,
                self.batch_flush_interval_s,
            )

    @classmethod
    def from_env(cls) -> "CloudAgentRuntime":
        base_url = os.environ.get("AGENTTRAIL_URL", DEFAULT_BASE_URL)
        api_key = os.environ.get("AGENTTRAIL_API_KEY")
        project = os.environ.get("AGENTTRAIL_PROJECT")

        if not api_key:
            raise RuntimeError("AGENTTRAIL_API_KEY must be set")

        return cls(base_url=base_url.rstrip("/"), api_key=api_key, project=project)

    def _headers(self) -> Dict[str, str]:
        headers = {"X-API-Key": self.api_key}
        if self.project:
            headers["X-Project"] = self.project
        return headers

    def _request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        attempt = 0
        timeout = kwargs.pop("timeout", self.request_timeout_s)
        while True:
            try:
                resp = self._http.request(method, url, timeout=timeout, **kwargs)
            except requests.RequestException as exc:
                if attempt >= self.max_retries:
                    logger.error("HTTP request failed after retries", exc_info=True)
                    raise RuntimeError(f"HTTP request failed: {exc}") from exc
                delay = min(self.max_backoff_s, self.backoff_factor * (2**attempt))
                delay += random.uniform(0, self.backoff_factor)
                attempt += 1
                logger.warning(
                    "HTTP request error; retrying (%s/%s) in %.2fs: %s",
                    attempt,
                    self.max_retries,
                    delay,
                    exc,
                )
                time.sleep(delay)
                continue

            if resp.status_code in self.retry_statuses and attempt < self.max_retries:
                delay = min(self.max_backoff_s, self.backoff_factor * (2**attempt))
                delay += random.uniform(0, self.backoff_factor)
                attempt += 1
                logger.warning(
                    "HTTP %s from %s; retrying (%s/%s) in %.2fs",
                    resp.status_code,
                    url,
                    attempt,
                    self.max_retries,
                    delay,
                )
                time.sleep(delay)
                continue

            return resp

    def _enqueue_completion(self, payload: Dict[str, Any]) -> None:
        if self._completion_batcher:
            self._completion_batcher.add(payload)
        else:
            self._flush_completion_batch([payload])

    def _flush_completion_batch(self, batch: List[Dict[str, Any]]) -> None:
        if not batch:
            return
        url = f"{self.base_url}/v1/tool-calls/complete-batch"
        resp = self._request(
            "POST",
            url,
            headers=self._headers(),
            json={"items": batch},
        )
        if resp.status_code >= 400:
            raise RuntimeError(
                f"Failed to batch complete tool calls: {resp.status_code} {resp.text}"
            )

    def flush_completions(self) -> None:
        if self._completion_batcher:
            self._completion_batcher.flush()

    # ---------- tool registration ----------

    def register_tool(self, name: str, func: ToolCall) -> None:
        self.tools[name] = func

    def register_compensation(self, tool_name: str, compensation_tool_name: str) -> None:
        self.compensations[tool_name] = compensation_tool_name

    def get_tool(self, name: str) -> ToolCall:
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' is not registered.")
        return self.tools[name]

    # ---------- sessions ----------

    def agent_session(
        self,
        name: str,
        input_payload: Any | None = None,
        replay: bool = False,
        replay_run_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        budget_limit: Optional[float] = None,
        compensate_on_budget_exceeded: bool = True,
    ) -> "CloudAgentSession":
        return CloudAgentSession(
            runtime=self,
            name=name,
            input_payload=input_payload,
            replay=replay,
            replay_run_id=replay_run_id,
            tags=tags or [],
            budget_limit=budget_limit,
            compensate_on_budget_exceeded=compensate_on_budget_exceeded,
        )

    def resume_session(
        self,
        name: str,
        run_id: str,
        input_payload: Any | None = None,
        tags: Optional[List[str]] = None,
        budget_limit: Optional[float] = None,
        compensate_on_budget_exceeded: bool = True,
    ) -> "CloudAgentSession":
        return CloudAgentSession(
            runtime=self,
            name=name,
            input_payload=input_payload,
            resume_run_id=run_id,
            tags=tags or [],
            budget_limit=budget_limit,
            compensate_on_budget_exceeded=compensate_on_budget_exceeded,
        )

    def replay_run(
        self,
        name: str,
        run_id: str,
        agent_fn: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        with self.agent_session(
            name=name,
            input_payload={"replay_of": run_id},
            replay=True,
            replay_run_id=run_id,
        ) as session:
            result = agent_fn(*args, **kwargs)
            session.set_output(result)
            return result

    def export_run_to_file(self, run_id: str, path: str) -> None:
        url = f"{self.base_url}/v1/runs/{run_id}/export"
        resp = self._request("GET", url, headers=self._headers())
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to export run: {resp.status_code} {resp.text}")
        with open(path, "w", encoding="utf-8") as file:
            json.dump(resp.json(), file, indent=2)

    def replay_run_from_file(
        self,
        name: str,
        path: str,
        agent_fn: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        with open(path, "r", encoding="utf-8") as file:
            payload = json.load(file)
        tool_calls = payload.get("tool_calls", [])
        run_id = payload.get("run", {}).get("id")
        with CloudAgentSession(
            runtime=self,
            name=name,
            input_payload=payload.get("run", {}).get("input"),
            replay=True,
            replay_run_id=run_id,
            replay_calls=tool_calls,
        ) as session:
            result = agent_fn(*args, **kwargs)
            session.set_output(result)
            return result


@dataclass
class CloudAgentSession:
    runtime: CloudAgentRuntime
    name: str
    input_payload: Any | None
    replay: bool = False
    replay_run_id: Optional[str] = None
    replay_calls: Optional[List[dict]] = None
    resume_run_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    budget_limit: Optional[float] = None
    compensate_on_budget_exceeded: bool = True

    run_id: Optional[str] = None
    status: str = "pending"
    error: Optional[str] = None
    output_payload: Any | None = None

    seq_no: int = 0
    executed_steps: List[ExecutedStep] = field(default_factory=list)
    _replay_calls: List[dict] = field(default_factory=list)
    _replay_index: int = 0
    _seq_lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0

    def __enter__(self) -> "CloudAgentSession":
        if self.replay:
            if not self.replay_run_id:
                self.run_id = f"replay-{uuid.uuid4()}"
            else:
                self.run_id = self.replay_run_id
            if self.replay_calls is not None:
                self._replay_calls = self.replay_calls
            else:
                self._load_replay_calls()
            set_current_session(self)
            return self

        if self.resume_run_id:
            url = f"{self.runtime.base_url}/v1/runs/{self.resume_run_id}/resume"
            resp = self.runtime._request("POST", url, headers=self.runtime._headers())
            if resp.status_code != 200:
                raise RuntimeError(f"Failed to resume run: {resp.status_code} {resp.text}")
            data = resp.json()
            self.run_id = data["run_id"]
            self.seq_no = int(data.get("seq_no", 0))
            self.total_prompt_tokens = int(data.get("total_prompt_tokens", 0))
            self.total_completion_tokens = int(data.get("total_completion_tokens", 0))
            self.total_tokens = int(data.get("total_tokens", 0))
            self.total_cost = float(data.get("total_cost", 0.0))
            if self.budget_limit is None:
                self.budget_limit = data.get("budget_limit")
            set_current_session(self)
            return self

        url = f"{self.runtime.base_url}/v1/runs"
        payload: Dict[str, Any] = {
            "name": self.name,
            "input": self.input_payload,
            "replay_of": None,
            "tags": self.tags,
            "project": self.runtime.project,  # redundancy; header is authoritative
            "budget_limit": self.budget_limit,
        }
        resp = self.runtime._request(
            "POST",
            url,
            headers=self.runtime._headers(),
            json=payload,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to create run: {resp.status_code} {resp.text}")

        data = resp.json()
        self.run_id = data["run_id"]
        set_current_session(self)
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        try:
            if exc_type is None:
                self.status = "success"
            else:
                self.status = "error"
                self.error = str(exc_value) if exc_value else "unknown error"
                if not self.replay:
                    if isinstance(exc_value, BudgetExceededError) and not self.compensate_on_budget_exceeded:
                        pass
                    else:
                        self._run_compensations()

            if not self.replay:
                self._persist_final_status()
                try:
                    self.runtime.flush_completions()
                except Exception:
                    logger.warning("Failed to flush completion batch on session exit.", exc_info=True)
        finally:
            set_current_session(None)

    def set_output(self, value: Any) -> None:
        self.output_payload = value

    def _persist_final_status(self) -> None:
        if not self.run_id:
            return

        url = f"{self.runtime.base_url}/v1/runs/{self.run_id}/complete"
        payload: Dict[str, Any] = {
            "status": self.status,
            "output": self.output_payload,
            "error": self.error,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
        }
        resp = self.runtime._request(
            "POST",
            url,
            headers=self.runtime._headers(),
            json=payload,
        )
        if resp.status_code >= 400:
            raise RuntimeError(
                f"Failed to persist final status: {resp.status_code} {resp.text}"
            )

    def _load_replay_calls(self) -> None:
        if not self.run_id:
            raise RuntimeError("Replay session has no run_id")

        url = f"{self.runtime.base_url}/v1/runs/{self.run_id}"
        resp = self.runtime._request(
            "GET",
            url,
            headers=self.runtime._headers(),
        )
        if resp.status_code != 200:
            raise RuntimeError(
                f"Failed to load replay data: {resp.status_code} {resp.text}"
            )

        data = resp.json()
        calls = data.get("tool_calls", []) or []
        calls.sort(key=lambda c: c.get("seq_no", 0))
        self._replay_calls = calls
        self._replay_index = 0

    def _compute_idempotency_key(
        self, tool_name: str, args: tuple, kwargs: dict, phase: str
    ) -> str:
        payload = {"tool": tool_name, "phase": phase, "args": args, "kwargs": kwargs}
        s = json.dumps(payload, sort_keys=True, default=repr)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()

    def _replay_step(self, tool_name: str, phase: str) -> Any:
        if self._replay_index >= len(self._replay_calls):
            raise RuntimeError("Replay exceeded recorded tool calls")

        record = self._replay_calls[self._replay_index]
        self._replay_index += 1

        if record.get("tool_name") != tool_name or record.get("phase") != phase:
            raise RuntimeError(
                f"Replay mismatch. Expected {tool_name}/{phase}, got {record.get('tool_name')}/{record.get('phase')}"
            )

        if record.get("status") != "success":
            raise RuntimeError(
                f"Replayed tool call ended in status {record.get('status')}"
            )

        return record.get("output")

    def _run_compensations(self) -> None:
        for step in reversed(self.executed_steps):
            comp_name = step.compensation_tool_name
            if not comp_name:
                continue
            comp_func = self.runtime.get_tool(comp_name)
            try:
                self.execute_tool_call(
                    tool_name=comp_name,
                    func=comp_func,
                    args=step.args,
                    kwargs=step.kwargs,
                    phase="compensation",
                    compensation_tool_name=None,
                )
            except Exception:
                continue

    def execute_tool_call(
        self,
        tool_name: str,
        func: ToolCall,
        args: tuple,
        kwargs: dict,
        phase: str = "forward",
        compensation_tool_name: Optional[str] = None,
        usage_parser: Optional[Callable[[Any], LLMUsage]] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Any:
        if not self.run_id:
            raise RuntimeError(
                "CloudAgentSession has no run_id; did you use it as a context manager?"
            )

        if self.replay:
            return self._replay_step(tool_name, phase)

        if phase == "forward" and self._is_budget_exceeded():
            raise BudgetExceededError(
                f"Budget cap exceeded: total_cost={self.total_cost} limit={self.budget_limit}"
            )

        idem_key = self._compute_idempotency_key(tool_name, args, kwargs, phase)

        with self._seq_lock:
            self.seq_no += 1
            claim_seq_no = self.seq_no

        claim_url = f"{self.runtime.base_url}/v1/runs/{self.run_id}/tool-calls/claim"
        claim_payload = {
            "seq_no": claim_seq_no,
            "tool_name": tool_name,
            "phase": phase,
            "idempotency_key": idem_key,
            "input": {"args": args, "kwargs": kwargs},
            "poll_ms": self.runtime.claim_poll_ms,
            "poll_interval_ms": self.runtime.claim_poll_interval_ms,
            "lease_seconds": self.runtime.claim_lease_seconds,
            "client_id": self.runtime._client_id,
        }

        def claim_once() -> Dict[str, Any]:
            resp = self.runtime._request(
                "POST",
                claim_url,
                headers=self.runtime._headers(),
                json=claim_payload,
            )
            if resp.status_code == 200:
                return resp.json()
            raise RuntimeError(f"Claim failed: {resp.status_code} {resp.text}")

        claim = claim_once()

        status = claim.get("status")
        if status == "success":
            return claim.get("output")
        if status == "error":
            raise RuntimeError(f"Prior attempt failed: {claim.get('error')}")

        if status == "pending":
            logger.info("Tool call pending; polling for completion.")
            start = time.time()
            while time.time() - start < self.runtime.pending_timeout_s:
                claim = claim_once()
                status = claim.get("status")
                if status == "success":
                    return claim.get("output")
                if status == "error":
                    raise RuntimeError(f"Prior attempt failed: {claim.get('error')}")
                time.sleep(self.runtime.claim_poll_interval_ms / 1000.0)
            raise RuntimeError("Tool call already pending; timed out waiting for completion")

        if status != "claimed":
            raise RuntimeError(f"Unexpected claim status: {status}")

        call_id = claim["tool_call_id"]

        if phase == "forward" and compensation_tool_name:
            self.executed_steps.append(
                ExecutedStep(
                    tool_name=tool_name,
                    compensation_tool_name=compensation_tool_name,
                    args=args,
                    kwargs=kwargs,
                )
            )

        heartbeat_stop = threading.Event()

        def heartbeat() -> None:
            while not heartbeat_stop.wait(self.runtime.heartbeat_interval_s):
                try:
                    self.runtime._request(
                        "POST",
                        f"{self.runtime.base_url}/v1/tool-calls/{call_id}/heartbeat",
                        headers=self.runtime._headers(),
                        json={"lease_seconds": self.runtime.claim_lease_seconds},
                    )
                    logger.debug("Sent heartbeat for tool call %s", call_id)
                except Exception:
                    logger.warning("Heartbeat failed for tool call %s", call_id, exc_info=True)

        heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
        heartbeat_thread.start()

        try:
            output = func(*args, **kwargs)
            usage = usage_parser(output) if usage_parser else None

            completion_payload = {
                "tool_call_id": call_id,
                "status": "success",
                "output": output,
                "error": None,
                "provider": provider,
                "model": model,
                "prompt_tokens": usage.prompt_tokens if usage else None,
                "completion_tokens": usage.completion_tokens if usage else None,
                "total_tokens": usage.total_tokens if usage else None,
                "input_cost": usage.input_cost if usage else None,
                "output_cost": usage.output_cost if usage else None,
                "total_cost": usage.total_cost if usage else None,
            }
            self.runtime._enqueue_completion(completion_payload)
            if usage:
                self._record_usage_totals(usage)
            return output

        except Exception as e:
            completion_payload = {
                "tool_call_id": call_id,
                "status": "error",
                "output": None,
                "error": str(e),
                "provider": provider,
                "model": model,
            }
            self.runtime._enqueue_completion(completion_payload)
            raise
        finally:
            heartbeat_stop.set()
            heartbeat_thread.join(timeout=2)

    def execute_llm_call(
        self,
        *,
        provider: str,
        model: str,
        tool_name: str,
        call: Callable[[], Any],
        usage_parser: Callable[[Any], LLMUsage],
    ) -> Any:
        return self.execute_tool_call(
            tool_name=tool_name,
            func=lambda: call(),
            args=(),
            kwargs={},
            phase="forward",
            compensation_tool_name=None,
            usage_parser=usage_parser,
            provider=provider,
            model=model,
        )

    def _record_usage_totals(self, usage: LLMUsage) -> None:
        self.total_prompt_tokens += usage.prompt_tokens
        self.total_completion_tokens += usage.completion_tokens
        self.total_tokens += usage.total_tokens
        self.total_cost = round(self.total_cost + usage.total_cost, 6)
        if self._is_budget_exceeded():
            raise BudgetExceededError(
                f"Budget cap exceeded: total_cost={self.total_cost} limit={self.budget_limit}"
            )

    def _is_budget_exceeded(self) -> bool:
        return self.budget_limit is not None and self.total_cost >= float(self.budget_limit)
