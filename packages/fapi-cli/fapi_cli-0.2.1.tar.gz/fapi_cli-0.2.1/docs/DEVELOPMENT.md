# 開発者向けドキュメント

## 開発用インストール

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## 開発

```bash
source .venv/bin/activate
pip install -e .[dev]
pytest
```

## 複数バージョンでのテスト

このプロジェクトは複数のFastAPIバージョンでテストされています。

### toxを使用したテスト

```bash
# すべての環境でテストを実行
tox

# 特定のPythonバージョンとFastAPIバージョンの組み合わせでテスト
tox -e py312-fastapilatest
```

### サポートされているFastAPIバージョン

- FastAPI 0.100.0以上、0.115.0未満
- FastAPI 0.115.0以上、0.120.0未満
- FastAPI 0.120.0以上（最新）

CIでは、Python 3.9、3.10、3.11、3.12、3.13、3.14と上記のFastAPIバージョンの組み合わせでテストが実行されます。

## パッケージング

### ローカルでのビルド

```bash
python -m build
twine check dist/*
```

### ローカルからのアップロード（手動）

事前に`~/.pypirc`を設定した上で以下のコマンドを実行してください。

```bash
# TestPyPIへアップロード
twine upload --repository testpypi dist/*

# PyPIへアップロード
twine upload dist/*
```

## リリースフロー

このプロジェクトはGitタグベースでバージョン管理を行い、GitHub Actionsで自動リリースします。

### バージョン管理

- バージョンはGitタグから自動取得されます（hatch-vcs使用）
- タグ形式: `v0.1.0`, `v1.2.3`（セマンティックバージョニング）

### TestPyPIへのリリース（テスト用）

```bash
# プレリリースタグを作成
git tag v0.1.0-rc1
git push origin v0.1.0-rc1
```

または、GitHub Actionsから手動でワークフローを実行できます。

### 本番PyPIへのリリース

```bash
# 正式リリースタグを作成
git tag v0.1.0
git push origin v0.1.0
```

これにより以下が自動実行されます：
1. テスト実行（Python 3.9, 3.14）
2. パッケージビルド
3. PyPIへ公開
4. GitHubリリースノート作成

## PyPI/TestPyPI 初期設定（Trusted Publisher）

GitHub Actionsから安全にパッケージを公開するため、Trusted Publisherを設定します。

### 1. PyPI/TestPyPIアカウント作成

- PyPI: https://pypi.org/account/register/
- TestPyPI: https://test.pypi.org/account/register/

### 2. TestPyPI Trusted Publisher設定

1. https://test.pypi.org/manage/account/publishing/ にアクセス
2. 「Add a new pending publisher」で以下を入力:
   - PyPI Project Name: `fapi-cli`
   - Owner: `WATA-saito`（GitHubユーザー名）
   - Repository name: `fapi-cli`
   - Workflow name: `publish-testpypi.yml`
   - Environment name: `testpypi`

### 3. PyPI Trusted Publisher設定

1. https://pypi.org/manage/account/publishing/ にアクセス
2. 「Add a new pending publisher」で以下を入力:
   - PyPI Project Name: `fapi-cli`
   - Owner: `WATA-saito`（GitHubユーザー名）
   - Repository name: `fapi-cli`
   - Workflow name: `release.yml`
   - Environment name: `pypi`

### 4. GitHub Environments設定

1. リポジトリの Settings → Environments
2. `testpypi` と `pypi` の2つのEnvironmentを作成
3. 必要に応じて保護ルール（承認者など）を設定

### 5. 初回リリーステスト

```bash
# TestPyPIでテスト
git tag v0.1.0-rc1
git push origin v0.1.0-rc1

# TestPyPIからインストールして動作確認
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ fapi-cli
```
