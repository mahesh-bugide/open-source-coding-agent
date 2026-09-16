# Agent Design

## Tools

Implemented tools with typed input/output + validation + error handling:

- list_files
- search_code
- read_file
- create_file
- edit_file
- delete_file
- run_command
- run_tests
- git_status
- git_diff

Code references:

- Schemas: [services/api/src/enterprise_agent/tools/schemas.py](services/api/src/enterprise_agent/tools/schemas.py)
- Registry: [services/api/src/enterprise_agent/tools/registry.py](services/api/src/enterprise_agent/tools/registry.py)
- File tools: [services/api/src/enterprise_agent/tools/file_tools.py](services/api/src/enterprise_agent/tools/file_tools.py)
- Command tools: [services/api/src/enterprise_agent/tools/command_tools.py](services/api/src/enterprise_agent/tools/command_tools.py)

## State machine

Defined in [services/api/src/enterprise_agent/agent/state.py](services/api/src/enterprise_agent/agent/state.py).

Run loop in [services/api/src/enterprise_agent/agent/orchestrator.py](services/api/src/enterprise_agent/agent/orchestrator.py).

## Repository context

Pipeline:

User request -> search_code + file tree -> relevant files -> symbol extraction -> bounded context.

Implementation in [services/api/src/enterprise_agent/context/repository_context.py](services/api/src/enterprise_agent/context/repository_context.py).

## Apply/Reject flow

- Agent edits sandbox copy
- Produces changed files and diff
- Extension can call apply or reject

Apply/reject endpoints in [services/api/src/enterprise_agent/api/routes.py](services/api/src/enterprise_agent/api/routes.py).
