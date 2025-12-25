# Claude Code Skills & 仕様駆動開発ワークフロー完全ガイド

## Skills活用 & プロアクティブな改善提案の実現

---

## 目次

1. [Agent Skillsとは](https://claude.ai/chat/79eaab5b-dd20-4349-b0dc-a8698f10e836#1-agent-skills%E3%81%A8%E3%81%AF)
2. [Skillsの主なメリット](https://claude.ai/chat/79eaab5b-dd20-4349-b0dc-a8698f10e836#2-skills%E3%81%AE%E4%B8%BB%E3%81%AA%E3%83%A1%E3%83%AA%E3%83%83%E3%83%88)
3. [Skillsの作成方法](https://claude.ai/chat/79eaab5b-dd20-4349-b0dc-a8698f10e836#3-skills%E3%81%AE%E4%BD%9C%E6%88%90%E6%96%B9%E6%B3%95)
4. [SKILL.mdの書き方](https://claude.ai/chat/79eaab5b-dd20-4349-b0dc-a8698f10e836#4-skillmd%E3%81%AE%E6%9B%B8%E3%81%8D%E6%96%B9)
5. [Skillsのベストプラクティス](https://claude.ai/chat/79eaab5b-dd20-4349-b0dc-a8698f10e836#5-skills%E3%81%AE%E3%83%99%E3%82%B9%E3%83%88%E3%83%97%E3%83%A9%E3%82%AF%E3%83%86%E3%82%A3%E3%82%B9)
6. [仕様駆動開発ワークフローへの統合](https://claude.ai/chat/79eaab5b-dd20-4349-b0dc-a8698f10e836#6-%E4%BB%95%E6%A7%98%E9%A7%86%E5%8B%95%E9%96%8B%E7%99%BA%E3%83%AF%E3%83%BC%E3%82%AF%E3%83%95%E3%83%AD%E3%83%BC%E3%81%B8%E3%81%AE%E7%B5%B1%E5%90%88)
7. [プロアクティブな提案を実現するCLAUDE.md設定](https://claude.ai/chat/79eaab5b-dd20-4349-b0dc-a8698f10e836#7-%E3%83%97%E3%83%AD%E3%82%A2%E3%82%AF%E3%83%86%E3%82%A3%E3%83%96%E3%81%AA%E6%8F%90%E6%A1%88%E3%82%92%E5%AE%9F%E7%8F%BE%E3%81%99%E3%82%8Bclaudemd%E8%A8%AD%E5%AE%9A)
8. [Skills vs サブエージェント vs MCP](https://claude.ai/chat/79eaab5b-dd20-4349-b0dc-a8698f10e836#8-skills-vs-%E3%82%B5%E3%83%96%E3%82%A8%E3%83%BC%E3%82%B8%E3%82%A7%E3%83%B3%E3%83%88-vs-mcp)
9. [実践的なSkills例](https://claude.ai/chat/79eaab5b-dd20-4349-b0dc-a8698f10e836#9-%E5%AE%9F%E8%B7%B5%E7%9A%84%E3%81%AAskills%E4%BE%8B)
10. [トラブルシューティング](https://claude.ai/chat/79eaab5b-dd20-4349-b0dc-a8698f10e836#10-%E3%83%88%E3%83%A9%E3%83%96%E3%83%AB%E3%82%B7%E3%83%A5%E3%83%BC%E3%83%86%E3%82%A3%E3%83%B3%E3%82%B0)
11. [参考リソース](https://claude.ai/chat/79eaab5b-dd20-4349-b0dc-a8698f10e836#11-%E5%8F%82%E8%80%83%E3%83%AA%E3%82%BD%E3%83%BC%E3%82%B9)

---

## 1. Agent Skillsとは

Agent Skillsは、Claude Codeの機能を拡張するためのモジュール式の能力パッケージです。Skillsフォルダには、指示書（SKILL.md）、スクリプト、リソースが含まれ、Claudeが必要に応じて読み込みます。

### Skillsの動作原理

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Code                              │
│                                                             │
│  ユーザーリクエスト                                          │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────┐                                        │
│  │ Skills スキャン  │ ← 利用可能なSkillsのメタデータを確認   │
│  └────────┬────────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │ マッチング判定   │ ← descriptionに基づいて関連性を判断   │
│  └────────┬────────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │ Skill読み込み    │ ← 必要なファイルのみロード            │
│  │ (Progressive     │   （プログレッシブディスクロージャー）│
│  │  Disclosure)     │                                       │
│  └────────┬────────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │ タスク実行       │                                       │
│  └─────────────────┘                                        │
└─────────────────────────────────────────────────────────────┘
```

### 重要な特徴

| 特徴                                       | 説明                                                                      |
| ------------------------------------------ | ------------------------------------------------------------------------- |
| **モデル起動型**                     | Claudeが自動的に判断してSkillを使用（ユーザーが明示的に呼び出す必要なし） |
| **プログレッシブディスクロージャー** | 必要なファイルのみを段階的に読み込み、コンテキストを効率的に管理          |
| **合成可能**                         | 複数のSkillsを組み合わせて使用可能                                        |
| **ポータブル**                       | Claude.ai、Claude Code、APIで同じ形式で動作                               |

---

## 2. Skillsの主なメリット

### 2.1 特化タスクのパフォーマンス向上

Skillsは、ドキュメント作成、データ分析、ドメイン固有の作業など、Claudeの汎用知識を補完する専門的な能力を提供します。

### 2.2 組織的知識の蓄積

会社のワークフロー、ベストプラクティス、制度的な知識をパッケージ化し、チーム全体で一貫して使用できます。

### 2.3 簡単なカスタマイズ

シンプルなSkillsはMarkdownで指示を書くだけで作成可能。コーディング不要です。高度な機能が必要な場合は実行可能なスクリプトを添付できます。

### 2.4 組織一元管理

TeamおよびEnterpriseプランでは、オーナーが組織全体にSkillsをプロビジョニングでき、各ユーザーの個別設定なしで一貫したワークフローを確保できます。

---

## 3. Skillsの作成方法

### 3.1 保存場所

| 種類                         | パス                                   | スコープ                           |
| ---------------------------- | -------------------------------------- | ---------------------------------- |
| **パーソナルSkills**   | `~/.claude/skills/skill-name/`       | 全プロジェクトで利用可能           |
| **プロジェクトSkills** | `.claude/skills/skill-name/`         | 現在のプロジェクトのみ             |
| **プラグインSkills**   | プラグイン内の `skills/`ディレクトリ | プラグインインストール時に利用可能 |

### 3.2 作成手順

```bash
# パーソナルSkillの作成
mkdir -p ~/.claude/skills/my-skill-name

# プロジェクトSkillの作成
mkdir -p .claude/skills/my-skill-name
```

### 3.3 ディレクトリ構造

```
my-skill/
├── SKILL.md           # 必須：メインの指示書
├── reference.md       # オプション：詳細ドキュメント
├── examples.md        # オプション：使用例
├── scripts/
│   └── helper.py      # オプション：ヘルパースクリプト
└── templates/
    └── template.txt   # オプション：テンプレート
```

---

## 4. SKILL.mdの書き方

### 4.1 基本構造

```markdown
---
name: your-skill-name
description: Brief description of what this Skill does and when to use it
allowed-tools: Read, Write, Edit, Bash  # オプション：許可するツール
model: sonnet  # オプション：使用するモデル
---

# Your Skill Name

## Instructions
Provide clear, step-by-step guidance for Claude.

## Examples
Show concrete examples of using this Skill.

## Guidelines
- Guideline 1
- Guideline 2
```

### 4.2 フロントマターフィールド

| フィールド        | 必須 | 説明                        | 制限                                      |
| ----------------- | :--: | --------------------------- | ----------------------------------------- |
| `name`          |  ✓  | 一意の識別子                | 小文字、数字、ハイフンのみ。最大64文字    |
| `description`   |  ✓  | Skillの説明と使用タイミング | 最大1024文字                              |
| `allowed-tools` |      | 許可するツールのリスト      | 省略時は通常の権限モデルに従う            |
| `model`         |      | 使用するモデル              | `sonnet`,`opus`,`haiku`,`inherit` |

### 4.3 descriptionの書き方（最重要）

`description`はClaudeがSkillを発見するための最も重要なフィールドです。

 **悪い例** :

```yaml
description: Helps with documents
```

 **良い例** :

```yaml
description: |
  Extract text and tables from PDF files, fill forms, merge documents.
  Use when working with PDF files or when the user mentions PDFs, 
  forms, or document extraction.
```

 **含めるべき要素** :

* Skillが何をするか（What）
* いつ使うべきか（When）
* ユーザーが言及しそうなキーワード

### 4.4 allowed-toolsによるツール制限

読み取り専用のSkillなど、ツールを制限したい場合：

```markdown
---
name: safe-code-analyzer
description: Analyze code for potential issues without making changes. Use when reviewing code quality.
allowed-tools: Read, Grep, Glob
---

# Safe Code Analyzer

This Skill provides read-only code analysis.

## Instructions
1. Use Read to view file contents
2. Use Grep to search for patterns
3. Use Glob to find files
4. Report findings without making changes
```

---

## 5. Skillsのベストプラクティス

### 5.1 Skillを単一目的に集中させる

 **良い例（集中）** :

* 「PDF form filling」
* 「Excel data analysis」
* 「Git commit messages」

 **悪い例（広すぎる）** :

* 「Document processing」（複数のSkillに分割すべき）
* 「Data tools」（データ種別や操作ごとに分割すべき）

### 5.2 明確なトリガーを含める

```yaml
# 良い例
description: |
  Analyze Excel spreadsheets, create pivot tables, and generate charts. 
  Use when working with Excel files, spreadsheets, or analyzing tabular data 
  in .xlsx format.

# 悪い例
description: For files
```

### 5.3 バージョン履歴を記録

```markdown
# My Skill

## Version History
- v2.0.0 (2025-10-01): Breaking changes to API
- v1.1.0 (2025-09-15): Added new features
- v1.0.0 (2025-09-01): Initial release
```

### 5.4 チームでテスト

* Skillが期待通りに起動するか
* 指示が明確か
* 欠けている例やエッジケースはないか

---

## 6. 仕様駆動開発ワークフローへの統合

あなたのプロジェクト構造に合わせたSkillsを設計します。

### 6.1 現在のドキュメント構造

```
docs/
├── adr/              # Architecture Decision Records
├── design/           # 設計ドキュメント
├── plan/             # 計画・プランニング
├── prd/              # Product Requirements Document
├── rules/            # ルール・規約
└── troubleshooting/  # トラブルシューティング
```

### 6.2 ワークフロー対応Skills

#### prd-writer.md（PRD作成スキル）

```markdown
---
name: prd-writer
description: |
  Create and update Product Requirements Documents (PRD).
  Use when user mentions PRD, requirements, feature specification,
  or asks to document a new feature.
  Output location: docs/prd/
allowed-tools: Read, Write, Edit, Glob, Grep
---

# PRD Writer Skill

あなたはPRD（製品要件定義書）の専門家です。

## 出力場所
- 新規PRD: `docs/prd/{feature-name}.md`

## PRDテンプレート

```markdown
# {機能名} PRD

## 概要
{機能の概要を1-2文で}

## 背景と課題
{なぜこの機能が必要か}

## 目標
{この機能で達成したいこと}

## ユーザーストーリー
- As a {user}, I want to {action}, so that {benefit}

## 機能要件
### 必須要件 (Must Have)
- [ ] 要件1
- [ ] 要件2

### 推奨要件 (Should Have)
- [ ] 要件1

### あれば良い要件 (Nice to Have)
- [ ] 要件1

## 非機能要件
- パフォーマンス:
- セキュリティ:
- アクセシビリティ:

## 成功指標
- KPI 1:
- KPI 2:

## タイムライン
- 開始日:
- 完了予定日:

## 関連ドキュメント
- 設計: docs/design/
- ADR: docs/adr/
```

## ガイドライン

1. 既存のPRDを確認し、一貫したフォーマットを使用
2. 曖昧な要件は明確化のための質問を生成
3. ステークホルダーを特定

```

#### design-doc-writer.md（設計書作成スキル）

```markdown
---
name: design-doc-writer
description: |
  Create and update technical design documents.
  Use when user mentions design doc, technical design, architecture design,
  system design, or API design.
  Output location: docs/design/
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Design Document Writer Skill

あなたは技術設計書の専門家です。

## 出力場所
- 新規設計書: `docs/design/{feature-name}.md`

## 設計書テンプレート

```markdown
# {機能名} 設計書

## ステータス
- [ ] Draft
- [ ] Review
- [ ] Approved
- [ ] Implemented

## 関連PRD
- docs/prd/{related-prd}.md

## 概要
{技術的な概要}

## 背景
{技術的な背景と制約}

## 設計目標
1. 目標1
2. 目標2

## 詳細設計

### アーキテクチャ
{アーキテクチャ図やコンポーネント構成}

### データモデル
{データ構造、スキーマ}

### API設計
{エンドポイント、リクエスト/レスポンス}

### シーケンス図
{主要フローのシーケンス}

## 代替案
### 検討した代替案
1. 代替案A
   - メリット:
   - デメリット:
   - 不採用理由:

## セキュリティ考慮事項
- 認証:
- 認可:
- データ保護:

## パフォーマンス考慮事項
- 想定負荷:
- ボトルネック:
- 最適化戦略:

## テスト戦略
- ユニットテスト:
- 統合テスト:
- E2Eテスト:

## 移行計画
{既存システムからの移行手順}

## 関連ADR
- docs/adr/ADR-{number}.md
```

## 作成プロセス

1. 関連PRDを確認
2. 既存の設計書パターンを確認
3. 設計書をドラフト
4. 技術的な代替案を検討
5. ADRが必要な場合は提案

```

#### adr-writer.md（ADR作成スキル）

```markdown
---
name: adr-writer
description: |
  Create Architecture Decision Records (ADR).
  Use when user mentions ADR, architecture decision, technical decision,
  or when a significant technical choice needs to be documented.
  Output location: docs/adr/
allowed-tools: Read, Write, Edit, Glob, Grep
---

# ADR Writer Skill

あなたはADR（アーキテクチャ決定記録）の専門家です。

## 出力場所
- 新規ADR: `docs/adr/ADR-{number}-{title}.md`

## ADR番号の決定
1. `docs/adr/`ディレクトリを確認
2. 最新のADR番号を取得
3. +1 した番号を使用

## ADRテンプレート

```markdown
# ADR-{number}: {決定タイトル}

## ステータス
Proposed | Accepted | Deprecated | Superseded by ADR-XXX

## 日付
{YYYY-MM-DD}

## コンテキスト
{この決定が必要になった背景、問題、制約}

## 決定
{何を決定したか}

## 検討した選択肢

### 選択肢1: {名前}
- **説明**: 
- **メリット**:
  - 
- **デメリット**:
  - 

### 選択肢2: {名前}
- **説明**:
- **メリット**:
  - 
- **デメリット**:
  - 

## 結果
{この決定の結果、何が良くなり、何に注意が必要か}

## 関連ドキュメント
- 設計書: docs/design/
- PRD: docs/prd/
```

## ADR作成のトリガー

以下の場合にADRを提案:

* 新しいライブラリ/フレームワークの採用
* アーキテクチャパターンの変更
* 破壊的変更を伴う決定
* 複数の選択肢から重要な選択をした場合

```

#### plan-writer.md（計画作成スキル）

```markdown
---
name: plan-writer
description: |
  Create implementation plans and task breakdowns.
  Use when user mentions plan, implementation plan, task breakdown,
  sprint planning, or milestone planning.
  Output location: docs/plan/
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Plan Writer Skill

あなたは実装計画の専門家です。

## 出力場所
- 新規計画: `docs/plan/{feature-name}-plan.md`

## 計画テンプレート

```markdown
# {機能名} 実装計画

## 概要
{計画の概要}

## 関連ドキュメント
- PRD: docs/prd/{prd-name}.md
- 設計書: docs/design/{design-name}.md

## マイルストーン

### Phase 1: {フェーズ名}
- **期間**: {開始日} - {終了日}
- **目標**: {このフェーズの目標}

#### タスク
- [ ] タスク1 (担当: @name, 見積: Xh)
- [ ] タスク2 (担当: @name, 見積: Xh)

#### 完了条件
- 条件1
- 条件2

### Phase 2: {フェーズ名}
...

## 依存関係
- タスクAはタスクBの完了後に開始
- 外部依存: {サービス名}

## リスクと軽減策
| リスク | 影響度 | 発生確率 | 軽減策 |
|--------|--------|----------|--------|
| リスク1 | 高 | 中 | 軽減策1 |

## リソース
- 開発者: X名
- デザイナー: X名
- 期間: X週間

## 進捗トラッキング
- 週次レビュー: 毎週{曜日}
- ステータス更新: {ツール名}
```

```

#### troubleshooting-writer.md（トラブルシューティング作成スキル）

```markdown
---
name: troubleshooting-writer
description: |
  Create and update troubleshooting guides.
  Use when user encounters an error, bug, or issue that should be documented,
  or when documenting known issues and their solutions.
  Output location: docs/troubleshooting/
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Troubleshooting Writer Skill

あなたはトラブルシューティングドキュメントの専門家です。

## 出力場所
- 新規ガイド: `docs/troubleshooting/{issue-category}.md`

## トラブルシューティングテンプレート

```markdown
# {カテゴリ} トラブルシューティング

## 目次
- [問題1: {問題名}](#問題1-問題名)
- [問題2: {問題名}](#問題2-問題名)

---

## 問題1: {問題名}

### 症状
{ユーザーが見る症状、エラーメッセージ}

```

エラーメッセージをここに記載

```

### 原因
{この問題が発生する原因}

### 解決方法

#### 方法1: {方法名}
1. ステップ1
2. ステップ2
3. ステップ3

```bash
# 必要なコマンド
command example
```

#### 方法2:（方法1で解決しない場合）

1. ステップ1
2. ステップ2

### 予防策

{この問題を防ぐためのベストプラクティス}

### 関連リソース

* [関連ドキュメント](https://claude.ai/chat/link)
* [GitHub Issue](https://claude.ai/chat/link)

---

```

## 作成ルール
1. エラーメッセージは正確にコピー
2. 解決方法は検証済みのものを記載
3. 複数の解決方法がある場合は優先度順に記載
4. 関連するissueやPRをリンク
```

#### rules-writer.md（ルール作成スキル）

```markdown
---
name: rules-writer
description: |
  Create and update project rules and conventions.
  Use when user mentions coding standards, conventions, rules,
  guidelines, or best practices that should be documented.
  Output location: docs/rules/
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Rules Writer Skill

あなたはプロジェクトルール・規約の専門家です。

## 出力場所
- 新規ルール: `docs/rules/{category}.md`

## ルールテンプレート

```markdown
# {カテゴリ} ルール

## 目的
{このルールセットの目的}

## 適用範囲
{このルールが適用されるコード・状況}

## ルール一覧

### 必須ルール (MUST)
これらのルールは必ず従うこと。CIで強制される。

#### RULE-001: {ルール名}
- **説明**: {ルールの詳細}
- **理由**: {なぜこのルールが必要か}
- **良い例**:
  ```typescript
  // Good
```

* **悪い例** :

```typescript
  // Bad
```

### 推奨ルール (SHOULD)

これらのルールは強く推奨される。

#### RULE-002:

...

### 禁止事項 (MUST NOT)

これらは絶対に行わないこと。

#### RULE-003:

...

## 例外

{ルールの例外が認められるケース}

## 関連ドキュメント

* ADR: docs/adr/
* 設計書: docs/design/

```

```

### 6.3 Skillsディレクトリ構造（完成形）

```
.claude/
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
│   └── skill-suggester/           # 新規Skill提案用
│       └── SKILL.md
├── agents/
│   ├── code-reviewer.md
│   ├── test-runner.md
│   └── ...
└── commands/
    └── ...
```

---

## 7. プロアクティブな提案を実現するCLAUDE.md設定

Claudeが作業後に積極的にSkillsやサブエージェントの追加を提案するようにするための設定です。

### 7.1 CLAUDE.md テンプレート

```markdown
# プロジェクト名

## プロジェクト概要
{プロジェクトの概要を1-2文で}

## ディレクトリ構成
```

docs/
├── adr/              # Architecture Decision Records
├── design/           # 設計ドキュメント
├── plan/             # 計画・プランニング
├── prd/              # Product Requirements Document
├── rules/            # ルール・規約
└── troubleshooting/  # トラブルシューティング

```

## 開発ワークフロー

### 仕様駆動開発フロー
1. **PRD作成** → `docs/prd/` に要件定義
2. **設計** → `docs/design/` に技術設計
3. **計画** → `docs/plan/` に実装計画
4. **ADR** → 重要な決定は `docs/adr/` に記録
5. **実装** → 設計に基づいて実装
6. **ドキュメント更新** → 問題は `docs/troubleshooting/` に記録

---

## 改善提案ルール (IMPORTANT)

<proactive_improvement_suggestions>

### Claudeは以下の場合に改善提案を行うこと:

#### 1. 新しいSkillの提案
作業完了後、以下のパターンを検出した場合に新しいSkillを提案:
- 同じ種類のドキュメントを複数回作成した場合
- 特定のワークフローが繰り返された場合
- ユーザーが「毎回同じことをしている」と感じられる作業を検出した場合

**提案フォーマット**:
```

💡 Skill提案: {skill-name}
━━━━━━━━━━━━━━━━━━━━━━━━
検出パターン: {繰り返された作業の説明}
提案理由: {なぜSkill化すると良いか}
推定効果: {どのくらい効率化できるか}

作成しますか？ [Y/n]

```

#### 2. 新しいサブエージェントの提案
以下の場合に新しいサブエージェントを提案:
- 特定のドメインで複雑なタスクが繰り返される場合
- 複数ステップの作業で、独立したコンテキストが有効な場合
- 専門的な知識が必要なタスクが頻発する場合

**提案フォーマット**:
```

🤖 サブエージェント提案: {agent-name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
検出パターン: {繰り返された複雑なタスク}
提案理由: {なぜサブエージェント化すると良いか}
推奨ツール: {Read, Write, Edit, etc.}

作成しますか？ [Y/n]

```

#### 3. ドキュメント更新の提案
以下の場合にドキュメント更新を提案:
- 新しいエラーに遭遇し解決した場合 → `docs/troubleshooting/`
- 重要な技術的決定をした場合 → `docs/adr/`
- 新しいルールや規約を発見した場合 → `docs/rules/`

**提案フォーマット**:
```

📝 ドキュメント更新提案
━━━━━━━━━━━━━━━━━━━━
種類: {troubleshooting | adr | rules}
内容: {追加すべき内容の要約}
場所: {ファイルパス}

追加しますか？ [Y/n]

```

#### 4. 既存Skill/サブエージェントの改善提案
使用中に問題や改善点を発見した場合:

**提案フォーマット**:
```

⚡ 改善提案: {skill/agent name}
━━━━━━━━━━━━━━━━━━━━━━━━
問題: {発見した問題}
改善案: {具体的な改善内容}

適用しますか？ [Y/n]

```

</proactive_improvement_suggestions>

---

## タスク完了時のチェックリスト

各タスク完了時に以下を確認:
1. [ ] 新しいパターンの繰り返しを検出したか？ → Skill提案を検討
2. [ ] 複雑な専門タスクを実行したか？ → サブエージェント提案を検討
3. [ ] 新しい問題を解決したか？ → トラブルシューティング追加を検討
4. [ ] 重要な決定をしたか？ → ADR追加を検討
5. [ ] 新しいルールを発見したか？ → ルール追加を検討

---

## コマンド

### ビルド
```bash
pnpm build
```

### テスト

```bash
pnpm test
```

### Lint

```bash
pnpm lint
```

---

## 利用可能なSkills

* `prd-writer`: PRD作成
* `design-doc-writer`: 設計書作成
* `adr-writer`: ADR作成
* `plan-writer`: 計画作成
* `troubleshooting-writer`: トラブルシューティング作成
* `rules-writer`: ルール作成

## 利用可能なサブエージェント

* `code-reviewer`: コードレビュー
* `test-runner`: テスト実行
* {追加されたエージェントをここにリスト}

```

### 7.2 skill-suggester Skill（Skill提案専用）

```markdown
---
name: skill-suggester
description: |
  Analyze work patterns and suggest new Skills or subagents.
  Use PROACTIVELY after completing tasks to identify automation opportunities.
  MUST be invoked at the end of complex tasks.
allowed-tools: Read, Glob, Grep
---

# Skill Suggester

あなたは作業パターンを分析し、新しいSkillsやサブエージェントを提案する専門家です。

## 分析対象

### Skill候補の検出パターン
1. **繰り返しドキュメント作成**: 同じ構造のドキュメントを3回以上作成
2. **定型コード生成**: 同じパターンのコードを繰り返し生成
3. **ワークフロー繰り返し**: 同じ手順を複数回実行

### サブエージェント候補の検出パターン
1. **複雑な分析タスク**: 複数ファイルの読み取りと分析が必要
2. **専門知識タスク**: 特定ドメインの深い知識が必要
3. **マルチステップタスク**: 5ステップ以上の連続作業

## 提案プロセス

1. 完了したタスクを分析
2. 繰り返しパターンを検出
3. 既存のSkills/サブエージェントでカバーされているか確認
4. カバーされていない場合、新規作成を提案

## 提案テンプレート

### Skill提案
```

💡 Skill提案: {skill-name}
━━━━━━━━━━━━━━━━━━━━━━━━
検出パターン: {具体的な繰り返しパターン}
提案理由: {効率化の理由}
推定効果:

* 時間削減: 約{X}分/回
* エラー削減: {具体的な効果}

提案するSKILL.md:

```yaml
name: {skill-name}
description: {description}
```

作成を希望しますか？

```

### サブエージェント提案
```

🤖 サブエージェント提案: {agent-name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
検出パターン: {複雑なタスクの説明}
提案理由: {なぜコンテキスト分離が有効か}
推奨ツール: {ツールリスト}
推奨モデル: {sonnet | opus | haiku}

提案する定義:

```yaml
name: {agent-name}
description: {description}
tools: {tools}
```

作成を希望しますか？

```

```

### 7.3 Hookによる自動提案トリガー

`.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "command": ".claude/hooks/suggest-improvements.sh",
        "timeout": 5000
      }
    ]
  }
}
```

`.claude/hooks/suggest-improvements.sh`:

```bash
#!/bin/bash

# タスク完了時に改善提案を促す

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 タスク完了 - 改善機会の確認"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "以下の観点で改善提案を検討してください:"
echo ""
echo "  💡 繰り返しパターン → 新しいSkillの候補?"
echo "  🤖 複雑な専門タスク → 新しいサブエージェントの候補?"
echo "  📝 新しい知見 → ドキュメント更新の候補?"
echo ""
echo "提案がある場合は報告してください。"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
```

---

## 8. Skills vs サブエージェント vs MCP

### 8.1 比較表

| 特徴                   | Skills                         | サブエージェント                 | MCP                         |
| ---------------------- | ------------------------------ | -------------------------------- | --------------------------- |
| **目的**         | 手順的知識の提供               | 独立したコンテキストでの作業委譲 | 外部サービス/データへの接続 |
| **コンテキスト** | メインコンテキストに追加       | 独自のコンテキストウィンドウ     | N/A（ツール提供）           |
| **起動方法**     | モデルが自動判断               | モデルが委譲判断/明示的呼び出し  | ツール呼び出し              |
| **並列処理**     | 不可                           | 可能                             | N/A                         |
| **適した用途**   | ドキュメント作成、ワークフロー | 複雑な分析、専門タスク           | API連携、データアクセス     |

### 8.2 使い分けガイド

```
┌─────────────────────────────────────────────────────────────┐
│                    どれを使うべき?                          │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │ 外部サービスへの      │
              │ アクセスが必要?       │
              └───────────┬───────────┘
                    │           │
                   Yes          No
                    │           │
                    ▼           ▼
              ┌─────────┐  ┌───────────────────────┐
              │   MCP   │  │ 独立したコンテキストが  │
              └─────────┘  │ 有効?                  │
                           └───────────┬───────────┘
                                 │           │
                                Yes          No
                                 │           │
                                 ▼           ▼
                           ┌──────────┐  ┌─────────┐
                           │サブ      │  │ Skills  │
                           │エージェント│  └─────────┘
                           └──────────┘
```

### 8.3 組み合わせ例

```markdown
# 機能実装ワークフロー

1. PRD作成 (Skill: prd-writer)
   ↓
2. 設計書作成 (Skill: design-doc-writer)
   ↓
3. ADR作成 (Skill: adr-writer) 
   ↓
4. コード実装 (サブエージェント: implementer)
   ↓
5. コードレビュー (サブエージェント: code-reviewer)
   ↓
6. GitHub PR作成 (MCP: GitHub)
   ↓
7. 問題があれば記録 (Skill: troubleshooting-writer)
```

---

## 9. 実践的なSkills例

### 9.1 Anthropic公式Skillsリポジトリ

GitHub: https://github.com/anthropics/skills

| Skill                       | 説明                                             |
| --------------------------- | ------------------------------------------------ |
| **algorithmic-art**   | p5.jsを使った生成アート                          |
| **artifacts-builder** | React/Tailwind/shadcn/uiでのアーティファクト構築 |
| **brand-guidelines**  | ブランドガイドラインの適用                       |
| **canvas-design**     | ビジュアルアートデザイン                         |
| **internal-comms**    | 社内コミュニケーション文書                       |
| **mcp-builder**       | MCPサーバーの構築ガイド                          |
| **skill-creator**     | Skill作成のガイド                                |
| **slack-gif-creator** | Slack用GIF作成                                   |
| **theme-factory**     | テーマ適用                                       |
| **webapp-testing**    | Playwrightでのテスト                             |

### 9.2 ドキュメントSkills

| Skill          | 説明                 |
| -------------- | -------------------- |
| **docx** | Word文書の作成・編集 |
| **pdf**  | PDF操作              |
| **pptx** | PowerPoint作成・編集 |
| **xlsx** | Excel操作            |

### 9.3 Claude Codeへのインストール

```bash
# プラグインマーケットプレイスを追加
/plugin marketplace add anthropics/skills

# ドキュメントSkillsをインストール
/plugin install document-skills@anthropic-agent-skills

# サンプルSkillsをインストール
/plugin install example-skills@anthropic-agent-skills
```

---

## 10. トラブルシューティング

### 10.1 Skillが使用されない

 **原因と解決策** :

| 原因               | 確認方法                | 解決策                                 |
| ------------------ | ----------------------- | -------------------------------------- |
| descriptionが曖昧  | 内容を確認              | 具体的なトリガーワードを追加           |
| パスが間違っている | `ls .claude/skills/`  | 正しいパスに配置                       |
| YAMLが無効         | `head -n 15 SKILL.md` | 構文エラーを修正                       |
| ファイル名が違う   | `ls -la`              | `SKILL.md`（大文字）であることを確認 |

### 10.2 複数Skillsの競合

 **解決策** : descriptionで明確に差別化

```yaml
# 悪い例（競合しやすい）
# Skill 1
description: For data analysis
# Skill 2
description: For analyzing data

# 良い例（明確に差別化）
# Skill 1
description: |
  Analyze sales data in Excel files and CRM exports. 
  Use for sales reports, pipeline analysis, and revenue tracking.
# Skill 2
description: |
  Analyze log files and system metrics data. 
  Use for performance monitoring, debugging, and system diagnostics.
```

### 10.3 Skillのエラー

```bash
# デバッグモードで起動
claude --debug

# SKILL.mdの検証
cat .claude/skills/my-skill/SKILL.md | head -n 15

# 実行権限の確認（スクリプトがある場合）
chmod +x .claude/skills/my-skill/scripts/*.py
```

---

## 11. 参考リソース

### 公式ドキュメント

* [Agent Skills - Claude Code Docs](https://code.claude.com/docs/en/skills)
* [What are Skills? - Claude Help Center](https://support.claude.com/en/articles/12512176-what-are-skills)
* [Using Skills in Claude](https://support.claude.com/en/articles/12512180-using-skills-in-claude)
* [Creating Custom Skills](https://support.claude.com/en/articles/12512198-creating-custom-skills)

### 技術ブログ

* [Introducing Agent Skills](https://claude.com/blog/skills)
* [Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)

### コミュニティリソース

* [Anthropic Skills Repository](https://github.com/anthropics/skills)
* [Agent Skills Specification](https://agentskills.io/)

### CLAUDE.md ベストプラクティス

* [Using CLAUDE.MD files](https://claude.com/blog/using-claude-md-files)
* [Writing a good CLAUDE.md](https://www.humanlayer.dev/blog/writing-a-good-claude-md)

---

## 変更履歴

| 日付       | 変更内容 |
| ---------- | -------- |
| 2025-12-21 | 初版作成 |

---

*このドキュメントは、公式ドキュメント、Anthropicのベストプラクティス、コミュニティの知見を統合して作成されました。*
