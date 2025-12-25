# PostgreSQL MCP サーバー

Model Context Protocol (MCP) サーバーで、PostgreSQL データベース操作を提供します。AI アシスタントに標準化された CRUD 操作とデータベース管理機能を提供します。

**ステータス**: ✅ **完了** - 完全に実装、テスト済み、PyPI に公開済み

## 機能

- **CRUD 操作**: エンティティの作成、読み取り、更新、削除
- **動的テーブルサポート**: 事前設定なしで任意のテーブルを操作
- **安全な接続**: 環境変数ベースの設定と検証
- **パラメータ化クエリ**: SQL インジェクション対策
- **テーブル管理**: テーブルの作成、変更、削除
- **スキーマ情報**: 詳細なテーブルスキーマとデータベースメタデータ
- **包括的なテスト**: ユニットテスト、統合テスト、Docker テスト

## 利用可能なツール

### CRUD 操作
- `create_entity`: テーブルに新しい行を挿入
- `read_entity`: 条件付きでテーブルをクエリ
- `update_entity`: 条件に基づいて既存の行を更新
- `delete_entity`: テーブルから行を削除
- `execute_sql_query`: 任意の SQL クエリを実行して結果を返す

### テーブル管理操作
- `create_table`: 指定されたスキーマで新しいテーブルを作成
- `alter_table`: 既存のテーブル構造を変更
- `drop_table`: データベースからテーブルを削除

### スキーマ操作
- `get_tables`: データベース内のすべてのテーブルのリストを取得
- `get_table_schema`: 特定のテーブルの詳細なスキーマ情報を取得
- `get_database_info`: データベースメタデータとバージョン情報を取得

## 利用可能なリソース

### データベースリソース
- `database://tables`: データベース内のすべてのテーブルのリスト
- `database://info`: データベースメタデータとバージョン情報
- `database://connection`: データベース接続パラメータ（ホスト、ポート、データベース、ユーザー名、パスワードなど）
- `database://schema/{table_name}`: 特定のテーブルのスキーマ情報

## インストール手順

### uv パッケージマネージャーのインストール

**uvとは？**
uvは高速なPythonパッケージマネージャーで、Pythonのインストールとバージョン管理も行えます。システムにPythonがインストールされていない場合でも、uvが自動的に必要なPythonバージョンをダウンロードして管理します。

**Windowsの場合**:
```powershell
# PowerShellで実行
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# インストール確認
uv --version
```

**macOS/Linuxの場合**:
```bash
# インストールスクリプトを使用
curl -LsSf https://astral.sh/uv/install.sh | sh

# またはHomebrewを使用（macOS）
brew install uv

# インストール確認
uv --version
```

### Pythonのセットアップ（uvによる自動管理）

uvはPythonのインストールも自動的に行います。以下のいずれかの方法でPython環境を準備できます：

**方法A: uvによる自動Pythonインストール（推奨）**
```bash
# 特定のPythonバージョンをインストール
uv python install 3.10

# または最新のPythonをインストール
uv python install

# インストールされたPythonバージョンを確認
uv python list
```

**方法B: 既存のPython環境を使用する場合**
システムにすでにPython 3.10以上がインストールされている場合は、uvが自動的に検出して使用します：
```bash
# 利用可能なPythonバージョンを確認
uv python list

# 特定のPythonバージョンを選択
uv python pin 3.10
```

### PostgreSQLデータベースのセットアップ

