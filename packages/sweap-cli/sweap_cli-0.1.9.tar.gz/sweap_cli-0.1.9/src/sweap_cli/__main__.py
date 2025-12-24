"""Allows `python -m sweap_cli` to invoke the CLI."""

from .main import app


def main() -> None:
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
