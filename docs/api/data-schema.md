# データスキーマ定義

## 1. ファイル一覧

| ファイル | 形式 | 用途 | 生成タイミング |
|----------|------|------|----------------|
| raw.jsonl | JSON Lines | 生ログ | 2分ごと |
| features.json | JSON | 集計済み特徴量 | 日報生成時 |
| report.json | JSON | LLM生成レポート | 日報生成時 |
| settings.json | JSON | 設定 | 初回/変更時 |
| audit.jsonl | JSON Lines | 監査ログ | 日報生成時 |

## 2. raw.jsonl

### 概要

常駐ロガーが2分間隔で出力する生ログ。

### スキーマ

```typescript
interface RawLogRecord {
  // 必須フィールド
  ts: string;            // ISO 8601 タイムスタンプ
  window_title: string | null;  // ウィンドウタイトル

  // Phase 2以降
  process_name?: string | null; // プロセス名

  // 抽出フィールド（オプション）
  keywords?: string[];   // 抽出キーワード
  urls?: string[];       // 抽出URL/ドメイン
  files?: string[];      // 抽出ファイルパス
  numbers?: string[];    // 抽出数値
}
```

### サンプル

```json
{"ts":"2025-01-15T09:00:00.000+09:00","window_title":"main.py - Visual Studio Code","process_name":"Code.exe","keywords":["Python","def","class"],"urls":[],"files":["main.py"],"numbers":[]}
{"ts":"2025-01-15T09:02:00.000+09:00","window_title":"main.py - Visual Studio Code","process_name":"Code.exe","keywords":["Python","import"],"urls":[],"files":["main.py"],"numbers":[]}
{"ts":"2025-01-15T09:04:00.000+09:00","window_title":"Stack Overflow - Google Chrome","process_name":"chrome.exe","keywords":["Python","error"],"urls":["stackoverflow.com"],"files":[],"numbers":[]}
```

### 制約

- 1行1レコード（JSON Lines形式）
- UTF-8エンコーディング（BOMなし）
- ファイル名: `YYYY-MM-DD.jsonl`
- 保存先: `%LOCALAPPDATA%/DailyReportBot/logs/`

## 3. features.json

### 概要

日報生成時に作成される集計済み特徴量。LLMへの入力として使用。

### スキーマ

```typescript
interface FeaturesJson {
  meta: {
    date: string;           // YYYY-MM-DD
    generated_at: string;   // ISO 8601
    capture_count: number;  // 総キャプチャ数
    first_capture: string;  // 最初のキャプチャ時刻
    last_capture: string;   // 最後のキャプチャ時刻
    total_duration_min: number; // 総記録時間（分）
  };

  time_blocks: TimeBlock[];
  app_summary: AppSummary[];
  global_keywords: GlobalKeywords;
}

interface TimeBlock {
  start: string;           // HH:MM
  end: string;             // HH:MM
  apps: Array<{
    name: string;
    percent: number;       // 0-100
  }>;
  top_keywords: string[];
  top_files: string[];

  // Phase 4以降
  insight_candidates?: InsightCandidate[];
}

interface AppSummary {
  name: string;            // 表示名
  process: string;         // プロセス名
  count: number;           // 観測回数
  duration_min: number;    // 推定使用時間（分）
  rank: "high" | "medium" | "low";
  top_keywords: string[];
  top_files?: string[];
  top_urls?: string[];
}

interface GlobalKeywords {
  top_keywords: string[];
  top_urls: string[];
  top_files: string[];
}

interface InsightCandidate {
  type: "error_resolution" | "documentation" | "learning";
  content: string;
  source?: string;
}
```

### サンプル

```json
{
  "meta": {
    "date": "2025-01-15",
    "generated_at": "2025-01-15T18:00:00+09:00",
    "capture_count": 240,
    "first_capture": "2025-01-15T09:00:00+09:00",
    "last_capture": "2025-01-15T17:58:00+09:00",
    "total_duration_min": 478
  },
  "time_blocks": [
    {
      "start": "09:00",
      "end": "09:30",
      "apps": [
        {"name": "Visual Studio Code", "percent": 80},
        {"name": "Google Chrome", "percent": 20}
      ],
      "top_keywords": ["Python", "Flask", "API"],
      "top_files": ["main.py", "routes.py"]
    }
  ],
  "app_summary": [
    {
      "name": "Visual Studio Code",
      "process": "Code.exe",
      "count": 120,
      "duration_min": 240,
      "rank": "high",
      "top_keywords": ["Python", "Flask", "import"],
      "top_files": ["main.py", "routes.py", "models.py"]
    }
  ],
  "global_keywords": {
    "top_keywords": ["Python", "Flask", "API", "documentation"],
    "top_urls": ["stackoverflow.com", "docs.python.org"],
    "top_files": ["main.py", "routes.py", "models.py"]
  }
}
```

## 4. report.json

### 概要

LLM要約後の日報データ。Notion出力に使用。

### スキーマ

```typescript
interface ReportJson {
  meta: {
    date: string;
    generated_at: string;
    llm_model: string;
    llm_success: boolean;
    llm_error?: string;    // エラー時のみ
  };

  // LLM生成フィールド
  main_tasks: MainTask[];
  insights: Insight[];
  work_summary: string;

  // 転記フィールド（features.jsonから）
  app_usage: AppUsage[];
  files: string[];
}

interface MainTask {
  title: string;
  description: string;
}

interface Insight {
  category: "技術" | "プロセス" | "その他";
  content: string;
}

interface AppUsage {
  name: string;
  duration_min: number;
  rank: "high" | "medium" | "low";
  purpose?: string;        // LLM生成
}
```

