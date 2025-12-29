from dataclasses import dataclass


@dataclass(frozen=True)
class CrawlItem:
    url: str
    depth: int


@dataclass(frozen=True)
class RetryPolicy:
    max_retries: int = 4
    timeout_s: float = 15.0
    backoff_base_s: float = 0.7
    backoff_jitter_s: float = 0.4
    delay_between_requests_s: float = 0.2
