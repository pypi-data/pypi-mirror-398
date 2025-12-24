"""fapi-cliのエントリーポイント。"""

from .cli import app


def main() -> None:
    """CLIアプリケーションを実行する。"""

    app()


if __name__ == "__main__":  # pragma: no cover
    main()
