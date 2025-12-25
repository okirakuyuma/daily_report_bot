# Skills・サブエージェント共通設計書

## 概要

本ドキュメントは、kessan_line_backモノレポにおける共通Skills・サブエージェントの設計仕様を定義します。仕様駆動開発ワークフローを支援し、ドキュメント作成の効率化と品質向上を実現します。

## 背景とコンテキスト

### 前提となるドキュメント

- `docs/skills_and_spec_driven_workflow.md`: Skills活用ガイド
- `docs/subagent_best_practices.md`: サブエージェントベストプラクティス

### 解決する問題

1. ドキュメント作成時のフォーマット不統一
2. 繰り返し作業による効率低下
3. 複雑なタスクにおけるコンテキスト管理の困難さ
4. infra/webapp間でのドキュメント構造の差異

### 現状の課題

- 各ディレクトリにtemplate.mdが存在するが、手動参照が必要
- Skills/サブエージェントが未整備
- 仕様駆動開発ワークフローの自動化が不十分

---

## Skills vs サブエージェント 判断基準

```
外部サービスアクセス必要?
    │
   Yes → MCP
    │
   No
    │
独立したコンテキストが有効?
    │
   Yes → サブエージェント（Task tool経由）
    │       - 複数ファイル分析
    │       - 専門知識が必要
    │       - 5ステップ以上の連続作業
    │       - 並列処理が有効
    │
   No → Skills（.claude/skills/）
           - テンプレートベースのドキュメント作成
           - 手順的知識の提供
           - ワークフロー定義
```

---

## 共通Skills設計

### 配置場所

```
/.claude/skills/
├── prd-writer/SKILL.md
├── design-doc-writer/SKILL.md
├── adr-writer/SKILL.md
├── plan-writer/SKILL.md
├── troubleshooting-writer/SKILL.md
├── rules-writer/SKILL.md
└── skill-suggester/SKILL.md
```

### 1. prd-writer

```yaml
name: prd-writer
description: |
  Create and update Product Requirements Documents (PRD).
  Use when user mentions PRD, requirements, feature specification,
  or asks to document a new feature.
  Output location: webapp/docs/prd/ or infra/docs/prd/
allowed-tools: Read, Write, Edit, Glob, Grep
```

**責務**:
- PRDの新規作成・更新
- 対象ディレクトリ（webapp/infra）の判断
- 対応するtemplate.mdの読み込みとフォーマット適用

**処理フロー**:
1. ユーザーリクエストからwebapp/infraを判断
2. `{target}/docs/prd/template.md` を読み込み
3. テンプレートに従ってPRDを作成
4. 既存PRDとの一貫性を確認

**出力パス**:
- webapp: `webapp/docs/prd/{feature-name}.md`
- infra: `infra/docs/prd/{feature-name}.md`

---

### 2. design-doc-writer

```yaml
name: design-doc-writer
description: |
  Create and update technical design documents.
  Use when user mentions design doc, technical design, architecture design,
  system design, or API design.
  Output location: webapp/docs/design/ or infra/docs/design/
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

**出力パス**:
- webapp: `webapp/docs/design/{feature-name}.md`
- infra: `infra/docs/design/{feature-name}.md`

---

### 3. adr-writer

```yaml
name: adr-writer
description: |
  Create Architecture Decision Records (ADR).
  Use when user mentions ADR, architecture decision, technical decision,
  or when a significant technical choice needs to be documented.
  Output location: webapp/docs/adr/ or infra/docs/adr/
allowed-tools: Read, Write, Edit, Glob, Grep
```

**責務**:
- ADRの新規作成
- ADR番号の自動採番
- 関連ドキュメントへのリンク

**処理フロー**:
1. 対象ディレクトリの判断
2. 既存ADR一覧を取得し次番号を決定
3. `{target}/docs/adr/template.md` を読み込み
4. ADRを作成

**ADR作成トリガー**:
- 新しいライブラリ/フレームワークの採用
- アーキテクチャパターンの変更
- 破壊的変更を伴う決定
- 複数選択肢からの重要な選択

**出力パス**:
- webapp: `webapp/docs/adr/ADR-{number}-{title}.md`
- infra: `infra/docs/adr/ADR-{number}-{title}.md`

---

### 4. plan-writer

```yaml
name: plan-writer
description: |
  Create implementation plans and task breakdowns.
  Use when user mentions plan, implementation plan, task breakdown,
  sprint planning, or milestone planning.
  Output location: webapp/docs/plan/ or infra/docs/plan/
