"""FastAPIアプリケーション向けCLIコマンドの実装。"""

from __future__ import annotations

import importlib.util
import json
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import parse_qsl

import typer
from fastapi import FastAPI
from fastapi.testclient import TestClient


app = typer.Typer(
    help="FastAPIアプリケーションに対してローカルでリクエストを送信します。"
)

DEFAULT_APP_NAMES: Tuple[str, ...] = ("app", "application", "fastapi_app")
VALID_METHODS: Tuple[str, ...] = (
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS",
    "HEAD",
    "TRACE",
)


class CLIError(RuntimeError):
    """CLI実行時の回復可能なエラー。"""


@dataclass
class RequestConfig:
    """リクエスト実行の設定値。"""

    method: str
    path: str
    headers: Dict[str, str]
    query: List[Tuple[str, str]]
    json_body: Optional[Any]
    # `httpx`/`requests` compatible multi-dict style
    # - data: List[Tuple[key, value]]
    # - files: List[Tuple[field_name, file_tuple]]
    #
    # NOTE: 同一キー複数指定（例: -F tag=python -F tag=fastapi）を保持するため dict ではなく list を使う。
    form_data: Optional[List[Tuple[str, str]]]
    files: Optional[List[Tuple[str, Tuple[str, bytes, Optional[str]]]]]
    include_headers: bool


def _normalize_path(path: str) -> str:
    path = path.strip() or "/"
    if not path.startswith("/"):
        path = f"/{path}"
    return path


def _parse_headers(raw_headers: Sequence[str]) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    for header in raw_headers:
        if ":" not in header:
            raise CLIError(
                f"ヘッダーの形式が無効です: '{header}'。'Key: Value' の形式を使用してください。"
            )
        key, value = header.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise CLIError(f"ヘッダー名が空です: '{header}'。")
        headers[key] = value
    return headers


def _parse_query(raw_query: Sequence[str]) -> List[Tuple[str, str]]:
    params: List[Tuple[str, str]] = []
    for query_item in raw_query:
        if not query_item:
            continue
        params.extend(parse_qsl(query_item, keep_blank_values=True))
    return params


def _parse_json(data: Optional[str]) -> Optional[Any]:
    if data is None:
        return None
    try:
        return json.loads(data)
    except json.JSONDecodeError as exc:
        raise CLIError(f"JSONの解析に失敗しました: {exc.msg}") from exc


def _check_multipart_installed() -> None:
    """python-multipart がインストールされているか確認する。"""
    try:
        import python_multipart  # noqa: F401
    except ImportError:
        raise CLIError(
            "-F (--form) オプションを使用するには 'python-multipart' が必要です。\n"
            "以下のコマンドでインストールしてください:\n\n"
            "  pip install 'fapi-cli[form]'\n\n"
            "または:\n\n"
            "  pip install python-multipart"
        )


def _parse_form(
    raw_form: Sequence[str],
) -> Tuple[List[Tuple[str, str]], List[Tuple[str, Tuple[str, bytes, Optional[str]]]]]:
    """フォームデータとファイルを解析する。

    Args:
        raw_form: -F オプションで指定された値のリスト

    Returns:
        (form_data, files) のタプル
        - form_data: フォームフィールドのリスト（同一キー複数指定を保持）
        - files: ファイルアップロード情報のリスト（同一キー複数指定を保持）
          [(field_name, (filename, content, content_type)), ...]
    """
    form_data: List[Tuple[str, str]] = []
    files: List[Tuple[str, Tuple[str, bytes, Optional[str]]]] = []

    for item in raw_form:
        if "=" not in item:
            raise CLIError(
                f"-F オプションの形式が無効です: '{item}'。'key=value' または "
                f"'key=@path' の形式を使用してください。"
            )

        key, value = item.split("=", 1)
        key = key.strip()

        if not key:
            raise CLIError(f"-F オプションのキーが空です: '{item}'。")

        if value.startswith("@"):
            # ファイルアップロード: key=@path または key=@path;type=xxx;filename=yyy
            file_spec = value[1:]  # '@' を除去

            # メタデータの解析: ;type= と ;filename=
            content_type: Optional[str] = None
            custom_filename: Optional[str] = None
            file_path_str = file_spec

            # セミコロンで分割してメタデータを解析
            if ";" in file_spec:
                parts = file_spec.split(";")
                file_path_str = parts[0]
                for part in parts[1:]:
                    part = part.strip()
                    if part.startswith("type="):
                        content_type = part[5:]
                    elif part.startswith("filename="):
                        custom_filename = part[9:]

            # ファイルの存在確認と読み込み
            file_path = Path(file_path_str)
            if not file_path.exists():
                raise CLIError(f"ファイルが見つかりません: {file_path}")

            try:
                file_content = file_path.read_bytes()
            except OSError as exc:
                raise CLIError(
                    f"ファイルの読み込みに失敗しました: {file_path} - {exc}"
                ) from exc

            filename = custom_filename if custom_filename else file_path.name
            files.append((key, (filename, file_content, content_type)))
        else:
            # 通常のフォームフィールド
            form_data.append((key, value))

    return form_data, files


def _validate_method(method: str) -> str:
    normalized = method.upper()
    if normalized not in VALID_METHODS:
        raise CLIError(
            f"HTTPメソッドが不正です: {method}。対応メソッド: {', '.join(VALID_METHODS)}"
        )
    return normalized


