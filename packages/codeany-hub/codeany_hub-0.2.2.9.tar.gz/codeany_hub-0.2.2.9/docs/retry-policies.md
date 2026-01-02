# Retry Policies & Transport Hooks

The `Transport` and `AsyncTransport` classes now accept a `RetryPolicy`
implementation, making it easy to tailor resilience strategies per application.

## Built-in exponential backoff

```python
from codeany_hub.core import ExponentialBackoffRetry
from codeany_hub import CodeanyClient

policy = ExponentialBackoffRetry(retries=3, backoff_factor=0.5)

client = CodeanyClient(
    "https://hub.codeany.dev",
    auth=...,  # any AuthStrategy
    retry_policy=policy,
    log_requests=True,
)
```

## Custom policy example

```python
from codeany_hub.core import RetryPolicy


class CircuitBreakerRetry(RetryPolicy):
    def __init__(self) -> None:
        self._max_attempts = 4
        self._total_failures = 0

    @property
    def max_attempts(self) -> int:
        return self._max_attempts

    def get_retry_delay_for_response(self, method, attempt, response):
        if response.status_code >= 500 and attempt < self.max_attempts:
            return min(2.0, 0.3 * attempt)
        return None

    def get_retry_delay_for_error(self, method, attempt, exc):
        return 0.3 if attempt < self.max_attempts else None
```

Supply the policy via `retry_policy=` to any sync or async client constructor.

## Hooking for observability

`TransportHooks` let you attach callable(s) that inspect request and response
metadata without mutating payloads.

```python
from codeany_hub.core import TransportHooks

latencies: list[float] = []

hooks = TransportHooks(
    on_response=[lambda ctx: latencies.append(ctx.duration)],
)

client = CodeanyClient(
    "https://hub.codeany.dev",
    auth=...,  # any AuthStrategy
    hooks=hooks,
)
```

For asynchronous instrumentation, use the `async_hooks` parameter on
`AsyncCodeanyClient` (awaitables are supported).
