# Reliability

Enterprise calls use replaceable ports. Bounded retry and timeout handling is paired with circuit breakers. Write-like execution supports idempotency: the same key and request replays its result, while conflicting reuse returns HTTP 409. Failures never expose provider payloads.
