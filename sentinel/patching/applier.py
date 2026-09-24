from pathlib import Path


def apply_unified_diff(project: Path, patch: str, allowed_files: set[str]) -> list[str]:
    """Apply a narrow text patch only after checking every target path."""
    touched: list[str] = []
    for line in patch.splitlines():
        if line.startswith("+++ b/"):
            relative = line.removeprefix("+++ b/")
            if relative not in allowed_files or Path(relative).is_absolute() or ".." in Path(relative).parts:
                raise ValueError(f"Patch targets an unauthorized file: {relative}")
            touched.append(relative)
    if not touched:
        raise ValueError("Patch contains no controlled target file")
    raise NotImplementedError("Unified-diff application is intentionally delegated to a vetted patch engine in the next implementation slice")


def apply_replacement(project: Path, relative_file: str, old: str, new: str, allowed_files: set[str]) -> None:
    relative = Path(relative_file)
    if relative_file not in allowed_files or relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Unauthorized patch target: {relative_file}")
    path = (project / relative).resolve()
    if project.resolve() not in path.parents:
        raise ValueError("Patch escaped the target project")
    source = path.read_text(encoding="utf-8")
    if source.count(old) != 1:
        raise ValueError("Patch anchor must occur exactly once")
    path.write_text(source.replace(old, new, 1), encoding="utf-8")