**方法A: ローカルインストール**
- [PostgreSQL公式サイト](https://www.postgresql.org/download/)からインストール
- またはパッケージマネージャーを使用：
  ```bash
  # macOS
  brew install postgresql@16
  
  # Ubuntu/Debian
  sudo apt install postgresql postgresql-contrib
  
  # Windows
  # 公式インストーラーを使用
  ```

**方法B: Dockerを使用（推奨）**
```bash
# PostgreSQLコンテナの実行
docker run --name postgres-mcp -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=mcp-postgres-db -p 5432:5432 -d postgres:16

# コンテナの状態確認
docker ps
```

### 前提条件の確認

すべての前提条件がインストールされたことを確認：

```bash
# uvのバージョン確認
uv --version

# Pythonのバージョン確認（uv経由）
uv python list

# PostgreSQL接続確認（ローカルインストールの場合）
psql -h localhost -U postgres -d mcp-postgres-db

# またはDockerコンテナの場合
docker exec -it postgres-mcp psql -U postgres -d mcp-postgres-db
```

### 方法1: 既存のPostgreSQLデータベースを使用する場合

#### MCPクライアントの設定

**Claude Desktopの設定例**：
```json
{
  "mcpServers": {
    "postgres-mcp": {
      "command": "uvx",
      "args": ["mcp-postgres-duwenji"],
      "env": {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_DB": "your_database",
        "POSTGRES_USER": "your_username",
        "POSTGRES_PASSWORD": "your_password",
        "POSTGRES_SSL_MODE": "prefer",
        "MCP_LOG_LEVEL": "INFO",
        "MCP_PROTOCOL_DEBUG": "true",
        "MCP_LOG_DIR": "C:\\Logs\\mcp-postgres"
      }
    }
  }
}
```

### 方法2: Docker自動セットアップを使用する場合

#### MCPクライアントの設定

**Docker自動セットアップ設定例**：
```json
{
  "mcpServers": {
    "postgres-mcp": {
      "disabled": false,
      "timeout": 60,
      "type": "stdio",
      "command": "uvx",
      "args": ["mcp-postgres-duwenji"],
      "env": {
        "MCP_DOCKER_AUTO_SETUP": "true",
        "MCP_DOCKER_IMAGE": "postgres:16",
        "MCP_DOCKER_CONTAINER_NAME": "mcp-postgres-auto",
        "MCP_DOCKER_PORT": "5432",
        "MCP_DOCKER_DATA_VOLUME": "mcp_postgres_data",
        "MCP_DOCKER_PASSWORD": "postgres",
        "MCP_DOCKER_DATABASE": "mcp-postgres-db",
        "MCP_DOCKER_USERNAME": "postgres",
        "MCP_DOCKER_MAX_WAIT_TIME": "30",
        "MCP_LOG_LEVEL": "INFO",
        "MCP_PROTOCOL_DEBUG": "true",
        "MCP_LOG_DIR": "C:\\Logs\\mcp-postgres"
      }
    }
  }
}
```

この設定により自動的に：
- MCPサーバー起動時にPostgreSQL Dockerコンテナが開始されます
- 指定されたDockerイメージ（postgres:16）が使用されます
- データ保存用の永続的なデータボリュームが作成されます
- 指定された認証情報でデータベースがセットアップされます
- **外部アクセスが有効**になります（すべてのインターフェースでリッスン）
- トラブルシューティング用のデバッグログが有効になります

詳細なDockerセットアップ手順については、[Docker自動セットアップガイド](docs/docker-auto-setup-guide.md)を参照してください。

### 外部プログラムからのアクセス

Docker自動セットアップを使用する場合、PostgreSQLコンテナは外部接続を許可するように設定されています：
- **リッスンアドレス**: `*`（すべてのインターフェース）
- **ポート**: `MCP_DOCKER_PORT`で設定可能（デフォルト: 5432）
- **認証**: パスワードベースの認証

外部のPythonプログラムは、`database://connection`リソースからの接続情報を使用して、PostgreSQLデータベースに直接接続できます。

### 動作確認

設定が完了したら、AIアシスタントを通じてMCPツールを使用できます：

**新しいユーザーの作成**：
```json
{
  "table_name": "users",
  "data": {
    "name": "John Doe",
    "email": "john@example.com",
    "age": 30
  }
}
```

**ユーザーの読み取り**：
```json
{
  "table_name": "users",
  "conditions": {
    "age": 30
  },
  "limit": 10
}
```

### トラブルシューティング

1. **接続エラーが発生する場合**：
   - 環境変数が正しく設定されているか確認してください
   - PostgreSQLサーバーが実行中か確認してください
   - ファイアウォール設定を確認してください

2. **Dockerコンテナが起動しない場合**：
   - Dockerがインストールされ実行中か確認してください
   - ポート5432が他のプロセスで使用されていないか確認してください

3. **詳細なログを確認する場合**：
   ```bash
   MCP_LOG_LEVEL=DEBUG uvx mcp-postgres-duwenji
   ```

### 使用例

設定が完了したら、AI アシスタントを通じて MCP ツールを使用できます：

**新しいユーザーの作成**：
```json
{
  "table_name": "users",
  "data": {
    "name": "John Doe",
    "email": "john@example.com",
    "age": 30
  }
}
```

**条件付きでユーザーを読み取り**：
```json
{
  "table_name": "users",
  "conditions": {
    "age": 30
  },
  "limit": 10
}
```

**ユーザー情報の更新**：
```json
{
  "table_name": "users",
  "conditions": {
    "id": 1
  },
  "updates": {
    "email": "newemail@example.com"
  }
}
```

**ユーザーの削除**：
```json
{
  "table_name": "users",
  "conditions": {
    "id": 1
  }
}
```

**カスタム SQL クエリの実行**：
```json
{
  "query": "SELECT u.name, COUNT(o.id) as order_count FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id, u.name HAVING COUNT(o.id) > 5",
  "limit": 100
}
```

**パラメータ化 SQL クエリの実行**：
```json
{
  "query": "SELECT * FROM users WHERE age > %(min_age)s AND created_at > %(start_date)s",
  "params": {
    "min_age": 18,
    "start_date": "2024-01-01"
  },
  "limit": 50
}
```

## テスト

プロジェクトには包括的なテストスイートが含まれており、単体テストと統合テストの両方をカバーしています。

### テストの実行

#### Windows環境
```bash
# 単体テストのみ実行
test\run_tests.bat unit

# 統合テストのみ実行（PostgreSQLデータベースが必要）
test\run_tests.bat integration

# すべてのテストを実行
test\run_tests.bat all
```

#### Unix/Linux/macOS環境
```bash
# 単体テストのみ実行
uv run python -m pytest test/unit/ -v --tb=short --cov=src --cov-report=term-missing

# 統合テストのみ実行（PostgreSQLデータベースが必要）
RUN_INTEGRATION_TESTS=1 uv run python -m pytest test/integration/ -v --tb=short

# すべてのテストを実行
uv run python -m pytest test/unit/ -v --tb=short --cov=src --cov-report=term-missing
RUN_INTEGRATION_TESTS=1 uv run python -m pytest test/integration/ -v --tb=short
```

### 統合テストの前提条件

統合テストを実行するには、以下の条件を満たすPostgreSQLデータベースが必要です：

1. **データベース接続**:
   - ホスト: `localhost`
   - ポート: `5432`
   - データベース名: `mcp_test_db`
   - ユーザー名: `test_user`
   - パスワード: `test_password`

2. **テストユーザーの権限**:
   ```sql
   -- テストユーザーにSUPERUSER権限を付与
   ALTER USER test_user WITH SUPERUSER;
   ```

3. **テストテーブルの準備**:
   - `users`, `products`, `orders` テーブルが自動的に作成されます
   - テスト実行前にデータベースがクリーンアップされます

### Dockerを使用したテスト環境のセットアップ

既存のDockerコンテナを使用してテスト環境を準備できます：

```bash
# テスト用データベースを作成
docker exec mcp-postgres-auto psql -U postgres -c "CREATE DATABASE mcp_test_db;"

# テストユーザーを作成
docker exec mcp-postgres-auto psql -U postgres -c "CREATE USER test_user WITH PASSWORD 'test_password';"

# テストユーザーに権限を付与
docker exec mcp-postgres-auto psql -U postgres -c "ALTER USER test_user WITH SUPERUSER;"
docker exec mcp-postgres-auto psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE mcp_test_db TO test_user;"
```

### テストカバレッジ

- **単体テスト**: 設定、プロンプト、Docker管理などの個別コンポーネントをテスト
- **統合テスト**: データベース接続、CRUD操作、テーブル管理、トランザクションなどをテスト
- **テストマーカー**: `@pytest.mark.integration` で統合テストをマーク

### テスト構成

- **テスト設定**: `test/conftest.py` で環境変数とフィクスチャを定義
- **テストデータ**: 各テスト実行前にデータベースが自動的にクリーンアップ
- **エラーハンドリング**: 無効な入力やエラー条件をテスト

### トラブルシューティング

1. **統合テストがスキップされる場合**:
   - 環境変数 `RUN_INTEGRATION_TESTS=1` が設定されているか確認
   - PostgreSQLデータベースが実行中か確認
   - テストユーザーの権限を確認

2. **データベース接続エラー**:
   - ポート番号が正しいか確認（デフォルト: 5432）
   - ファイアウォール設定を確認
   - データベースが外部接続を許可しているか確認

3. **権限エラー**:
   - テストユーザーにSUPERUSER権限が必要
   - データベースへの完全なアクセス権限が必要

詳細なテスト情報については、[テストガイド](docs/testing-and-qa.md)を参照してください。

## ライセンス

Apache 2.0
