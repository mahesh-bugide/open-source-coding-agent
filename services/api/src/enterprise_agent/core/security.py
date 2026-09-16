from pathlib import Path


def ensure_within_directory(base_dir: Path, target: Path) -> Path:
    base_resolved = base_dir.resolve()
    target_resolved = target.resolve()

    if target_resolved == base_resolved or base_resolved in target_resolved.parents:
        return target_resolved

    raise ValueError(f"Path '{target}' escapes workspace root '{base_dir}'")


def resolve_safe_path(workspace_root: Path, relative_path: str) -> Path:
    candidate = (workspace_root / relative_path).resolve()
    return ensure_within_directory(workspace_root, candidate)


def resolve_workspace_root(workspace_path: str, allowed_root: Path | None) -> Path:
    workspace_root = Path(workspace_path).resolve()
    if not workspace_root.exists() or not workspace_root.is_dir():
        raise ValueError("workspace_path must be an existing directory")

    if allowed_root is None:
        return workspace_root

    ensure_within_directory(allowed_root.resolve(), workspace_root)
    return workspace_root
