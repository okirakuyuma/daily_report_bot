"""Domain層の使用例.

CaptureRecordとFeaturesモデルの基本的な使い方を示す。
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.domain import (
    AppRank,
    AppSummary,
    AppUsage,
    CaptureRecord,
    Features,
    FeaturesMeta,
    GlobalKeywords,
    TimeBlock,
)


def example_capture_record_usage() -> None:
    """CaptureRecord の使用例."""
    print("=" * 60)
    print("CaptureRecord の使用例")
    print("=" * 60)

    # 1. 基本的な作成
    record = CaptureRecord(
        ts="2025-12-25T14:30:00+09:00",
        window_title="Visual Studio Code - main.py",
        process_name="code.exe",
        keywords=["function", "async", "await"],
        urls=["github.com", "stackoverflow.com"],
        files=["C:\\Users\\okira\\project\\main.py"],
        numbers=["42", "3.14"],
    )

    print(f"\n1. 作成したレコード:\n{record}")

    # 2. プロパティの利用
    print(f"\n2. プロパティ:")
    print(f"   タイムスタンプ: {record.timestamp}")
    print(f"   アプリ識別子: {record.app_identifier}")
    print(f"   コンテンツあり: {record.has_content}")

    # 3. 特徴量のマージ
    record2 = CaptureRecord(
        ts="2025-12-25T14:32:00+09:00",
        keywords=["class", "method"],
        urls=["python.org"],
    )
    record.merge_features(record2)
    print(f"\n3. マージ後のキーワード: {record.keywords}")

    # 4. JSON シリアライゼーション
    json_str = record.model_dump_json(indent=2)
    print(f"\n4. JSON出力:\n{json_str[:200]}...")

    # 5. JSON デシリアライゼーション
    restored = CaptureRecord.model_validate_json(json_str)
    print(f"\n5. JSON から復元: {restored.window_title}")


def example_features_usage() -> None:
    """Features の使用例."""
    print("\n" + "=" * 60)
    print("Features の使用例")
    print("=" * 60)

    # 1. メタデータの作成
    meta = FeaturesMeta(
        date="2025-12-25",
        generated_at=datetime.now(timezone.utc).isoformat(),
        capture_count=240,
        first_capture="09:00:00",
        last_capture="18:00:00",
        total_duration_min=480.0,
    )

    # 2. 時間ブロックの作成
    time_blocks = [
        TimeBlock(
            start="09:00",
            end="12:00",
            apps=[
                AppUsage(name="VSCode", percent=60.0),
                AppUsage(name="Chrome", percent=30.0),
                AppUsage(name="Slack", percent=10.0),
            ],
            top_keywords=["python", "async", "function"],
            top_files=["main.py", "utils.py"],
        ),
        TimeBlock(
            start="13:00",
            end="18:00",
            apps=[
                AppUsage(name="Chrome", percent=70.0),
                AppUsage(name="VSCode", percent=30.0),
            ],
            top_keywords=["documentation", "API", "REST"],
            top_files=["README.md"],
        ),
    ]

    # 3. アプリサマリの作成
    app_summary = [
        AppSummary(
            name="Visual Studio Code",
            process="code.exe",
            count=120,
            duration_min=250.5,
            rank=AppRank.HIGH,
            top_keywords=["python", "function", "class"],
            top_files=["main.py", "utils.py", "config.py"],
            top_urls=None,
        ),
        AppSummary(
            name="Google Chrome",
            process="chrome.exe",
            count=80,
            duration_min=180.0,
            rank=AppRank.HIGH,
            top_keywords=["documentation", "API", "tutorial"],
            top_files=None,
            top_urls=["github.com", "stackoverflow.com", "python.org"],
        ),
        AppSummary(
            name="Slack",
            process="slack.exe",
            count=40,
            duration_min=49.5,
            rank=AppRank.LOW,
            top_keywords=["meeting", "team"],
            top_files=None,
            top_urls=None,
        ),
    ]

    # 4. グローバルキーワードの作成
    global_keywords = GlobalKeywords(
        top_keywords=["python", "async", "function", "API", "documentation"],
        top_urls=["github.com", "stackoverflow.com", "python.org"],
        top_files=["main.py", "utils.py", "config.py", "README.md"],
    )

    # 5. Features オブジェクトの作成
    features = Features(
        meta=meta,
        time_blocks=time_blocks,
        app_summary=app_summary,
        global_keywords=global_keywords,
    )

    print(f"\n1. 作成した Features:\n{features}")

    # 6. プロパティの利用
    print(f"\n2. プロパティ:")
    print(f"   データあり: {features.has_data}")
    print(f"   トップアプリ: {features.top_app.name if features.top_app else 'なし'}")
    print(f"   アクティブ時間: {features.active_hours}時間")

    # 7. メソッドの利用
    high_rank_apps = features.get_apps_by_rank(AppRank.HIGH)
    print(f"\n3. HIGH ランクのアプリ: {[app.name for app in high_rank_apps]}")

    # 8. JSON シリアライゼーション
    json_str = features.model_dump_json(indent=2)
    print(f"\n4. JSON出力（サイズ: {len(json_str)} バイト）")

    # 9. ファイル保存の例
    output_path = Path("examples/sample_features.json")
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(json_str, encoding="utf-8")
    print(f"\n5. JSON保存先: {output_path.absolute()}")

    # 10. ファイルから読み込み
    loaded_features = Features.model_validate_json(output_path.read_text(encoding="utf-8"))
    print(f"\n6. ファイルから読み込み成功: {loaded_features.meta.date}")


def example_validation_and_error_handling() -> None:
    """バリデーションとエラーハンドリングの例."""
    print("\n" + "=" * 60)
    print("バリデーションとエラーハンドリング")
    print("=" * 60)

    # 1. 自動的な正規化
    record = CaptureRecord(
        ts="2025-12-25T14:30:00+09:00",
        window_title="  Chrome  ",  # 空白がトリミングされる
        keywords=["test", "test", "python"],  # 重複が削除される
    )
    print(f"\n1. 正規化後:")
    print(f"   window_title: '{record.window_title}'")
    print(f"   keywords: {record.keywords}")

    # 2. バリデーションエラー
    print("\n2. バリデーションエラーの例:")
    try:
        CaptureRecord(ts="invalid-timestamp")
    except Exception as e:
        print(f"   エラー: {type(e).__name__}")

    # 3. 自動ソート
    time_block = TimeBlock(
        start="09:00",
        end="10:00",
        apps=[
            AppUsage(name="App1", percent=30.0),
            AppUsage(name="App2", percent=70.0),
            AppUsage(name="App3", percent=50.0),
        ],
    )
    print(f"\n3. 自動ソート後のアプリ順:")
    for app in time_block.apps:
        print(f"   {app.name}: {app.percent}%")

    # 4. frozen モデル
    meta = FeaturesMeta(
        date="2025-12-25",
        generated_at="2025-12-25T18:00:00+09:00",
        capture_count=100,
        first_capture="09:00:00",
        last_capture="18:00:00",
        total_duration_min=480.0,
    )
    features = Features(meta=meta)

    print("\n4. Features は frozen (変更不可):")
    try:
        features.meta = meta  # type: ignore[misc]
    except Exception as e:
        print(f"   変更試行時のエラー: {type(e).__name__}")


def main() -> None:
    """メイン実行."""
    example_capture_record_usage()
    example_features_usage()
    example_validation_and_error_handling()

    print("\n" + "=" * 60)
    print("全ての例が正常に実行されました！")
    print("=" * 60)


if __name__ == "__main__":
    main()
