# フォルダ構成

## 概要

軽量DDD（Domain-Driven Design）を採用したPython統一構成。

| 方針 | 内容 |
|------|------|
| 言語 | Python 3.10+ |
| アーキテクチャ | 軽量DDD（4レイヤー） |
| フェーズ対応 | 段階的に機能追加可能 |

## ディレクトリ構成

```
daily_report_bot/
│
├── docs/                      # ドキュメント
│   ├── architecture/          # アーキテクチャ設計
│   ├── design/                # フロー設計
│   └── phases/                # フェーズ仕様
│
├── src/
│   ├── domain/                # エンティティ・ビジネスルール
│   │   ├── __init__.py
│   │   ├── capture.py         # CaptureRecord
│   │   ├── session.py         # Session (Phase 2)
│   │   ├── features.py        # Features
│   │   └── report.py          # Report
│   │
│   ├── services/              # ユースケース・ビジネスロジック
│   │   ├── __init__.py
│   │   ├── logger.py          # 常駐ロガー
│   │   ├── aggregator.py      # ログ集計
│   │   ├── summarizer.py      # LLM要約 (Phase 3)
│   │   └── exporter.py        # Notion出力
│   │
│   ├── repositories/          # データ永続化
│   │   ├── __init__.py
│   │   ├── log_repository.py  # JSONL読み書き
│   │   └── config_repository.py
│   │
│   ├── gateways/              # 外部API連携
│   │   ├── __init__.py
│   │   ├── window.py          # Win32 API
│   │   ├── screenshot.py      # スクリーンショット
│   │   ├── ocr.py             # OCR
│   │   ├── notion.py          # Notion API
│   │   ├── gemini.py          # Gemini API (Phase 3)
│   │   └── toast.py           # Toast通知
│   │
│   ├── utils/                 # 共通ユーティリティ
│   │   ├── __init__.py
│   │   ├── extractor.py       # 正規表現抽出
│   │   └── time.py            # 時間処理
│   │
│   └── main.py                # エントリーポイント
│
├── scripts/                   # セットアップ・運用
│   ├── install.ps1            # インストーラ
│   ├── register_task.py       # タスクスケジューラ登録
│   └── hotkey.ahk             # ショートカット設定
│
├── data/                      # ランタイムデータ (.gitignore)
│   ├── logs/                  # raw JSONL
│   ├── features/              # 集計済みJSON
│   └── reports/               # レポートJSON
│
├── pyproject.toml
├── .env.example
└── CLAUDE.md
```

## レイヤー説明

### domain/ - ドメイン層

ビジネスエンティティと値オブジェクト。外部依存なし。

| ファイル | 責務 | Phase |
|----------|------|-------|
| `capture.py` | キャプチャレコード定義 | 1 |
| `session.py` | セッション（連続作業）定義 | 2 |
| `features.py` | 集計特徴量定義 | 1 |
| `report.py` | 日報レポート定義 | 1 |

### services/ - サービス層

ユースケースとビジネスロジック。ドメイン層のみに依存。

| ファイル | 責務 | Phase |
|----------|------|-------|
| `logger.py` | 常駐ロガー（2分間隔キャプチャ） | 1 |
| `aggregator.py` | ログ集計・時間ブロック生成 | 1 |
| `summarizer.py` | LLM要約生成 | 3 |
| `exporter.py` | Notion出力制御 | 1 |

### repositories/ - リポジトリ層

データの永続化・読み込み。

| ファイル | 責務 | Phase |
|----------|------|-------|
| `log_repository.py` | JSONL読み書き | 1 |
| `config_repository.py` | 設定ファイル管理 | 1 |

### gateways/ - ゲートウェイ層

外部システム・APIとの連携。

| ファイル | 責務 | 依存ライブラリ | Phase |
|----------|------|---------------|-------|
| `window.py` | ウィンドウ情報取得 | pywin32 | 1 |
| `screenshot.py` | スクリーンショット | Pillow | 1 |
| `ocr.py` | テキスト抽出 | winocr | 1 |
| `notion.py` | Notion API | notion-client | 1 |
| `gemini.py` | Gemini API | google-genai | 3 |
| `toast.py` | Windows通知 | win10toast | 1 |

### utils/ - ユーティリティ

共通処理。

| ファイル | 責務 |
|----------|------|
| `extractor.py` | 正規表現でキーワード/URL/ファイル抽出 |
| `time.py` | タイムスタンプ処理 |

## 依存関係

```
┌─────────────────────────────────────────┐
│              main.py                     │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│              services/                   │
│  logger, aggregator, summarizer, exporter│
└─────────────────────────────────────────┘
          │                   │
          ▼                   ▼
┌──────────────────┐  ┌──────────────────┐
│    domain/       │  │  repositories/   │
│                  │  │  gateways/       │
└──────────────────┘  └──────────────────┘
                              │
                              ▼
                      外部ライブラリ/API
```

**依存ルール**:
- `domain/` → 外部依存なし
- `services/` → `domain/`, `repositories/`, `gateways/`
- `repositories/`, `gateways/` → `domain/`

## フェーズ別ファイル追加

| Phase | 追加ファイル |
|-------|-------------|
| 1 MVP | 基本構成すべて（summarizer.py除く） |
| 2 安定運用 | `domain/session.py` |
| 3 LLM導入 | `services/summarizer.py`, `gateways/gemini.py` |
| 4 高精度化 | `utils/` 拡張 |
| 5 プロダクト化 | `scripts/` 拡張 |

## data/ ディレクトリ

ランタイムで生成されるデータ。`.gitignore` に追加。

```
data/
├── logs/
│   ├── 2025-01-15.jsonl
│   └── 2025-01-16.jsonl
├── features/
│   ├── 2025-01-15.json
│   └── 2025-01-16.json
└── reports/
    ├── 2025-01-15.json
    └── 2025-01-16.json
```

Windows環境では `%LOCALAPPDATA%/DailyReportBot/` も利用可能。
