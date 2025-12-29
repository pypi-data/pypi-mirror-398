from __future__ import annotations

from .cli import app


def main() -> int:
    """Entrypoint for ``python -m dataform_view_migrator`` delegating to Typer app."""
    return app()  # Delegate to Typer app


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
