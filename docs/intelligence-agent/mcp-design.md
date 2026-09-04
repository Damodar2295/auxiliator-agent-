# MCP design

One official Python MCP v2 server exposes `list_skills`, `get_skill`, `get_skill_schema` and `execute_skill`. In-memory and Streamable HTTP clients use the same server. External access requires a bearer token; lifecycle and policy remain outside MCP.
