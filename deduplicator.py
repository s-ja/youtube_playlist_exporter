"""
Local playlist duplicate analysis.

This module reads an exported playlist JSON file and prepares a dry-run list of
playlist item IDs that can be deleted later. It does not call the YouTube API.
"""
import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


VIDEO_ID_KEYS = ("videoId", "video_id")
PLAYLIST_ITEM_ID_KEYS = ("playlistItemId", "playlist_item_id")
ITEMS_KEYS = ("items", "videos")


@dataclass
class DeduplicationResult:
    total_count: int
    unique_count: int
    duplicate_count: int
    keep_list: List[str]
    delete_list: List[str]
    duplicate_groups: List[Dict[str, Any]]


def _first_value(item: Dict[str, Any], keys: tuple[str, ...]) -> Optional[Any]:
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return value
    return None


def _load_items(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    for key in ITEMS_KEYS:
        value = data.get(key)
        if isinstance(value, list):
            return value
    raise ValueError("JSON 파일에서 items 또는 videos 배열을 찾을 수 없습니다.")


def _position(item: Dict[str, Any], fallback: int) -> int:
    value = item.get("position", fallback)
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def analyze_playlist_json(input_path: Path) -> DeduplicationResult:
    """
    Analyze duplicate videos in a playlist export JSON file.

    Args:
        input_path: Path to a JSON file exported by this project or a compatible
            YouTube playlist exporter.

    Returns:
        DeduplicationResult containing keep/delete playlist item IDs.

    Raises:
        ValueError: If duplicate entries cannot be mapped to playlist item IDs.
    """
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = _load_items(data)
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            continue

        video_id = _first_value(item, VIDEO_ID_KEYS)
        if not video_id:
            continue

        normalized = dict(item)
        normalized["_position"] = _position(item, index)
        normalized["_playlist_item_id"] = _first_value(item, PLAYLIST_ITEM_ID_KEYS)
        normalized["_source_index"] = index
        grouped[str(video_id)].append(normalized)

    keep_list: List[str] = []
    delete_list: List[str] = []
    duplicate_groups: List[Dict[str, Any]] = []
    missing_keep_ids: List[Dict[str, Any]] = []
    missing_delete_ids: List[Dict[str, Any]] = []

    for video_id, group in grouped.items():
        sorted_group = sorted(
            group,
            key=lambda item: (item["_position"], item["_source_index"]),
        )

        keep_item = sorted_group[0]
        keep_id = keep_item.get("_playlist_item_id")
        if keep_id:
            keep_list.append(str(keep_id))

        duplicates = sorted_group[1:]
        if not duplicates:
            continue

        if not keep_id:
            missing_keep_ids.append(
                {
                    "videoId": video_id,
                    "position": keep_item["_position"],
                    "title": keep_item.get("title", ""),
                }
            )

        group_delete_ids: List[str] = []
        for duplicate in duplicates:
            playlist_item_id = duplicate.get("_playlist_item_id")
            if playlist_item_id:
                delete_id = str(playlist_item_id)
                delete_list.append(delete_id)
                group_delete_ids.append(delete_id)
            else:
                missing_delete_ids.append(
                    {
                        "videoId": video_id,
                        "position": duplicate["_position"],
                        "title": duplicate.get("title", ""),
                    }
                )

        duplicate_groups.append(
            {
                "videoId": video_id,
                "keepPlaylistItemId": str(keep_id) if keep_id else None,
                "keepPosition": keep_item["_position"],
                "deletePlaylistItemIds": group_delete_ids,
                "duplicateCount": len(duplicates),
            }
        )

    if missing_keep_ids or missing_delete_ids:
        sample = {
            "missing_keep_ids": missing_keep_ids[:5],
            "missing_delete_ids": missing_delete_ids[:5],
        }
        raise ValueError(
            "중복 그룹 중 playlistItemId/playlist_item_id가 없는 항목이 있습니다. "
            "실제 삭제에는 playlist item ID가 필요하므로 최신 코드로 재추출한 JSON을 사용하세요. "
            f"누락 예시: {sample}"
        )

    return DeduplicationResult(
        total_count=len(items),
        unique_count=len(grouped),
        duplicate_count=len(delete_list),
        keep_list=keep_list,
        delete_list=delete_list,
        duplicate_groups=duplicate_groups,
    )


def write_dry_run_output(result: DeduplicationResult, output_path: Path, input_path: Path) -> None:
    output = {
        "source_file": str(input_path),
        "summary": {
            "total_count": result.total_count,
            "unique_count": result.unique_count,
            "duplicate_count": result.duplicate_count,
        },
        "keep_list": result.keep_list,
        "delete_list": result.delete_list,
        "duplicate_groups": result.duplicate_groups,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


def print_summary(result: DeduplicationResult, output_path: Path) -> None:
    print("중복 분석 완료")
    print(f"- 총 분석한 영상 수: {result.total_count}")
    print(f"- 고유한 영상 수: {result.unique_count}")
    print(f"- 삭제 예정인 중복 영상 수: {result.duplicate_count}")
    print(f"- Dry-run 삭제 대상 파일: {output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="추출된 재생목록 JSON에서 중복 영상을 분석하고 삭제 대상 dry-run 파일을 생성합니다."
    )
    parser.add_argument(
        "input_json",
        type=Path,
        help="분석할 재생목록 JSON 파일 경로",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("target_to_delete.json"),
        help="dry-run 삭제 대상 JSON 출력 경로 (기본값: ./target_to_delete.json)",
    )

    args = parser.parse_args()

    try:
        result = analyze_playlist_json(args.input_json)
        write_dry_run_output(result, args.output, args.input_json)
        print_summary(result, args.output)
        return 0
    except Exception as e:
        print(f"오류: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
