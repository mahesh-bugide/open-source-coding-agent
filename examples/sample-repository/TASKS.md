# Sample Repository Tasks

## Bug-fix tasks (5)

1. Fix authentication timeout default and explicit timeout behavior, then update tests.
2. Fix billing discount/tax ordering bug and update tests.
3. Ensure empty usernames in greeting feature are validated with a clear error.
4. Fix rounding behavior in billing for fractional cent totals.
5. Fix auth token prefix bug for service accounts (`svc-` should map to `service-token-`).

## Feature tasks (3)

1. Add `formal=True` mode to greeting renderer (`Good day, <name>`).
2. Add annual billing helper that applies monthly logic across 12 months.
3. Add auth helper to parse token owner from token string.

## Refactoring tasks (2)

1. Extract shared percentage math helpers for billing calculations.
2. Refactor auth service constants/config into a dataclass config object.
