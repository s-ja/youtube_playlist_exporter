"""
Execute duplicate playlist item deletion from a local dry-run target file.

The default mode is dry-run. Real deletion only happens with --execute and an
interactive y/n confirmation.
"""
import argparse
import json
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    from googleapiclient.errors import HttpError
except ModuleNotFoundError:
    class HttpError(Exception):
        """Fallback used only when google-api-python-client is not installed for tests."""

        resp = None
        content = None


def load_target_file(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    delete_list = data.get("delete_list")
    if not isinstance(delete_list, list):
        raise ValueError("target JSON에 delete_list 배열이 없습니다.")

    return data


def load_successful_playlist_item_ids(log_dir: Path) -> set[str]:
    successful_ids: set[str] = set()

    for path in sorted(log_dir.glob("deletion_success_*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                records = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue

        if not isinstance(records, list):
            continue

        for record in records:
            if not isinstance(record, dict):
                continue
            playlist_item_id = record.get("playlistItemId")
            if playlist_item_id not in (None, ""):
                successful_ids.add(str(playlist_item_id))

    return successful_ids


def pending_targets(delete_list: List[Any], successful_ids: set[str], ignore_success_log: bool) -> List[str]:
    targets = [str(item) for item in delete_list if item not in (None, "")]
    if ignore_success_log:
        return targets
    return [item for item in targets if item not in successful_ids]


def limited_targets(targets: List[Any], limit: Optional[int]) -> List[str]:
    targets = [str(item) for item in targets if item not in (None, "")]
    if limit is not None:
        if limit < 1:
            raise ValueError("--limit 값은 1 이상이어야 합니다.")
        targets = targets[:limit]
    return targets


def print_plan(
    target_data: Dict[str, Any],
    target_path: Path,
    targets: List[str],
    execute: bool,
    successful_count: int,
    pending_count: int,
    ignore_success_log: bool,
) -> None:
    summary = target_data.get("summary", {})
    source_file = target_data.get("source_file", "N/A")
    full_delete_count = len(target_data.get("delete_list", []))

    print("삭제 실행 계획")
    print(f"- 모드: {'EXECUTE' if execute else 'DRY-RUN'}")
    print(f"- target 파일: {target_path}")
    print(f"- source_file: {source_file}")
    print(f"- summary.duplicate_count: {summary.get('duplicate_count', 'N/A')}")
    print(f"- delete_list 전체 개수: {full_delete_count}")
    print(f"- 성공 로그 기반 제외: {'사용 안 함' if ignore_success_log else '사용'}")
    print(f"- 이미 삭제 성공 로그에 있는 개수: {successful_count}")
    print(f"- 이번 실행 가능 잔여 개수: {pending_count}")
    print(f"- limit 적용 후 실제 요청 개수: {len(targets)}")


def confirm_execution() -> bool:
    answer = input("정말 삭제를 진행하시겠습니까? (y/n): ").strip().lower()
    return answer == "y"


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def backup_target_file(target_path: Path, log_dir: Path, ts: str) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    backup_path = log_dir / f"delete_backup_{ts}.json"
    shutil.copy2(target_path, backup_path)
    return backup_path


def write_log(path: Path, records: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def http_error_info(error: HttpError) -> Dict[str, Any]:
    status = getattr(error.resp, "status", None)
    reason = getattr(error.resp, "reason", "")
    detail = ""

    if error.content:
        try:
            parsed = json.loads(error.content.decode("utf-8"))
            detail = parsed.get("error", {}).get("message", "")
            errors = parsed.get("error", {}).get("errors", [])
            if errors and not reason:
                reason = errors[0].get("reason", "")
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            detail = str(error)

    return {
        "http_status": status,
        "reason": reason,
        "detail": detail or str(error),
    }


def progress_iter(items: List[str]) -> Iterable[str]:
    try:
        from tqdm import tqdm

        return tqdm(items, desc="Deleting", unit="item")
    except ImportError:
        return items


def delete_playlist_items(service, playlist_item_ids: List[str], delay: float) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    successes: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []
    total = len(playlist_item_ids)

    for index, playlist_item_id in enumerate(progress_iter(playlist_item_ids), 1):
        if "tqdm" not in sys.modules:
            print(f"[{index}/{total}] 삭제 요청: {playlist_item_id}")

        try:
            service.playlistItems().delete(id=playlist_item_id).execute()
            successes.append(
                {
                    "playlistItemId": playlist_item_id,
                    "status": "deleted",
                    "index": index,
                }
            )
        except HttpError as e:
            failures.append(
                {
                    "playlistItemId": playlist_item_id,
                    "index": index,
                    **http_error_info(e),
                }
            )
        except Exception as e:
            failures.append(
                {
                    "playlistItemId": playlist_item_id,
                    "index": index,
                    "http_status": None,
                    "reason": type(e).__name__,
                    "detail": str(e),
                }
            )

        if index < total and delay > 0:
            time.sleep(delay)

    return successes, failures


def main() -> int:
    parser = argparse.ArgumentParser(
        description="target_to_delete.json의 delete_list를 사용해 YouTube 재생목록 중복 항목을 삭제합니다."
    )
    parser.add_argument(
        "target_json",
        type=Path,
        help="deduplicator.py가 생성한 target_to_delete.json 경로",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="실제 삭제를 실행합니다. 이 플래그가 없으면 dry-run만 수행합니다.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="이번 실행에서 처리할 delete_list 앞쪽 N개만 선택합니다.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="삭제 요청 사이의 대기 시간(초). 기본값: 2.0",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        help="백업/성공/실패 로그 저장 디렉토리. 기본값: target JSON이 있는 디렉토리",
    )
    parser.add_argument(
        "--ignore-success-log",
        action="store_true",
        help="기존 deletion_success_*.json 로그를 무시하고 delete_list를 처음부터 다시 대상으로 삼습니다.",
    )

    args = parser.parse_args()

    try:
        target_data = load_target_file(args.target_json)
        log_dir = args.log_dir or args.target_json.parent
        successful_ids = load_successful_playlist_item_ids(log_dir)
        pending = pending_targets(
            target_data["delete_list"],
            successful_ids,
            args.ignore_success_log,
        )
        targets = limited_targets(pending, args.limit)

        print_plan(
            target_data,
            args.target_json,
            targets,
            args.execute,
            len(successful_ids),
            len(pending),
            args.ignore_success_log,
        )

        if not targets:
            print("삭제 대상이 없습니다.")
            return 0

        if not args.execute:
            print("DRY-RUN 모드입니다. 실제 삭제는 수행하지 않습니다.")
            print("실제 삭제 테스트 예: python3 deleter.py target_to_delete.json --execute --limit 1")
            return 0

        if not confirm_execution():
            print("사용자 확인이 없어 삭제를 취소했습니다.")
            return 1

        ts = timestamp()
        backup_path = backup_target_file(args.target_json, log_dir, ts)
        print(f"삭제 대상 백업 파일 생성: {backup_path}")

        from youtube_api import YouTubeAPI

        youtube_api = YouTubeAPI()
        service = youtube_api.get_service(require_oauth=True)
        successes, failures = delete_playlist_items(service, targets, args.delay)

        success_path = log_dir / f"deletion_success_{ts}.json"
        failed_path = log_dir / f"deletion_failed_{ts}.json"
        write_log(success_path, successes)
        write_log(failed_path, failures)

        print("삭제 실행 완료")
        print(f"- 성공: {len(successes)}개 ({success_path})")
        print(f"- 실패: {len(failures)}개 ({failed_path})")
        return 0 if not failures else 2
    except Exception as e:
        print(f"오류: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
