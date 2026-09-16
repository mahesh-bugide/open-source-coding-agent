# NEXT STEPS

## MVP COMPLETE

Objective:
Deliver a working self-hosted coding agent MVP with VS Code integration, typed tools, iterative testing loop, and AWS deploy scaffold.

Files likely to change:
- [services/api](services/api)
- [vscode-extension](vscode-extension)
- [scripts/aws](scripts/aws)

Architecture impact:
Baseline architecture is established and modularized.

Implementation approach:
Stabilize current components, increase test coverage, and harden runtime boundaries.

Acceptance criteria:
- End-to-end sample task run succeeds with review/apply/reject flow.

## NEXT 1: Autocomplete

Objective:
Add low-latency inline code completion API and editor integration.

Files likely to change:
- [services/api/src/enterprise_agent/api/routes.py](services/api/src/enterprise_agent/api/routes.py)
- [services/api/src/enterprise_agent/model/client.py](services/api/src/enterprise_agent/model/client.py)
- [vscode-extension/src/extension.ts](vscode-extension/src/extension.ts)

Architecture impact:
Adds a parallel inference path optimized for latency instead of multi-step orchestration.

Implementation approach:
Create `/v1/completions` endpoint, add debounce and context window builder for active file region.

Acceptance criteria:
- Completion returns in <700ms p50 in mock and <1.5s p50 on vLLM.

## NEXT 2: Vector/semantic repository search

Objective:
Improve retrieval quality with embeddings and semantic ranking.

Files likely to change:
- [services/api/src/enterprise_agent/context/repository_context.py](services/api/src/enterprise_agent/context/repository_context.py)
- [services/api/src/enterprise_agent/context](services/api/src/enterprise_agent/context)

Architecture impact:
Introduces retrieval index lifecycle and embedding model dependency.

Implementation approach:
Add retrieval interface and hybrid search combining ripgrep and embedding similarity.

Acceptance criteria:
- Context precision improves on benchmark tasks versus keyword-only baseline.

## NEXT 3: Model router

Objective:
Route requests to different models by task type, latency budget, and cost.

Files likely to change:
- [services/api/src/enterprise_agent/model/client.py](services/api/src/enterprise_agent/model/client.py)
- [services/api/src/enterprise_agent/core/config.py](services/api/src/enterprise_agent/core/config.py)

Architecture impact:
Adds policy layer between orchestrator and model providers.

Implementation approach:
Introduce router policy engine and model capability metadata.

Acceptance criteria:
- Router selects model deterministically with audit logs and fallback policy.

## NEXT 4: Qwen3-Coder-Next evaluation

Objective:
Evaluate next model variant for quality and latency tradeoffs.

Files likely to change:
- [evaluation/tasks.json](evaluation/tasks.json)
- [evaluation/evaluate.py](evaluation/evaluate.py)
- [inference/config/vllm.env](inference/config/vllm.env)

Architecture impact:
No major architecture changes; expands model matrix.

Implementation approach:
Add comparative benchmark harness and report generation.

Acceptance criteria:
- Side-by-side quality and runtime report across task set.

## NEXT 5: SSO/OIDC

Objective:
Replace dev API key with enterprise identity and access control.

Files likely to change:
- [services/api/src/enterprise_agent/core/auth.py](services/api/src/enterprise_agent/core/auth.py)

Architecture impact:
Adds identity provider trust and token validation path.

Implementation approach:
Implement OIDC middleware and user mapping to internal roles.

Acceptance criteria:
- Valid OIDC tokens required; per-user run attribution preserved.

## NEXT 6: GitHub integration

Objective:
Support pull request creation, branch management, and checks.

Files likely to change:
- [services/api/src/enterprise_agent/tools](services/api/src/enterprise_agent/tools)
- [vscode-extension/src/extension.ts](vscode-extension/src/extension.ts)

Architecture impact:
Adds external SCM integration and permission boundaries.

Implementation approach:
Add git hosting tool adapters and approval workflow in extension.

Acceptance criteria:
- Agent can propose branch + PR from reviewed patch.

## NEXT 7: Jira integration

Objective:
Link tasks to tickets and update ticket status from runs.

Files likely to change:
- [services/api/src/enterprise_agent/api](services/api/src/enterprise_agent/api)
- [services/api/src/enterprise_agent/tools](services/api/src/enterprise_agent/tools)

Architecture impact:
Adds issue-tracker integration and metadata mapping.

Implementation approach:
Add Jira client adapter and optional run-to-ticket linkage.

Acceptance criteria:
- Agent run can read ticket context and post completion summary.

## NEXT 8: Production sandbox isolation

Objective:
Harden sandbox boundaries for adversarial repository content.

Files likely to change:
- [services/api/src/enterprise_agent/sandbox/manager.py](services/api/src/enterprise_agent/sandbox/manager.py)
- [sandbox.Dockerfile](sandbox.Dockerfile)

Architecture impact:
Strengthens execution isolation and may alter command runtime semantics.

Implementation approach:
Adopt rootless isolated runtime with seccomp/AppArmor/network egress policy.

Acceptance criteria:
- Untrusted code cannot escape sandbox in security test suite.

## NEXT 9: GPU autoscaling

Objective:
Scale inference capacity by load and queue depth.

Files likely to change:
- one instance's `docker-compose.gpu.yml` scaling config or a future autoscaling group definition
- [inference](inference)

Architecture impact:
Introduces dynamic capacity control and warm-pool policy.

Implementation approach:
Add ASG policies, model warm-up hooks, and request queue metrics.

Acceptance criteria:
- Sustained throughput increases without SLO regression.

## NEXT 10: Enterprise admin dashboard

Objective:
Provide operational visibility and governance controls.

Files likely to change:
- [services/api/src/enterprise_agent/api](services/api/src/enterprise_agent/api)
- new admin UI module

Architecture impact:
Adds read-heavy reporting APIs and policy management layer.

Implementation approach:
Expose run analytics endpoints and build minimal admin frontend.

Acceptance criteria:
- Admin can inspect usage, success rates, and policy settings.
