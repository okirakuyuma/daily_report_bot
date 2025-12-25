# モノレポ Skills・サブエージェント設計書

## 概要

Auto Movie Editorモノレポにおける Skills・サブエージェントの設計仕様を定義。
仕様駆動開発ワークフローを支援し、frontend/terraform両ドメインでの開発効率化と品質向上を実現する。

## 背景とコンテキスト

### 前提ドキュメント

- `docs/best/skills-spec-driven-workflow.md`: Skills活用ガイド
- `docs/best/skills-subagents-common-design.md`: サブエージェント共通設計

### 解決する課題

| 課題 | 影響 | 解決策 |
|------|------|--------|
| ドキュメント作成の非効率 | 毎回template.md参照が必要 | ドキュメントSkillsで自動化 |
| frontend/terraformの技術スタック差異 | 異なるルール適用が必要 | ドメイン固有Skillsで対応 |
| 繰り返し作業の手動実行 | 時間浪費・ミス発生 | 専門Skillsで標準化 |
| コードレビュー品質のばらつき | レビュー観点漏れ | 専門サブエージェントで統一 |

### 現状分析

```
現在の構造:
/.claude/
├── agents/                    # 既存エージェント定義
└── settings.local.json

/frontend/
├── .claude/
│   └── settings.local.json
├── AGENTS.md                  # フロントエンド用エージェント定義
└── docs/
    ├── adr/template.md
    ├── design/template.md
    ├── plans/template.md
    ├── prd/template.md
    ├── rules/
    └── troubleshooting/

/terraform/
├── .claude/
│   ├── plans/
│   └── settings.local.json
├── CLAUDE.md                  # Terraform専用指示書
└── docs/
    ├── adr/template.md
    ├── design/template.md
    ├── plans/template.md
    ├── prd/template.md
    ├── rules/
    └── agents/               # 既存エージェント定義

/terraform/app/               # Pythonサービス群
├── audio-extractor/
├── json-segmentation/
├── mfa_correction/
├── quality-assurance/
├── speech-recognition/
├── subtitle-format/
├── transcription_pipeline/
└── xml-generator/
```

---

## Skills vs サブエージェント 判断基準

```
外部サービスアクセス必要?
    │
   Yes → MCP Server（既存: serena, sequential-thinking, slack-notify等）
    │
   No
    │
独立したコンテキストが有効?（並列処理、長時間、専門分析）
    │
   Yes → サブエージェント（Task tool経由）
    │       - 複数ファイル横断分析
    │       - 5ステップ以上の連続作業
    │       - 専門知識が必要
    │       - 並列実行で効率化可能
    │
   No → Skills（.claude/skills/）
           - テンプレートベースのドキュメント作成
           - 手順的知識の提供
           - ワークフロー定義
           - 軽量な繰り返しタスク
```

---

## Skills 配置設計

### 階層構造

```
/.claude/skills/                    # ルートレベル（モノレポ共通）
├── prd-writer/SKILL.md
├── design-doc-writer/SKILL.md
├── adr-writer/SKILL.md
├── plan-writer/SKILL.md
├── troubleshooting-writer/SKILL.md
├── rules-writer/SKILL.md
├── skill-suggester/SKILL.md
└── git-workflow/SKILL.md

/frontend/.claude/skills/           # frontend固有
├── typescript-expert/SKILL.md
├── ui-component-writer/SKILL.md
├── prisma-migration/SKILL.md
└── nextjs-api-writer/SKILL.md

/terraform/.claude/skills/          # terraform固有
├── python-service-writer/SKILL.md
├── terraform-module-writer/SKILL.md
├── cloudrun-deploy/SKILL.md
├── pubsub-pipeline-writer/SKILL.md
└── pydantic-model-writer/SKILL.md
```

---

## ルートレベル共通 Skills

### 1. prd-writer

```yaml
name: prd-writer
description: |
  Create and update Product Requirements Documents (PRD).
  Use when user mentions PRD, requirements, feature specification,
  or asks to document a new feature.
  Automatically detects target: frontend/docs/prd/ or terraform/docs/prd/
allowed-tools: Read, Write, Edit, Glob, Grep
```

**責務**:
- PRDの新規作成・更新
- 対象ディレクトリ（frontend/terraform）の自動判断
- 対応する`template.md`の読み込みとフォーマット適用

