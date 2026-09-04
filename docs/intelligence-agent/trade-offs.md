# Trade-offs

- Memory is the low-friction default; PostgreSQL provides durable decisions and traces.
- Batch execution is sequential for predictable bounded load.
- Operations aggregate stored traces rather than adding another database.
- Demo identity proves boundaries but is not production IAM.
- Model fallback favors safe deterministic output over invention.
