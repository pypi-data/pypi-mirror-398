import re
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Template

_CANONICAL_RE = re.compile(r"[^a-zA-Z0-9]+")


def to_canonical(name: str) -> str:
    """Convert a human-friendly name to a canonical form (e.g., for
    pyproject.toml).

    """
    return _CANONICAL_RE.sub("-", name).strip("-").lower()


def copy_templates(
    template_dir: Path, target_dir: Path, context: dict, force: bool = False
) -> list[str]:
    """Copy a directory of Jinja2 templates into a new project structure.

    Renders both file contents and any directory or file names containing
    Jinja2 placeholders (e.g. {{project_name}}). Files ending with .j2 are
    rendered with Jinja2 and written without the .j2 suffix. All other files
    are copied as-is.

    """
    template_files = [
        path
        for path in template_dir.rglob("*")
        if "__pycache__" not in path.parts and not path.is_dir()
    ]

    if not force:
        for src_path in template_files:
            dst_path, rel_path = path_parts(src_path, target_dir, template_dir, context)
            if dst_path.exists():
                raise FileExistsError(f"'{dst_path}' already exists in {target_dir}.")

    env = Environment(loader=FileSystemLoader(str(template_dir)))
    paths = []

    for src_path in template_files:
        dst_path, rel_path = path_parts(src_path, target_dir, template_dir, context)

        if not force and dst_path.exists():
            raise FileExistsError(f"File already exists: {dst_path}")

        if src_path.suffix == ".j2":
            template = env.get_template(str(rel_path))
            dst_path.write_text(template.render(**context))
        else:
            shutil.copy2(src_path, dst_path)

        paths.append(dst_path)

    return paths


def path_parts(src_path, target_dir, template_dir, context):
    rel_path = src_path.relative_to(template_dir)

    # Interpolate placeholders in directory and file names using jinja2 as
    # well.
    rendered_parts = [Template(part).render(**context) for part in rel_path.parts]
    dst_rel = Path(*rendered_parts)

    dst_name = dst_rel.stem if src_path.suffix == ".j2" else dst_rel.name
    dst_path = target_dir / dst_rel.parent / dst_name
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    return dst_path, rel_path