**処理フロー**:
1. ユーザーリクエストからfrontend/terraformを判断（キーワード: UI, API, TypeScript → frontend / Python, GCP, Cloud Run → terraform）
2. `{target}/docs/prd/template.md` を読み込み
3. テンプレートに従ってPRDを作成
4. 既存PRDとの一貫性を確認

**出力パス**:
- frontend: `frontend/docs/prd/{feature-name}.md`
- terraform: `terraform/docs/prd/{feature-name}.md`

---

### 2. design-doc-writer

```yaml
name: design-doc-writer
description: |
  Create and update technical design documents.
  Use when user mentions design doc, technical design, architecture design,
  system design, or API design.
  Automatically detects target: frontend/docs/design/ or terraform/docs/design/
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
```

**責務**:
- 技術設計書の新規作成・更新
- 関連PRDの参照
- ADR作成要否の判断・提案

**処理フロー**:
1. 対象ディレクトリの判断
2. `{target}/docs/design/template.md` を読み込み
3. 関連PRDを検索・参照
4. テンプレートに従って設計書を作成
5. ADRが必要な場合は提案

---

### 3. adr-writer

```yaml
name: adr-writer
description: |
  Create Architecture Decision Records (ADR).
  Use when user mentions ADR, architecture decision, technical decision,
  or when a significant technical choice needs to be documented.
  Use for: new library adoption, architecture pattern changes, breaking changes.
allowed-tools: Read, Write, Edit, Glob, Grep
```

**責務**:
- ADRの新規作成
- ADR番号の自動採番
- 関連ドキュメントへのリンク

**ADR作成トリガー**:
- 新しいライブラリ/フレームワークの採用
- アーキテクチャパターンの変更
- 破壊的変更を伴う決定
- 6ファイル以上の変更（`documentation-criteria.md`準拠）
- 複数選択肢からの重要な選択

---

### 4. plan-writer

```yaml
name: plan-writer
description: |
  Create implementation plans and task breakdowns.
  Use when user mentions plan, implementation plan, task breakdown,
  sprint planning, or milestone planning.
  Outputs to: frontend/docs/plans/ or terraform/docs/plans/
allowed-tools: Read, Write, Edit, Glob, Grep
```

**命名規則**:
- `{YYYYMMDD}-{type}-{summary}.md`
- type: feature, fix, refactor, migration, etc.

---

### 5. troubleshooting-writer

```yaml
name: troubleshooting-writer
description: |
  Create and update troubleshooting guides.
  Use when user encounters an error, bug, or issue that should be documented,
  or when documenting known issues and their solutions.
  Records: error messages, root causes, solutions, prevention measures.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
```

**構造**:
```markdown
## 問題: {問題名}

### 症状
{エラーメッセージ、ログ出力}

### 原因
{根本原因の分析}

### 解決方法
1. ステップ1
2. ステップ2

### 予防策
{再発防止策}
```

---

### 6. rules-writer

```yaml
name: rules-writer
description: |
  Create and update project rules and conventions.
  Use when user mentions coding standards, conventions, rules,
  guidelines, or best practices that should be documented.
  Categories: MUST (required), SHOULD (recommended), MUST NOT (prohibited)
allowed-tools: Read, Write, Edit, Glob, Grep
```

---

### 7. skill-suggester

```yaml
name: skill-suggester
description: |
  Analyze work patterns and suggest new Skills or subagents.
  Use PROACTIVELY after completing tasks to identify automation opportunities.
  Detects: repeated document creation, pattern-based code generation, multi-step workflows.
allowed-tools: Read, Glob, Grep
```

**提案フォーマット**:
```
💡 Skill提案: {skill-name}
━━━━━━━━━━━━━━━━━━━━━━━━
検出パターン: {具体的な繰り返しパターン}
提案理由: {効率化の理由}
推定効果: {時間削減、エラー削減}

作成を希望しますか？
```

---

### 8. git-workflow

```yaml
name: git-workflow
description: |
  Guide git operations following project conventions.
  Use when committing, branching, or creating PRs.
  Conventions: Conventional Commits, feature/fix/chore branches.
allowed-tools: Bash, Read
```

**責務**:
- コミットメッセージのConventional Commits準拠チェック
- ブランチ命名規則の確認（feature/, fix/, chore/）
- PR作成ガイダンス

