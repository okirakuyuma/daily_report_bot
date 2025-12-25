# Phase 4: 高精度化仕様

## 概要

| 項目 | 内容 |
|------|------|
| 目標 | ファイル検出・メモ抽出精度向上 |
| 前提 | Phase 3完了 |
| 期間 | 1週間 |
| 優先度 | 中 |

## スコープ

### 含まれる機能

- ✅ エディタからのファイル名抽出強化
- ✅ Explorer操作の推定
- ✅ OCRからのキーワード抽出強化
- ✅ 知見候補の事前抽出
- ✅ アプリ別カスタム抽出ルール

### Phase 3からの変更点

| 項目 | Phase 3 | Phase 4 |
|------|---------|---------|
| ファイル検出 | 正規表現のみ | アプリ別ルール |
| キーワード抽出 | 汎用 | ドメイン特化 |
| 知見候補 | LLM任せ | 事前抽出 |

## 機能要件

### FR-15: エディタファイル抽出

| ID | 要件 |
|----|------|
| FR-15.1 | VSCodeのウィンドウタイトルからファイルパス抽出 |
| FR-15.2 | JetBrains IDEのタイトルからプロジェクト・ファイル抽出 |
| FR-15.3 | Vimのタイトルからファイル名抽出 |
| FR-15.4 | プロジェクトルートからの相対パスに正規化 |

### FR-16: Explorer操作推定

| ID | 要件 |
|----|------|
| FR-16.1 | Explorerのタイトルからフォルダパス抽出 |
| FR-16.2 | ファイル操作（コピー/移動/削除）の推定 |
| FR-16.3 | 操作対象ファイルの記録 |

### FR-17: キーワード抽出強化

| ID | 要件 |
|----|------|
| FR-17.1 | 技術用語辞書によるマッチング |
| FR-17.2 | プロジェクト固有用語の学習 |
| FR-17.3 | 出現頻度による重要度スコアリング |

### FR-18: 知見候補抽出

| ID | 要件 |
|----|------|
| FR-18.1 | エラーメッセージパターンの検出 |
| FR-18.2 | ドキュメントURL/Stack Overflowアクセスの検出 |
| FR-18.3 | 知見候補をtime_blocksに付与 |

## アプリ別抽出ルール

### VSCode

```python
# ウィンドウタイトル例: "main.py - project_name - Visual Studio Code"
VSCODE_PATTERN = r"^(.+?) - (.+?) - Visual Studio Code$"
# グループ1: ファイル名, グループ2: プロジェクト名
```

### JetBrains

```python
# ウィンドウタイトル例: "project_name – src/main.py [project_name]"
JETBRAINS_PATTERN = r"^(.+?) – (.+?) \[.+\]$"
```

### Chrome/Edge

```python
# ウィンドウタイトル例: "Python Tutorial - Google Chrome"
BROWSER_PATTERN = r"^(.+?) - (Google Chrome|Microsoft Edge)$"
# ドメイン抽出はOCRテキストから
```

### Explorer

```python
# ウィンドウタイトル例: "Documents" or "C:\Users\name\Documents"
EXPLORER_PATTERN = r"^([A-Z]:\\.*|.+)$"
```

## データ仕様

### features.json（Phase 4版）

```json
{
  "time_blocks": [
    {
      "start": "09:00",
      "end": "09:30",
      "apps": [...],
      "files_worked": [
        {
          "path": "src/main.py",
          "app": "VSCode",
          "duration_min": 20
        }
      ],
      "insight_candidates": [
        {
          "type": "error_resolution",
          "content": "ModuleNotFoundError解決",
          "source": "stackoverflow.com"
        }
      ]
    }
  ]
}
```

## 受け入れ基準

### AC-10: ファイル抽出

- [ ] VSCodeからのファイル名抽出成功率 90%以上
- [ ] JetBrainsからのファイル名抽出成功率 80%以上
- [ ] プロジェクト相対パスに正規化

### AC-11: キーワード抽出

- [ ] 技術用語の検出率向上
- [ ] ノイズ（一般語）の除去
- [ ] 重要度スコア付き

### AC-12: 知見候補

- [ ] エラー解決パターンの検出
- [ ] ドキュメント参照の記録
- [ ] LLM入力に知見候補が含まれる

## 実装タスク

| タスク | 見積 |
|--------|------|
| アプリ別抽出ルール実装 | 6h |
| 技術用語辞書作成 | 4h |
| 知見候補抽出ロジック | 4h |
| features.json拡張 | 2h |
| LLMプロンプト更新 | 2h |
| テスト | 4h |