def load_application(file_path: str, app_name: Optional[str] = None) -> FastAPI:
    """指定ファイルからFastAPIアプリケーションを読み込む。"""

    path = Path(file_path)
    if not path.exists():
        raise CLIError(f"アプリケーションファイルが見つかりません: {path}")

    module_name = path.stem.replace("-", "_")
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise CLIError(f"モジュールを読み込めませんでした: {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module

    try:
        parent = str(path.parent.resolve())
        if parent not in sys.path:
            sys.path.insert(0, parent)
        spec.loader.exec_module(module)
    except Exception as exc:  # pragma: no cover - ログ用の詳細メッセージ
        trace = "".join(traceback.format_exception(exc))
        raise CLIError(
            f"FastAPIアプリケーションの読み込みに失敗しました: {exc}\n{trace}"
        ) from exc

    candidate_names: Iterable[str]
    if app_name:
        candidate_names = [app_name]
    else:
        candidate_names = DEFAULT_APP_NAMES

    for candidate in candidate_names:
        candidate = candidate.strip()
        if not candidate:
            continue
        app_obj = getattr(module, candidate, None)
        if isinstance(app_obj, FastAPI):
            return app_obj

    raise CLIError(
        "FastAPIアプリケーションが見つかりませんでした。'app' などの変数名を確認してください。"
    )


def _execute_request(fastapi_app: FastAPI, config: RequestConfig) -> Dict[str, Any]:
    client = TestClient(fastapi_app)

    # `-F` 指定時は常に multipart/form-data として送る（curl 互換）
    # httpx は `files=` に list-of-tuples を渡すと multipart になる。
    # かつ、同一キー複数指定を扱えるよう dict ではなく list で渡す。
    files_param: Optional[List[Tuple[str, Any]]] = None
    data_param: Optional[Any] = config.form_data or None

    if config.form_data or config.files:
        files_param = []
        data_param = None

        # フォームフィールド（ファイル名 None）として multipart に含める
        if config.form_data:
            for key, value in config.form_data:
                files_param.append((key, (None, value)))

        # ファイルアップロードを multipart に含める
        if config.files:
            for field, (filename, content, content_type) in config.files:
                if content_type:
                    files_param.append((field, (filename, content, content_type)))
                else:
                    files_param.append((field, (filename, content)))

    response = client.request(
        config.method,
        config.path,
        headers=config.headers,
        params=config.query or None,
        json=config.json_body,
        data=data_param,
        files=files_param,
    )

    try:
        body: Any = response.json()
    except json.JSONDecodeError:
        body = response.text

    result: Dict[str, Any] = {
        "status_code": response.status_code,
        "body": body,
    }

    if config.include_headers:
        result["headers"] = dict(response.headers)

    return result


def _emit_json(data: Dict[str, Any]) -> None:
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2))


def _handle_cli_error(exc: Exception) -> None:
    typer.secho(str(exc), fg=typer.colors.RED, err=True)


@app.command()
def request(
    app_file: str = typer.Argument(
        ...,
        help="FastAPIアプリケーションが定義されたPythonファイルへのパス",
    ),
    path: str = typer.Option("/", "--path", "-P", help="リクエスト送信先のパス"),
    method: str = typer.Option("GET", "--method", "-X", help="HTTPメソッド"),
    data: Optional[str] = typer.Option(
        None, "--data", "-d", help="JSON形式のリクエストボディ"
    ),
    form: List[str] = typer.Option(
        [],
        "--form",
        "-F",
        help=(
            "フォームデータまたはファイル (複数指定可)。"
            "フォーム: 'key=value'、ファイル: 'key=@path'。"
            "ファイルには ';type=mime' や ';filename=name' を追加可能。"
        ),
    ),
    header: List[str] = typer.Option(
        [],
        "--header",
        "-H",
        help="追加するHTTPヘッダー (Key: Value)",
    ),
    query: List[str] = typer.Option(
        [],
        "--query",
        "-q",
        help="クエリパラメータ (key=value&foo=bar の形式)",
    ),
    include_headers: bool = typer.Option(
        False, "--include-headers", help="レスポンスヘッダーを出力に含める"
    ),
    app_name: Optional[str] = typer.Option(
        None,
        "--app-name",
        help="FastAPIアプリケーションの変数名 (デフォルトは app/application/fastapi_app)",
    ),
) -> None:
    """FastAPIアプリケーションに対してHTTPリクエストを送信する。"""

    try:
        # -d と -F の排他制御
        if data is not None and form:
            raise CLIError(
                "-d (--data) と -F (--form) は同時に指定できません。"
                "JSON を送信する場合は -d を、フォームデータやファイルを送信する場合は -F を使用してください。"
            )

        normalized_method = _validate_method(method)
        normalized_path = _normalize_path(path)
        headers = _parse_headers(header)
        query_params = _parse_query(query)
        json_body = _parse_json(data)

        # フォームデータとファイルの解析
        form_data: Optional[List[Tuple[str, str]]] = None
        files: Optional[List[Tuple[str, Tuple[str, bytes, Optional[str]]]]] = None
        if form:
            _check_multipart_installed()
            form_data, files = _parse_form(form)
            # 空の場合は None に
            form_data = form_data or None
            files = files or None

        fastapi_app = load_application(app_file, app_name=app_name)
        config = RequestConfig(
            method=normalized_method,
            path=normalized_path,
            headers=headers,
            query=query_params,
            json_body=json_body,
            form_data=form_data,
            files=files,
            include_headers=include_headers,
        )

        result = _execute_request(fastapi_app, config)
        _emit_json(result)
    except CLIError as exc:
        _handle_cli_error(exc)
        raise typer.Exit(code=1) from exc


@app.callback()
def main() -> None:
    """fapi-cliのメインコマンド。"""

    # サブコマンドを提供するだけなので実装は不要
    return None