---

## frontend固有 Skills

### 1. typescript-expert

```yaml
name: typescript-expert
description: |
  Provide TypeScript best practices and type-safe implementations.
  Use when working with TypeScript code, type definitions, or fixing type errors.
  Key rules: no any, use unknown with type guards, strict typing.
  References: frontend/docs/rules/typescript.md
allowed-tools: Read, Write, Edit, Grep, Glob
```

**責務**:
- `any`禁止ルールの適用
- `unknown` + 型ガードパターンの実装
- ジェネリクス活用のガイド
- APIレスポンスの安全な抽出パターン

**典型パターン**:
```typescript
// NG
function f(x: any) { return x.id; }

// OK
function f(x: unknown) {
  return isObject(x) && 'id' in x ? x.id : null;
}
```

---

### 2. ui-component-writer

```yaml
name: ui-component-writer
description: |
  Create UI components following design system guidelines.
  Use when creating buttons, forms, modals, cards, or other UI elements.
  References: frontend/docs/design/ui-design-system.md, ui-component-catalog.md
  Style: GCP-inspired enterprise SaaS, Tailwind + CVA
allowed-tools: Read, Write, Edit, Glob
```

**責務**:
- デザインシステム準拠のコンポーネント作成
- GCP UIパターンの適用
- Tailwind + class-variance-authority の活用
- ミニマルUI方針の遵守

---

### 3. prisma-migration

```yaml
name: prisma-migration
description: |
  Guide Prisma database migrations safely.
  Use when creating, modifying, or applying database migrations.
  References: frontend/docs/rules/database-migration-guide.md
  Commands: pnpm db:migrate:dev, pnpm db:studio
allowed-tools: Read, Write, Bash
```

**責務**:
- マイグレーションファイルの作成ガイド
- 影響範囲の確認
- ロールバック手順の提示

---

### 4. nextjs-api-writer

```yaml
name: nextjs-api-writer
description: |
  Create Next.js API routes following clean architecture.
  Use when creating API endpoints in app/api/.
  Architecture: domain → usecases → controllers → infrastructure
  References: frontend/docs/rules/architecture/frontend-architecture.md
allowed-tools: Read, Write, Edit, Glob
```

**責務**:
- App Router APIルートの作成
- クリーンアーキテクチャのレイヤー分離
- 型安全なリクエスト/レスポンス処理

---

## terraform固有 Skills

### 1. python-service-writer

```yaml
name: python-service-writer
description: |
  Create Python services following project architecture.
  Use when implementing new API endpoints or services in terraform/app/.
  References: terraform/docs/rules/python.md, python-pydantic-validation.md
  Architecture: functions → services → models
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
```

**責務**:
- Pythonサービスの新規作成
- Pydanticモデルによるバリデーション
- 型ヒントの適用
- エラーハンドリングパターン

**ディレクトリ構造**:
```
terraform/app/{service-name}/
├── app/
│   ├── functions/      # ビジネスロジック
│   ├── services/       # サービス層
│   ├── models/         # Pydanticモデル
│   └── main.py         # エントリポイント
├── tests/
├── Dockerfile
└── requirements.txt
```

---

### 2. terraform-module-writer

```yaml
name: terraform-module-writer
description: |
  Create and update Terraform modules and configurations.
  Use when modifying terraform/modules/ or terraform/environments/.
  Safety: always run fmt, validate, plan before apply.
allowed-tools: Read, Write, Edit, Bash
```

**責務**:
- Terraformモジュールの作成・更新
- 事前検証（fmt, validate, plan）
- 環境間差分の管理

**安全チェックリスト**:
- [ ] `terraform fmt` でフォーマット統一
- [ ] `terraform validate` でエラーなし
- [ ] `terraform plan` の出力を確認
- [ ] staging で先行テスト（production 適用時）

---

### 3. cloudrun-deploy

```yaml
name: cloudrun-deploy
description: |
  Guide Cloud Run deployment process.
  Use when deploying services to GCP Cloud Run.
  Includes: Docker build, push, deploy commands.
  References: terraform/docs/rules/cloudrun-job-local-development.md
allowed-tools: Read, Bash
```

**責務**:
- デプロイ手順のガイド
- 環境変数の確認
- ロールバック手順の提示

