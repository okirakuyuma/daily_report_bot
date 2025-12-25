---
name: drb-architecture
description: Daily Report Botの軽量DDDアーキテクチャルール。新規ファイル作成時、コード配置判断時、リファクタリング時に使用。どのレイヤーにコードを配置すべきか判断する際に参照。
---

# DRB Architecture

Daily Report Botの軽量DDDアーキテクチャルール。

## レイヤー構成

```
src/
├── domain/          # エンティティ・値オブジェクト・ビジネスルール
├── services/        # ユースケース・アプリケーションロジック
├── repositories/    # データ永続化（JSONL, ローカルファイル）
├── gateways/        # 外部API連携（Notion, Gemini, Slack）
├── utils/           # 共通ユーティリティ
└── main.py          # エントリポイント
```

## レイヤー責務

| レイヤー | 責務 | 依存先 |
|----------|------|--------|
| `domain/` | ビジネスルール、エンティティ定義 | なし（純粋） |
| `services/` | ユースケース実行、オーケストレーション | domain, repositories, gateways |
| `repositories/` | ローカルデータ永続化 | domain |
| `gateways/` | 外部APIとの通信 | domain |
| `utils/` | 汎用ヘルパー | なし |

## 配置ルール

### domain/
- Pydanticモデル（`CaptureRecord`, `DailyReport`等）
- 値オブジェクト（`TimeBlock`, `AppUsage`等）
- ビジネスルール（バリデーション、計算ロジック）
- **外部依存禁止**

### services/
- ユースケース単位のクラス/関数
- 例: `ReportGenerationService`, `LogAggregationService`
- repositories/gatewaysを組み合わせて処理を実行

### repositories/
- ローカルファイル操作（JSONL読み書き）
- 例: `CaptureRepository`, `ReportRepository`

### gateways/
- 外部API呼び出し
- 例: `NotionGateway`, `GeminiGateway`, `SlackGateway`
- リトライ・エラーハンドリング含む

### utils/
- 日付処理、文字列処理、ロギング
- どのレイヤーからも使用可能

## 命名規則

| 種類 | パターン | 例 |
|------|---------|-----|
| エンティティ | `{Name}` | `CaptureRecord`, `DailyReport` |
| サービス | `{Name}Service` | `ReportGenerationService` |
| リポジトリ | `{Name}Repository` | `CaptureRepository` |
| ゲートウェイ | `{Name}Gateway` | `NotionGateway` |

## 依存方向

```
main.py
  ↓
services/
  ↓
repositories/ + gateways/
  ↓
domain/
```

**上位レイヤーは下位レイヤーに依存。逆は禁止。**