allowed-tools: Read, Write, Edit, Glob, Grep
```

**責務**:
- 実装計画書の作成
- フェーズ分けとタスク分解
- 完了条件とE2E確認手順の定義

**処理フロー**:
1. 対象ディレクトリの判断
2. `{target}/docs/plan/template.md` を読み込み
3. 関連PRD・設計書を参照
4. 計画書を作成

**出力パス**:
- webapp: `webapp/docs/plan/{YYYYMMDD}-{type}-{summary}.md`
- infra: `infra/docs/plan/{YYYYMMDD}-{type}-{summary}.md`

---

### 5. troubleshooting-writer

```yaml
name: troubleshooting-writer
description: |
  Create and update troubleshooting guides.
  Use when user encounters an error, bug, or issue that should be documented,
  or when documenting known issues and their solutions.
  Output location: webapp/docs/troubleshooting/ or infra/docs/troubleshooting/
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
```

**責務**:
- トラブルシューティングガイドの作成・更新
- エラーメッセージの正確な記録
- 解決方法の検証と記載

**処理フロー**:
1. 問題カテゴリの特定
2. 既存ガイドの有無を確認
3. 新規作成または既存ガイドへの追記

**出力パス**:
- `{target}/docs/troubleshooting/{issue-category}.md`

---

### 6. rules-writer

```yaml
name: rules-writer
description: |
  Create and update project rules and conventions.
  Use when user mentions coding standards, conventions, rules,
  guidelines, or best practices that should be documented.
  Output location: webapp/docs/rules/ or infra/docs/rules/
allowed-tools: Read, Write, Edit, Glob, Grep
```

**責務**:
- プロジェクトルール・規約の作成
- MUST/SHOULD/MUST NOTの分類
- 良い例・悪い例の提示

**出力パス**:
- `{target}/docs/rules/{category}.md`

---

### 7. skill-suggester

```yaml
name: skill-suggester
description: |
  Analyze work patterns and suggest new Skills or subagents.
  Use PROACTIVELY after completing tasks to identify automation opportunities.
  MUST be invoked at the end of complex tasks.
allowed-tools: Read, Glob, Grep
```

**責務**:
- 繰り返しパターンの検出
- 新規Skill/サブエージェントの提案
- ドキュメント更新の提案

**検出パターン**:

| 種類 | 検出条件 | 提案内容 |
|------|----------|----------|
| Skill | 同じ構造のドキュメントを3回以上作成 | 新規Skill |
| Skill | 同じパターンのコードを繰り返し生成 | 新規Skill |
| サブエージェント | 複数ファイルの分析が必要なタスク | 新規サブエージェント |
| サブエージェント | 5ステップ以上の連続作業 | 新規サブエージェント |

---

## 共通サブエージェント設計

### 配置場所

```
/.claude/agents/
├── code-reviewer.md
├── test-runner.md
└── doc-analyzer.md
```

### 1. code-reviewer

**目的**: コード品質の分析とレビューコメント生成

**トリガー条件**:
- コード実装完了後
- PR作成前
- 明示的なレビュー依頼

**ツール**: Read, Grep, Glob

**責務**:
- コード品質チェック（DRY, SOLID原則）
- セキュリティリスクの検出
- パフォーマンス問題の指摘
- 改善提案の生成

**サブエージェント定義**:
```yaml
name: code-reviewer
description: |
  Review code for quality, maintainability, and adherence to best practices.
  Use after implementing new features, fixing bugs, or making significant changes.
  Provides actionable feedback on design, code quality, testing, and documentation.
tools: Read, Grep, Glob
model: sonnet
```

---

### 2. test-runner

**目的**: テスト実行と結果分析

**トリガー条件**:
- 実装完了後
- CI/CD前の事前確認
- テスト失敗時の調査

**ツール**: Bash, Read, Grep

**責務**:
- テストコマンドの実行
- 失敗テストの分析
- カバレッジレポートの解釈
- 修正提案

**サブエージェント定義**:
```yaml
name: test-runner
description: |
  Execute tests and analyze results.
  Use after code changes to verify functionality.
  Provides failure analysis and coverage reporting.