### サンプル

```json
{
  "meta": {
    "date": "2025-01-15",
    "generated_at": "2025-01-15T18:05:00+09:00",
    "llm_model": "gpt-4o-mini",
    "llm_success": true
  },
  "main_tasks": [
    {
      "title": "Flask APIエンドポイントの実装",
      "description": "ユーザー認証用のREST APIを3エンドポイント実装した"
    },
    {
      "title": "ドキュメント調査・レビュー",
      "description": "Stack OverflowとPython公式ドキュメントでFlaskの認証パターンを調査した"
    },
    {
      "title": "Slackでのコードレビュー対応",
      "description": "チームからのレビューコメントに対応し、修正を実施した"
    }
  ],
  "insights": [
    {
      "category": "技術",
      "content": "Flask-JWTの設定でトークン有効期限のデフォルト値に注意が必要"
    },
    {
      "category": "プロセス",
      "content": "認証周りは早めにレビュー依頼すると手戻りが減る"
    }
  ],
  "work_summary": "本日はFlask APIの認証機能実装に注力し、基本的なエンドポイントを完成させた。",
  "app_usage": [
    {
      "name": "Visual Studio Code",
      "duration_min": 240,
      "rank": "high",
      "purpose": "Python/Flask開発"
    },
    {
      "name": "Google Chrome",
      "duration_min": 160,
      "rank": "high",
      "purpose": "ドキュメント調査"
    },
    {
      "name": "Slack",
      "duration_min": 80,
      "rank": "medium",
      "purpose": "コードレビュー対応"
    }
  ],
  "files": ["main.py", "routes.py", "models.py", "auth.py"]
}
```

## 5. settings.json

### スキーマ

```typescript
interface Settings {
  logger: {
    sampling_interval_sec: number;  // デフォルト: 120
    ocr_enabled: boolean;
    ocr_language: string;           // デフォルト: "ja"
    excluded_processes: string[];
    excluded_window_titles: string[];
    log_retention_days: number;     // デフォルト: 30
  };

  aggregation: {
    exclude_recent_sec: number;     // デフォルト: 120
    time_block_min: number;         // デフォルト: 30
    top_keywords_count: number;     // デフォルト: 10
    min_captures_for_report: number; // デフォルト: 5
  };

  llm: {
    provider: "openai";
    model: string;                  // デフォルト: "gpt-4o-mini"
    max_tokens: number;             // デフォルト: 1000
    temperature: number;            // デフォルト: 0.3
    timeout_sec: number;            // デフォルト: 30
    fallback_on_error: boolean;     // デフォルト: true
  };

  notion: {
    database_id: string;
    page_title_format: string;      // デフォルト: "{date} 日報"
  };

  toast: {
    enabled: boolean;
    duration_success: number;       // デフォルト: 5
    duration_failure: number;       // デフォルト: 10
  };

  privacy: {
    mask_patterns: MaskPattern[];
  };
}

interface MaskPattern {
  pattern: string;     // 正規表現
  replacement: string; // 置換文字列
}
```

### サンプル

```json
{
  "logger": {
    "sampling_interval_sec": 120,
    "ocr_enabled": true,
    "ocr_language": "ja",
    "excluded_processes": ["LockApp.exe", "ScreenClipping.exe"],
    "excluded_window_titles": ["*password*", "*credential*"],
    "log_retention_days": 30
  },
  "aggregation": {
    "exclude_recent_sec": 120,
    "time_block_min": 30,
    "top_keywords_count": 10,
    "min_captures_for_report": 5
  },
  "llm": {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "max_tokens": 1000,
    "temperature": 0.3,
    "timeout_sec": 30,
    "fallback_on_error": true
  },
  "notion": {
    "database_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "page_title_format": "{date} 日報"
  },
  "toast": {
    "enabled": true,
    "duration_success": 5,
    "duration_failure": 10
  },
  "privacy": {
    "mask_patterns": [
      {"pattern": "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b", "replacement": "[EMAIL]"},
      {"pattern": "\\b\\d{3}-\\d{4}-\\d{4}\\b", "replacement": "[PHONE]"}
    ]
  }
}
```

## 6. audit.jsonl（Phase 5）

### スキーマ

```typescript
interface AuditRecord {
  ts: string;
  action: "generate_report" | "regenerate_report";
  date: string;
  input_file: string;
  capture_count: number;
  llm_used: boolean;
  llm_model?: string;
  notion_page_id?: string;
  notion_url?: string;
  success: boolean;
  error?: string;
  duration_ms: number;
  pc_name: string;
  user_name: string;
}
```

### サンプル

```json
{"ts":"2025-01-15T18:05:00+09:00","action":"generate_report","date":"2025-01-15","input_file":"2025-01-15.jsonl","capture_count":240,"llm_used":true,"llm_model":"gpt-4o-mini","notion_page_id":"abc123","notion_url":"https://notion.so/abc123","success":true,"duration_ms":5432,"pc_name":"DESKTOP-ABC","user_name":"okira"}
```