---

### 4. pubsub-pipeline-writer

```yaml
name: pubsub-pipeline-writer
description: |
  Create and debug Pub/Sub pipeline components.
  Use when working with message processing, pipeline triggers, or Pub/Sub integration.
  Services: transcription_pipeline, json-segmentation, mfa_correction, xml-generator
allowed-tools: Read, Write, Edit, Grep, Bash
```

**責務**:
- Pub/Subメッセージハンドラの作成
- パイプラインフローの理解と実装
- メッセージスキーマの定義

**パイプラインフロー**:
```
audio-extractor → speech-recognition → mfa_correction →
json-segmentation → xml-generator
```

---

### 5. pydantic-model-writer

```yaml
name: pydantic-model-writer
description: |
  Create Pydantic models for request/response validation.
  Use when defining API schemas, message formats, or data models.
  References: terraform/docs/rules/python-pydantic-validation.md
allowed-tools: Read, Write, Edit
```

**責務**:
- Pydanticモデルの作成
- バリデーションルールの定義
- OpenAPIスキーマ生成対応

---

## サブエージェント設計

### 配置場所

```
/.claude/agents/                    # ルートレベル（既存）
├── code-reviewer.md
├── test-runner.md
└── doc-analyzer.md

/frontend/docs/agents/              # frontend固有（既存）

/terraform/docs/agents/             # terraform固有（既存）
├── terraform-infrastructure-agent.md
├── python-service-architect-agent.md
├── pipeline-debugger-agent.md
├── python-testing-agent.md
├── database-migration-agent.md
├── documentation-generator-agent.md
├── cloudrun-deployment-agent.md
└── shared-library-manager-agent.md
```

### ルートレベル共通サブエージェント

#### 1. code-reviewer

```yaml
name: code-reviewer
description: |
  Review code for quality, maintainability, and adherence to best practices.
  Use after implementing new features, fixing bugs, or making significant changes.
  References: docs/claude_code_review/general_code_review_guide.md
tools: Read, Grep, Glob
model: sonnet
```

**起動条件**:
- コード実装完了後
- PR作成前
- 明示的なレビュー依頼

**責務**:
- コード品質チェック（DRY, SOLID原則）
- セキュリティリスクの検出
- パフォーマンス問題の指摘
- 改善提案の生成

---

#### 2. test-runner

```yaml
name: test-runner
description: |
  Execute tests and analyze results.
  Use after code changes to verify functionality.
  Frontend: pnpm test, Terraform: pytest
tools: Bash, Read, Grep
model: haiku
```

**責務**:
- テストコマンドの実行
- 失敗テストの分析
- カバレッジレポートの解釈
- 修正提案

---

#### 3. doc-analyzer

```yaml
name: doc-analyzer
description: |
  Analyze documentation for consistency and completeness.
  Use after major changes or during quality reviews.
  Checks cross-references, broken links, and template compliance.
tools: Read, Grep, Glob
model: haiku
```

**責務**:
- ドキュメント間の整合性確認
- リンク切れの検出
- 更新漏れの指摘
- テンプレート準拠の確認

---

## 実装計画

### フェーズ1: ルートレベル共通Skills

**目的**: 仕様駆動開発の基盤構築

**実装内容**:
1. `/.claude/skills/` ディレクトリ構造作成
2. ドキュメント系Skills作成（prd-writer, design-doc-writer, adr-writer, plan-writer, troubleshooting-writer, rules-writer）
3. skill-suggester, git-workflow作成

**完了条件**:
- [ ] 全Skillが正しく認識される
- [ ] 各Skillがtemplate.mdを読み込んで出力できる
- [ ] frontend/terraformの判断が正しく動作する

---

### フェーズ2: frontend固有Skills

**目的**: TypeScript/Next.js開発の効率化

**実装内容**:
1. `/frontend/.claude/skills/` ディレクトリ構造作成
2. typescript-expert, ui-component-writer, prisma-migration, nextjs-api-writer作成

**完了条件**:
- [ ] TypeScript開発時にtypescript-expertが自動起動
- [ ] UI作成リクエストでui-component-writerが起動

---

### フェーズ3: terraform固有Skills

**目的**: Python/GCP開発の効率化

