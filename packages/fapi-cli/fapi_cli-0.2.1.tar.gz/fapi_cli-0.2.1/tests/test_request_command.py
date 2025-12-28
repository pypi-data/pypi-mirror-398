from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent
from typing import List

import pytest
from typer.testing import CliRunner, Result

from fapi_cli.cli import app


runner = CliRunner()


def _write_app(tmp_path: Path, content: str, filename: str = "main.py") -> Path:
    app_path = tmp_path / filename
    app_path.write_text(dedent(content), encoding="utf-8")
    return app_path


def _invoke(args: List[str]) -> Result:
    return runner.invoke(app, args)


def _basic_app() -> str:
    return """
    from fastapi import FastAPI

    app = FastAPI()

    @app.get("/")
    def read_root():
        return {"message": "hello"}

    @app.post("/items")
    def create_item(payload: dict):
        return {"received": payload}

    @app.get("/headers")
    def read_headers():
        return {"ok": True}
    """


def test_basic_get_request(tmp_path: Path) -> None:
    app_path = _write_app(tmp_path, _basic_app())
    result = _invoke(["request", str(app_path)])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["status_code"] == 200
    assert payload["body"] == {"message": "hello"}


def test_get_with_custom_path_and_query(tmp_path: Path) -> None:
    app_path = _write_app(
        tmp_path,
        """
        from fastapi import FastAPI

        app = FastAPI()

        @app.get("/search")
        def search(q: str, limit: int = 10):
            return {"q": q, "limit": limit}
        """,
    )

    result = _invoke(
        [
            "request",
            str(app_path),
            "-P",
            "/search",
            "-q",
            "q=test",
            "-q",
            "limit=5",
        ]
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["status_code"] == 200
    assert payload["body"] == {"q": "test", "limit": 5}


def test_post_with_json_body(tmp_path: Path) -> None:
    app_path = _write_app(tmp_path, _basic_app())
    result = _invoke(
        [
            "request",
            str(app_path),
            "-X",
            "POST",
            "-P",
            "/items",
            "-d",
            '{"name": "Alice"}',
        ]
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["status_code"] == 200
    assert payload["body"] == {"received": {"name": "Alice"}}


def test_include_headers(tmp_path: Path) -> None:
    app_path = _write_app(tmp_path, _basic_app())
    result = _invoke(
        [
            "request",
            str(app_path),
            "-P",
            "/headers",
            "--include-headers",
        ]
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["status_code"] == 200
    assert "headers" in payload
    assert isinstance(payload["headers"], dict)


def test_custom_app_name(tmp_path: Path) -> None:
    app_path = _write_app(
        tmp_path,
        """
        from fastapi import FastAPI

        fastapi_app = FastAPI()

        @fastapi_app.get("/")
        def read_root():
            return {"custom": True}
        """,
    )

    result = _invoke(["request", str(app_path), "--app-name", "fastapi_app"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["status_code"] == 200
    assert payload["body"] == {"custom": True}


def test_invalid_json_body(tmp_path: Path) -> None:
    app_path = _write_app(tmp_path, _basic_app())
    result = _invoke(["request", str(app_path), "-d", "{invalid"])

    assert result.exit_code == 1
    assert "JSON" in result.output


def test_invalid_method(tmp_path: Path) -> None:
    app_path = _write_app(tmp_path, _basic_app())
    result = _invoke(["request", str(app_path), "-X", "INVALID"])

    assert result.exit_code == 1
    assert "HTTPメソッド" in result.output


def test_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.py"
    result = _invoke(["request", str(missing)])

    assert result.exit_code == 1
    assert "見つかりません" in result.output


def test_invalid_app(tmp_path: Path) -> None:
    app_path = _write_app(
        tmp_path,
        """
        from fastapi import FastAPI

        not_app = object()
        """,
    )

    result = _invoke(["request", str(app_path)])

    assert result.exit_code == 1
    assert "アプリケーション" in result.output


@pytest.mark.parametrize("header_option", [["Authorization: Bearer token"]])
def test_headers(tmp_path: Path, header_option: List[str]) -> None:
    app_path = _write_app(
        tmp_path,
        """
        from fastapi import FastAPI
        from fastapi import Header

        app = FastAPI()

        @app.get("/protected")
        def protected(authorization: str = Header(...)):
            return {"authorization": authorization}
        """,
    )

    result = _invoke(
        ["request", str(app_path), "-P", "/protected", "-H", header_option[0]]
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["status_code"] == 200
    assert payload["body"] == {"authorization": "Bearer token"}


# ============================================================================
# Form and File Upload Tests
# ============================================================================


def _form_app() -> str:
    return """
    from fastapi import FastAPI, Form, File, UploadFile
    from typing import List, Optional

    app = FastAPI()

    @app.post("/form")
    def submit_form(name: str = Form(...), age: int = Form(...)):
        return {"name": name, "age": age}

    @app.post("/upload")
    def upload_file(file: UploadFile = File(...)):
        content = file.file.read()
        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(content),
        }

    @app.post("/mixed")
    def mixed_form(
        name: str = Form(...),
        avatar: UploadFile = File(...),
    ):
        content = avatar.file.read()
        return {
            "name": name,
            "filename": avatar.filename,
            "size": len(content),
        }

    @app.post("/multi-file")
    def multi_file(
        file1: UploadFile = File(...),
        file2: UploadFile = File(...),
    ):
        return {
            "file1": file1.filename,
            "file2": file2.filename,
        }

    @app.post("/tags")
    def tags(tag: List[str] = Form(...)):
        return {"tag": tag}

    @app.post("/upload-many")
    def upload_many(files: List[UploadFile] = File(...)):
        return {"filenames": [f.filename for f in files]}
    """


def test_form_field_submission(tmp_path: Path) -> None:
    """フォームフィールド送信のテスト"""
    app_path = _write_app(tmp_path, _form_app())
    result = _invoke(
        [
            "request",
            str(app_path),
            "-X",
            "POST",
            "-P",
            "/form",
            "-F",
            "name=Alice",
            "-F",
            "age=30",
        ]
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["status_code"] == 200
    assert payload["body"] == {"name": "Alice", "age": 30}


def test_file_upload(tmp_path: Path) -> None:
    """ファイルアップロードのテスト"""
    app_path = _write_app(tmp_path, _form_app())

    # テスト用ファイルを作成
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")

    result = _invoke(
        [
            "request",
            str(app_path),
            "-X",
            "POST",
            "-P",
            "/upload",
            "-F",
            f"file=@{test_file}",
        ]
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["status_code"] == 200
    assert payload["body"]["filename"] == "test.txt"
    assert payload["body"]["size"] == 13  # len("Hello, World!")


def test_mixed_form_and_file(tmp_path: Path) -> None:
    """フォームフィールドとファイルの混合送信テスト"""
    app_path = _write_app(tmp_path, _form_app())

    # テスト用画像ファイルを作成（バイナリ）
    avatar_file = tmp_path / "avatar.png"
    avatar_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

    result = _invoke(
        [
            "request",
            str(app_path),
            "-X",
            "POST",
            "-P",
            "/mixed",
            "-F",
            "name=Bob",
            "-F",
            f"avatar=@{avatar_file}",
        ]
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["status_code"] == 200
    assert payload["body"]["name"] == "Bob"
    assert payload["body"]["filename"] == "avatar.png"
    assert payload["body"]["size"] == 108


def test_file_with_content_type(tmp_path: Path) -> None:
    """Content-Type指定付きファイルアップロードのテスト"""
    app_path = _write_app(tmp_path, _form_app())

    test_file = tmp_path / "data.bin"
    test_file.write_bytes(b"binary data")

    result = _invoke(
        [
            "request",
            str(app_path),
            "-X",
            "POST",
            "-P",
            "/upload",
            "-F",
            f"file=@{test_file};type=application/octet-stream",
        ]
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["status_code"] == 200
    assert payload["body"]["content_type"] == "application/octet-stream"


def test_file_with_custom_filename(tmp_path: Path) -> None:
    """カスタムファイル名指定のテスト"""
    app_path = _write_app(tmp_path, _form_app())

    test_file = tmp_path / "original.txt"
    test_file.write_text("content")

    result = _invoke(
        [
            "request",
            str(app_path),
            "-X",
            "POST",
            "-P",
            "/upload",
            "-F",
            f"file=@{test_file};filename=custom.txt",
        ]
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["status_code"] == 200
    assert payload["body"]["filename"] == "custom.txt"


def test_file_with_type_and_filename(tmp_path: Path) -> None:
    """Content-Typeとファイル名の両方を指定するテスト"""
    app_path = _write_app(tmp_path, _form_app())

    test_file = tmp_path / "image.dat"
    test_file.write_bytes(b"\x89PNG\r\n\x1a\n")

    result = _invoke(
        [
            "request",
            str(app_path),
            "-X",
            "POST",
            "-P",
            "/upload",
            "-F",
            f"file=@{test_file};type=image/png;filename=photo.png",
        ]
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["status_code"] == 200
    assert payload["body"]["filename"] == "photo.png"
    assert payload["body"]["content_type"] == "image/png"


def test_multiple_file_upload(tmp_path: Path) -> None:
    """複数ファイルアップロードのテスト"""
    app_path = _write_app(tmp_path, _form_app())

    file1 = tmp_path / "file1.txt"
    file1.write_text("content1")
    file2 = tmp_path / "file2.txt"
    file2.write_text("content2")

    result = _invoke(
        [
            "request",
            str(app_path),
            "-X",
            "POST",
            "-P",
            "/multi-file",
            "-F",
            f"file1=@{file1}",
            "-F",
            f"file2=@{file2}",
        ]
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["status_code"] == 200
    assert payload["body"]["file1"] == "file1.txt"
    assert payload["body"]["file2"] == "file2.txt"


def test_multiple_form_fields_same_key(tmp_path: Path) -> None:
    """同一キー複数指定（フォーム）のテスト: -F tag=python -F tag=fastapi"""
    app_path = _write_app(tmp_path, _form_app())

    result = _invoke(
        [
            "request",
            str(app_path),
            "-X",
            "POST",
            "-P",
            "/tags",
            "-F",
            "tag=python",
            "-F",
            "tag=fastapi",
        ]
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["status_code"] == 200
    assert payload["body"] == {"tag": ["python", "fastapi"]}


def test_multiple_file_uploads_same_key(tmp_path: Path) -> None:
    """同一キー複数指定（ファイル）のテスト: -F files=@a -F files=@b"""
    app_path = _write_app(tmp_path, _form_app())

    file1 = tmp_path / "a.txt"
    file1.write_text("a")
    file2 = tmp_path / "b.txt"
    file2.write_text("b")

    result = _invoke(
        [
            "request",
            str(app_path),
            "-X",
            "POST",
            "-P",
            "/upload-many",
            "-F",
            f"files=@{file1}",
            "-F",
            f"files=@{file2}",
        ]
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["status_code"] == 200
    assert payload["body"] == {"filenames": ["a.txt", "b.txt"]}


# ============================================================================
# Form/File Error Cases
# ============================================================================


def test_form_file_not_found(tmp_path: Path) -> None:
    """存在しないファイルを指定した場合のエラーテスト"""
    app_path = _write_app(tmp_path, _form_app())

    result = _invoke(
        [
            "request",
            str(app_path),
            "-X",
            "POST",
            "-P",
            "/upload",
            "-F",
            "file=@/nonexistent/file.txt",
        ]
    )

    assert result.exit_code == 1
    assert "見つかりません" in result.output


def test_form_invalid_format(tmp_path: Path) -> None:
    """-F オプションの形式が不正な場合のエラーテスト"""
    app_path = _write_app(tmp_path, _form_app())

    result = _invoke(
        [
            "request",
            str(app_path),
            "-X",
            "POST",
            "-P",
            "/form",
            "-F",
            "invalid_format_without_equals",
        ]
    )

    assert result.exit_code == 1
    assert "-F オプションの形式が無効です" in result.output


def test_form_empty_key(tmp_path: Path) -> None:
    """-F オプションのキーが空の場合のエラーテスト"""
    app_path = _write_app(tmp_path, _form_app())

    result = _invoke(
        [
            "request",
            str(app_path),
            "-X",
            "POST",
            "-P",
            "/form",
            "-F",
            "=value",
        ]
    )

    assert result.exit_code == 1
    assert "キーが空です" in result.output


def test_data_and_form_exclusive(tmp_path: Path) -> None:
    """-d と -F の同時指定エラーテスト"""
    app_path = _write_app(tmp_path, _form_app())

    result = _invoke(
        [
            "request",
            str(app_path),
            "-X",
            "POST",
            "-P",
            "/form",
            "-d",
            '{"name": "Alice"}',
            "-F",
            "name=Bob",
        ]
    )

    assert result.exit_code == 1
    assert "同時に指定できません" in result.output


def test_form_without_multipart_installed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """python-multipart がインストールされていない場合のエラーテスト"""
    import builtins

    app_path = _write_app(tmp_path, _form_app())

    # python_multipart のインポートを失敗させる
    original_import = builtins.__import__

    def mock_import(name: str, *args, **kwargs):  # type: ignore[no-untyped-def]
        if name == "python_multipart":
            raise ImportError("No module named 'python_multipart'")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)

    result = _invoke(
        [
            "request",
            str(app_path),
            "-X",
            "POST",
            "-P",
            "/form",
            "-F",
            "name=Alice",
        ]
    )

    assert result.exit_code == 1
    assert "python-multipart" in result.output
    assert "fapi-cli[form]" in result.output