tools: Bash, Read, Grep
model: haiku
```

---

### 3. doc-analyzer

**目的**: ドキュメント整合性チェック

**トリガー条件**:
- 大規模な変更後
- ドキュメント更新後
- 定期的な品質チェック

**ツール**: Read, Grep, Glob

**責務**:
- ドキュメント間の整合性確認
- リンク切れの検出
- 更新漏れの指摘
- テンプレート準拠の確認

**サブエージェント定義**:
```yaml
name: doc-analyzer
description: |
  Analyze documentation for consistency and completeness.
  Use after major changes or during quality reviews.
  Checks cross-references, broken links, and template compliance.
tools: Read, Grep, Glob
model: haiku
```

---

## 実装計画

### フェーズ1: 共通ドキュメントSkills

**目的**: 仕様駆動開発の基盤構築

**実装内容**:
1. `/.claude/skills/` ディレクトリ構造作成
2. prd-writer/SKILL.md 作成
3. design-doc-writer/SKILL.md 作成
4. adr-writer/SKILL.md 作成
5. plan-writer/SKILL.md 作成
6. troubleshooting-writer/SKILL.md 作成
7. rules-writer/SKILL.md 作成
8. skill-suggester/SKILL.md 作成

**フェーズ完了条件**:
- [ ] 全Skillが正しく認識される
- [ ] 各Skillがtemplate.mdを読み込んで出力できる
- [ ] webapp/infraの判断が正しく動作する

**E2E確認手順**:
1. 「新機能のPRDを作成して」でprd-writerが起動
2. 正しいtemplate.mdが参照される
3. 出力パスが適切

---

### フェーズ2: 共通サブエージェント

**目的**: 品質管理の自動化

**実装内容**:
1. `/.claude/agents/` ディレクトリ構造作成
2. code-reviewer.md 作成
3. test-runner.md 作成
4. doc-analyzer.md 作成

**フェーズ完了条件**:
- [ ] Task toolからサブエージェントが呼び出せる
- [ ] 各エージェントが適切なツールを使用できる

---

## ディレクトリ構造（完成形）

```
/.claude/
├── skills/
│   ├── prd-writer/
│   │   └── SKILL.md
│   ├── design-doc-writer/
│   │   └── SKILL.md
│   ├── adr-writer/
│   │   └── SKILL.md
│   ├── plan-writer/
│   │   └── SKILL.md
│   ├── troubleshooting-writer/
│   │   └── SKILL.md
│   ├── rules-writer/
│   │   └── SKILL.md
│   └── skill-suggester/
│       └── SKILL.md
├── agents/
│   ├── code-reviewer.md
│   ├── test-runner.md
│   └── doc-analyzer.md
└── settings.json
```

---

## テスト戦略

### Skill検証

| Skill | テストシナリオ | 期待結果 |
|-------|---------------|----------|
| prd-writer | 「webappのPRD作成」 | webapp/docs/prd/にtemplate.md準拠で出力 |
| prd-writer | 「infraのPRD作成」 | infra/docs/prd/にtemplate.md準拠で出力 |
| design-doc-writer | 「設計書作成」 | 適切なディレクトリに出力 |
| adr-writer | 「ADR作成」 | 正しい番号で採番される |

### サブエージェント検証

| エージェント | テストシナリオ | 期待結果 |
|-------------|---------------|----------|
| code-reviewer | コード変更後に呼び出し | レビューコメント生成 |
| test-runner | テスト実行依頼 | 結果分析と報告 |
| doc-analyzer | ドキュメント整合性チェック | 問題点リスト出力 |

---

## 参考資料

- `docs/skills_and_spec_driven_workflow.md`
- `docs/subagent_best_practices.md`
- [Agent Skills - Claude Code Docs](https://code.claude.com/docs/en/skills)

---

## 更新履歴

| 日付 | 版 | 変更内容 | 作成者 |
|------|-----|----------|--------|
| 2025-12-21 | 1.0 | 初版作成 | Claude |
