# fapi-cli

FastAPIアプリケーションに対してサーバーを起動せずにHTTPリクエストを送信できるCLIツールです。`fastapi.testclient.TestClient`を活用して、ローカルファイルからFastAPIアプリケーションを読み込み、curlライクなインターフェースでエンドポイントを呼び出します。

## 特長

- `fapi-cli request` コマンドで任意のFastAPIアプリケーションにリクエストを送信
- `-X/--method`, `-P/--path`, `-d/--data`, `-H/--header`, `-q/--query` といったcurl互換のオプション
- `-F/--form` でフォームデータとファイルアップロードに対応（`multipart/form-data`）
- JSONレスポンスを整形して標準出力に表示
- `--include-headers` でレスポンスヘッダーも表示可能

## インストール

### PyPIからインストール

```bash
pip install fapi-cli
```

### pipxでインストール（推奨）

```bash
pipx install fapi-cli
```

### uvxで一時実行

```bash
uvx fapi-cli request main.py -P /
```

> **Note (uvx / TestPyPI)**: TestPyPI では依存解決の都合で未検証の依存バージョンを拾ってしまうことがあります（特にプレリリース配布時）。
> その場合は、明示的に依存を固定して回避してください。例:
>
> ```bash
> uvx fapi-cli request main.py -P / --with "fastapi<1.0"
> uvx fapi-cli request main.py -P / -F "name=Alice" --with "fastapi<1.0" --with "python-multipart<1.0"
> ```

## 要件

- Python 3.9以上
- FastAPI 0.100.0以上
- FastAPIアプリケーション（テスト対象）

## 使い方

```bash
# アプリケーションを定義したファイルからGETリクエスト
fapi-cli request src/main.py

# POSTメソッドでJSONボディを送信
fapi-cli request src/main.py -X POST -P /items -d '{"name": "Alice"}'

# ヘッダーとクエリパラメータを付与
fapi-cli request src/main.py -H "Authorization: Bearer token" -q "page=1"

# アプリケーションの変数名が app 以外の場合
fapi-cli request src/api.py --app-name fastapi_app
```

### フォームデータとファイルアップロード

`-F` オプションでフォームデータやファイルを送信できます（curlの`-F`オプションと同等）。

> **Note**: フォーム機能を使用するには `python-multipart` が必要です。FastAPIアプリケーション側で `Form()` や `File()` を使用している場合はすでにインストールされているはずです。そうでない場合は以下のコマンドでインストールしてください：
>
> ```bash
> pip install 'fapi-cli[form]'
> ```

```bash
# フォームフィールドを送信
fapi-cli request src/main.py -X POST -P /form -F "name=Alice" -F "age=30"

# 同一キーを複数回指定（例: List[str] を受け取る Form）
fapi-cli request src/main.py -X POST -P /tags -F "tag=python" -F "tag=fastapi"

# ファイルをアップロード（@記法）
fapi-cli request src/main.py -X POST -P /upload -F "file=@./image.png"

# Content-Type を指定
fapi-cli request src/main.py -X POST -P /upload -F "document=@./file.pdf;type=application/pdf"

# ファイル名を変更
fapi-cli request src/main.py -X POST -P /upload -F "file=@./temp.txt;filename=report.txt"

# フォームフィールドとファイルを同時に送信
fapi-cli request src/main.py -X POST -P /profile -F "name=Alice" -F "avatar=@./photo.jpg"

# 同一キーで複数ファイルをアップロード（例: List[UploadFile] を受け取る File）
fapi-cli request src/main.py -X POST -P /upload-many -F "files=@./a.txt" -F "files=@./b.txt"
```

> **Note**: `-d`（JSONボディ）と `-F`（フォームデータ）は同時に指定できません。

## ライセンス

MIT License
