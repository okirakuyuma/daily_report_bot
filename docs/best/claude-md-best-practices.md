# auto-movie-editor CLAUDE.md ベストプラクティス

## このリポジトリでのClaude Code設定ガイド

---

## 目次

1. [リポジトリ構成](#1-リポジトリ構成)
2. [CLAUDE.md階層構造](#2-claudemd階層構造)
3. [スキルとエージェント](#3-スキルとエージェント)
4. [トークン最適化](#4-トークン最適化)
5. [効果的な記述方法](#5-効果的な記述方法)
6. [避けるべきアンチパターン](#6-避けるべきアンチパターン)
7. [運用ガイドライン](#7-運用ガイドライン)

---

## 1. リポジトリ構成

### 1.1 ディレクトリ構造

```
auto-movie-editor/
├── CLAUDE.md                 # ルート: プロジェクト共通設定
├── .claude/
│   ├── agents/               # 12個のエージェント
│   ├── skills/               # 19個のスキル
│   └── settings.local.json   # ローカル設定
│
├── frontend/                 # Next.js Webアプリケーション
│   ├── CLAUDE.md             # frontend固有設定（オプション）
│   ├── app/                  # プレゼンテーション層
│   ├── src/                  # ビジネスロジック層
│   ├── prisma/               # データベーススキーマ
│   └── docs/                 # フロントエンドドキュメント
│
├── terraform/                # インフラ・バックエンドサービス
│   ├── CLAUDE.md             # terraform固有設定（オプション）
│   ├── app/                  # Cloud Runサービス群
│   ├── environments/         # 環境別設定
│   └── modules/              # 共通モジュール
│
├── docs/                     # プロジェクト全体ドキュメント
├── scripts/                  # ユーティリティスクリプト
└── mcp-servers/              # MCPサーバー設定
```

### 1.2 技術スタック

| 領域 | 技術 |
|------|------|
| Frontend | Next.js 15, React, TypeScript, Tailwind CSS |
| Backend API | Next.js API Routes (クリーンアーキテクチャ) |
| Database | PostgreSQL, Prisma ORM |
| Infrastructure | Terraform, Google Cloud Run, Pub/Sub |
| Python Services | FastAPI, Pydantic, Cloud Run Jobs |

---

## 2. CLAUDE.md階層構造

### 2.1 読み込み順序

```
┌─────────────────────────────────────────────────────────────┐
│ 1. ~/.claude/CLAUDE.md（ユーザー共通設定）                    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. /CLAUDE.md（プロジェクトルート）                           │
│    - 言語設定、共通ルール、アーキテクチャ概要                  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. /frontend/CLAUDE.md（オンデマンド読み込み）                │
│    - Next.js固有、TypeScriptルール、テスト設定                │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. /terraform/CLAUDE.md（オンデマンド読み込み）               │
│    - Terraform固有、Pythonサービス、Cloud Run設定             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 各レベルの役割

| レベル | ファイル | 内容 |
|--------|----------|------|
| ルート | `/CLAUDE.md` | 言語設定、共通ルール、エージェント/スキル概要 |
| Frontend | `/frontend/CLAUDE.md` | TypeScript、Next.js、Prisma固有ルール |
| Terraform | `/terraform/CLAUDE.md` | Python、Terraform、Cloud Run固有ルール |

### 2.3 重要な制約

**スキルとエージェントの配置場所は固定:**

```
# ✅ 正しい配置（Claude Codeが認識する）
.claude/skills/typescript-expert/SKILL.md
.claude/agents/code-reviewer.md

# ❌ 認識されない配置
frontend/.claude/skills/...
terraform/.claude/agents/...
```

CLAUDE.mdでカスタムパスを指定することは**できません**。

---

## 3. スキルとエージェント

### 3.1 利用可能なスキル（19個）

| カテゴリ | スキル | 用途 |
|----------|--------|------|
| **ドキュメント** | adr-writer, design-doc-writer, plan-writer, prd-writer, rules-writer | 各種ドキュメント作成 |
| **Frontend** | typescript-expert, ui-component-writer, nextjs-api-writer, prisma-migration | TypeScript/Next.js開発 |
| **Terraform** | python-service-writer, pydantic-model-writer, pubsub-pipeline-writer, cloudrun-deploy, terraform-module-writer | Python/インフラ開発 |
| **その他** | git-workflow, skill-suggester, troubleshooting-writer | ワークフロー支援 |

### 3.2 利用可能なエージェント（12個）

| カテゴリ | エージェント | 用途 |
|----------|--------------|------|
| **コードレビュー** | code-reviewer, doc-analyzer, test-runner | 品質管理 |
| **GitHub** | github-workflow-manager | PR/Issue管理 |
| **Python** | python-service-architect-agent, python-testing-agent, shared-library-manager-agent | Pythonサービス開発 |
| **インフラ** | cloudrun-deployment-agent, terraform-infrastructure-agent, pipeline-debugger-agent | デプロイ・インフラ |
| **その他** | database-migration-agent, documentation-generator-agent | DB・ドキュメント |

### 3.3 スキル作成のベストプラクティス

```yaml
---
name: my-skill-name          # 小文字+ハイフンのみ（最大64文字）
description: |
  What: スキルの機能説明
  When: 使用タイミング（トリガーキーワードを含める）
  References: 参照ドキュメント
allowed-tools: Read, Write, Edit, Glob
---

# スキルタイトル

## 核心ルール
最も重要なルールを最初に記載

## パターン/テンプレート
コード例やテンプレート

## チェックリスト
作業完了時の確認項目
```

---

## 4. トークン最適化

### 4.1 推奨サイズ

| ファイル | 推奨サイズ | 現状 |
|----------|-----------|------|
| `/CLAUDE.md` | 5K〜10K tokens | 要確認 |
| サブディレクトリCLAUDE.md | 3K〜5K tokens | - |
| スキル（SKILL.md） | 500行以下 | ✅ 適正 |

### 4.2 トークン削減テクニック

**DO:**
```markdown
## コマンド
pnpm check:all  # 品質チェック（lint + typecheck + test）
```

**DON'T:**
```markdown
## コマンド
品質チェックを実行するには、pnpm check:allコマンドを使用します。
このコマンドは、ESLintによるリント、TypeScriptによる型チェック、
Vitestによるテスト実行を順番に行い、すべてのチェックが
パスすることを確認します。
```

### 4.3 参照による分離

```markdown
# ✅ オンデマンド読み込み（トークン節約）
詳細は frontend/docs/rules/typescript.md を参照。

# ❌ 起動時に全て読み込まれる（トークン消費）
@frontend/docs/rules/typescript.md
```

---

## 5. 効果的な記述方法

### 5.1 このリポジトリの必須記載事項

```markdown
# CLAUDE.md テンプレート

## 言語設定
- 返答: 日本語
- コード: 英語

## 重要コマンド
pnpm check:all          # 品質チェック
pnpm db:migrate:dev     # マイグレーション
pnpm dev                # 開発サーバー

## 絶対ルール
1. any型禁止 → unknown + 型ガード
2. PRの前に pnpm check:all
3. 6ファイル以上の変更 → ADR作成

## アーキテクチャ
クリーンアーキテクチャ + DDD
domain → usecases → controllers → infrastructure
```

### 5.2 具体的 vs 曖昧

| ❌ 曖昧 | ✅ 具体的 |
|---------|----------|
| コードを適切にドキュメント化 | 公開関数にはJSDocを追加 |
| ベストプラクティスに従う | any禁止、unknown + 型ガードを使用 |
| テストを書く | カバレッジ70%以上、境界値テスト必須 |

### 5.3 強調の使い方

```markdown
# 重要度に応じた強調

**MUST:** PRの前に pnpm check:all を実行
**IMPORTANT:** any型は完全禁止
**NOTE:** 詳細は docs/rules/ を参照
```

---

## 6. 避けるべきアンチパターン

### 6.1 ❌ スキル/エージェントの誤配置

```bash
# ❌ 認識されない
frontend/.claude/skills/my-skill/SKILL.md
terraform/.claude/agents/my-agent.md

# ✅ 正しい配置
.claude/skills/my-skill/SKILL.md
.claude/agents/my-agent.md
```

### 6.2 ❌ 重複した情報

```markdown
# ❌ 悪い例: ルートとfrontendで重複
# /CLAUDE.md
any型は禁止です。unknownを使用してください。

# /frontend/CLAUDE.md
any型は使用しないでください。unknownと型ガードを使います。
```

```markdown
# ✅ 良い例: ルートに共通ルール、サブは参照のみ
# /CLAUDE.md
any型禁止 → unknown + 型ガード

# /frontend/CLAUDE.md
型安全性の詳細は /CLAUDE.md を参照
```

### 6.3 ❌ 古い情報の放置

```markdown
# ❌ 悪い例
## ロギング
Winston を使用  # 実際は Pino に移行済み
```

**対策:** 定期的なレビュー（四半期ごと）

### 6.4 ❌ コードスタイルの詳細記述

```markdown
# ❌ 悪い例: 50行のスタイルガイド
- インデント2スペース
- セミコロン省略
- シングルクォート
...

# ✅ 良い例
既存コードのパターンに従う。変更後は pnpm lint を実行。
```

---

## 7. 運用ガイドライン

### 7.1 更新タイミング

CLAUDE.mdを更新すべき場合:
- [ ] 新しい主要な依存関係を追加
- [ ] アーキテクチャパターンを変更
- [ ] ディレクトリ構造を変更
- [ ] 新しい環境変数を追加
- [ ] 新しいスキル/エージェントを追加

### 7.2 スキル/エージェント追加手順

```bash
# 1. 正しい場所にファイル作成
mkdir -p .claude/skills/new-skill
touch .claude/skills/new-skill/SKILL.md

# 2. SKILL.md を編集（フロントマター必須）

# 3. 動作確認
# Claude Codeを再起動して認識されるか確認
```

### 7.3 チェックリスト

**CLAUDE.md作成時:**
- [ ] 10K tokens以下
- [ ] 絶対ルールは5個以下
- [ ] 曖昧な指示がない
- [ ] 古い情報がない

**スキル作成時:**
- [ ] `.claude/skills/` に配置
- [ ] name: 小文字+ハイフンのみ
- [ ] description: トリガーキーワードを含む
- [ ] 500行以下

**エージェント作成時:**
- [ ] `.claude/agents/` に配置
- [ ] 明確な起動条件を記載
- [ ] 他エージェントとの役割分担が明確

---

## 付録: 現在の構成一覧

### スキル一覧（19個）

```
.claude/skills/
├── adr-writer/
├── cloudrun-deploy/
├── design-doc-writer/
├── git-workflow/
├── nextjs-api-writer/
├── plan-writer/
├── prd-writer/
├── prisma-migration/
├── pubsub-pipeline-writer/
├── pydantic-model-writer/
├── python-service-writer/
├── rules-writer/
├── skill-suggester/
├── terraform-module-writer/
├── troubleshooting-writer/
├── typescript-expert/
└── ui-component-writer/
```

### エージェント一覧（12個）

```
.claude/agents/
├── cloudrun-deployment-agent.md
├── code-reviewer.md
├── database-migration-agent.md
├── doc-analyzer.md
├── documentation-generator-agent.md
├── github-workflow-manager.md
├── pipeline-debugger-agent.md
├── python-service-architect-agent.md
├── python-testing-agent.md
├── shared-library-manager-agent.md
├── terraform-infrastructure-agent.md
└── test-runner.md
```

---

## 変更履歴

| 日付 | 変更内容 |
|------|----------|
| 2025-12-21 | auto-movie-editor向けに全面改訂 |

---

*このドキュメントはauto-movie-editorリポジトリのClaude Code設定ガイドです。*