**実装内容**:
1. `/terraform/.claude/skills/` ディレクトリ構造作成
2. python-service-writer, terraform-module-writer, cloudrun-deploy, pubsub-pipeline-writer, pydantic-model-writer作成

**完了条件**:
- [ ] Pythonサービス作成時に適切なSkillが起動
- [ ] Terraform操作時にterraform-module-writerが起動

---

### フェーズ4: サブエージェント整備

**目的**: 品質管理の自動化

**実装内容**:
1. ルートレベルの共通サブエージェント定義
2. 既存エージェント定義の整理・統合

**完了条件**:
- [ ] Task toolからサブエージェントが呼び出せる
- [ ] 各エージェントが適切なツールを使用できる

---

## Skill優先度マトリクス

| Skill | 頻度 | 効果 | 実装難易度 | 優先度 |
|-------|------|------|-----------|--------|
| prd-writer | 中 | 高 | 低 | 🔴 最優先 |
| design-doc-writer | 中 | 高 | 低 | 🔴 最優先 |
| adr-writer | 低 | 高 | 低 | 🔴 最優先 |
| plan-writer | 高 | 中 | 低 | 🔴 最優先 |
| typescript-expert | 高 | 高 | 中 | 🟡 優先 |
| python-service-writer | 高 | 高 | 中 | 🟡 優先 |
| ui-component-writer | 中 | 中 | 中 | 🟢 推奨 |
| terraform-module-writer | 低 | 高 | 高 | 🟢 推奨 |
| pubsub-pipeline-writer | 中 | 高 | 高 | 🟢 推奨 |
| skill-suggester | 低 | 中 | 中 | 🔵 任意 |

---

## テスト戦略

### Skill検証

| Skill | テストシナリオ | 期待結果 |
|-------|---------------|----------|
| prd-writer | 「フロントエンドのPRD作成」 | frontend/docs/prd/にtemplate.md準拠で出力 |
| prd-writer | 「パイプラインのPRD作成」 | terraform/docs/prd/にtemplate.md準拠で出力 |
| typescript-expert | 「anyを使わずに型定義」 | unknown+型ガードパターンを提案 |
| python-service-writer | 「新しいサービス作成」 | Pydanticモデル付きの標準構造を生成 |

### サブエージェント検証

| エージェント | テストシナリオ | 期待結果 |
|-------------|---------------|----------|
| code-reviewer | コード変更後に呼び出し | レビューコメント生成 |
| test-runner | テスト実行依頼 | 結果分析と報告 |
| doc-analyzer | ドキュメント整合性チェック | 問題点リスト出力 |

---

## ディレクトリ構造（完成形）

```
/.claude/
├── skills/
│   ├── prd-writer/SKILL.md
│   ├── design-doc-writer/SKILL.md
│   ├── adr-writer/SKILL.md
│   ├── plan-writer/SKILL.md
│   ├── troubleshooting-writer/SKILL.md
│   ├── rules-writer/SKILL.md
│   ├── skill-suggester/SKILL.md
│   └── git-workflow/SKILL.md
├── agents/
│   ├── code-reviewer.md
│   ├── test-runner.md
│   └── doc-analyzer.md
└── settings.local.json

/frontend/.claude/
├── skills/
│   ├── typescript-expert/SKILL.md
│   ├── ui-component-writer/SKILL.md
│   ├── prisma-migration/SKILL.md
│   └── nextjs-api-writer/SKILL.md
└── settings.local.json

/terraform/.claude/
├── skills/
│   ├── python-service-writer/SKILL.md
│   ├── terraform-module-writer/SKILL.md
│   ├── cloudrun-deploy/SKILL.md
│   ├── pubsub-pipeline-writer/SKILL.md
│   └── pydantic-model-writer/SKILL.md
├── plans/
└── settings.local.json
```

---

## 参考資料

- `docs/best/skills-spec-driven-workflow.md`
- `docs/best/skills-subagents-common-design.md`
- `frontend/AGENTS.md`
- `terraform/CLAUDE.md`
- `terraform/docs/agents/`
- [Agent Skills - Claude Code Docs](https://code.claude.com/docs/en/skills)

---

## 更新履歴

| 日付 | 版 | 変更内容 | 作成者 |
|------|-----|----------|--------|
| 2025-12-21 | 1.0 | 初版作成 | Claude |
