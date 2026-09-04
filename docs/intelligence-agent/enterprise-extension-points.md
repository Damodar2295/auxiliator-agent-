# Enterprise extension points

Protocols in `agent/intelligence/interfaces.py` isolate authorization, identity, model, MCP, audit, secrets, Knowledge Fabric and Salesforce. Replace adapters through bootstrap wiring without changing runtime contracts. Production adapters must enforce least privilege, approved secrets, retries, timeouts, circuit breaking, idempotency and redacted logs.
