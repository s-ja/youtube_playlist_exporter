# 중복 삭제 워크플로우 후속 개선 핸드오프

## 현재 구현 상태

- `deduplicator.py`
  - 추출된 재생목록 JSON을 로컬에서 분석한다.
  - `video_id`/`videoId` 기준으로 중복을 찾는다.
  - `position`이 가장 작은 항목 하나를 보존하고, 나머지 항목의 `playlist_item_id`/`playlistItemId`를 `delete_list`로 저장한다.
  - 기본 출력은 `target_to_delete.json`이다.

- `deleter.py`
  - `target_to_delete.json`의 `delete_list`를 기반으로 YouTube `playlistItems.delete`를 실행한다.
  - 기본값은 dry-run이며, `--execute`와 y/n 확인이 있어야 실제 삭제한다.
  - `--limit N`, `--delay`, `--log-dir`를 지원한다.
  - 실행 전 `delete_backup_*.json`을 만들고, 성공/실패 결과를 `deletion_success_*.json`, `deletion_failed_*.json`로 저장한다.
  - 같은 로그 디렉토리의 `deletion_success_*.json`을 읽어 이미 성공한 `playlistItemId`는 다음 실행 대상에서 자동 제외한다.
  - `--ignore-success-log`로 성공 로그 기반 제외를 비활성화할 수 있다.

## 실제 검증 결과

- GCP OAuth scope를 `https://www.googleapis.com/auth/youtube`로 조정했다.
- 로컬 `token.json` 삭제 후 `--execute` 실행 시 새 권한으로 재인증이 진행됐다.
- `target_to_delete.json` 기준 삭제 대상 17개를 다음 순서로 처리했다.
  - `--execute --limit 1`: 1개 성공
  - `--execute --limit 1`: 성공 로그를 읽어 다음 1개 성공
  - `--execute --limit 20`: 기존 성공 2개를 제외하고 남은 15개만 처리, 15개 성공
- 최종적으로 17개 삭제 대상 처리 성공, 실패 0개로 확인됐다.

## 현재 사용성 문제

다수 사용자가 수십 개 재생목록을 대상으로 반복 실행할 경우, 현재 기본 설정은 작업 루트에 아래 파일들을 계속 생성한다.

- `target_to_delete.json`
- `delete_backup_YYYYMMDD_HHMMSS.json`
- `deletion_success_YYYYMMDD_HHMMSS.json`
- `deletion_failed_YYYYMMDD_HHMMSS.json`

현재 파일들은 `.gitignore`의 `*.json` 규칙으로 Git 추적 대상은 아니지만, 사용성 측면에서는 루트 디렉토리가 쉽게 지저분해진다. 특히 재생목록별 실행 이력과 로그를 사람이 구분하기 어렵다.

## 후속 개선 검토 요청 프롬프트

현재 프로젝트는 YouTube 재생목록 추출 JSON을 기반으로 중복 영상을 식별하고, `playlistItems.delete`로 원본 재생목록에서 중복 항목만 삭제하는 Python 로컬 도구다.

이미 구현된 안전장치:
- 실제 삭제 전 dry-run 기본값
- `--execute` 및 y/n 확인 필수
- `--limit`, `--delay`
- 삭제 전 백업 파일 생성
- 성공/실패 로그 분리
- 성공 로그 기반 재실행 제외
- OAuth scope는 `https://www.googleapis.com/auth/youtube`

후속 기획/분석 요청:
1. 다수 재생목록을 반복 처리하는 사용성을 고려해 로그와 dry-run 산출물의 디렉토리 구조를 제안할 것.
2. 루트 디렉토리 난립을 피하고, 재생목록별 실행 이력을 사람이 쉽게 확인할 수 있어야 한다.
3. 기존 `--log-dir` 옵션과 호환되거나 자연스럽게 대체 가능한 설계를 우선할 것.
4. 과도한 DB나 복잡한 상태 관리 도입은 피하고, 현재 로컬 파일 기반 구조를 유지하는 방향을 우선할 것.
5. 기존 JSON exporter 출력 구조(`output/<playlist title>/<playlist title>.json`)와 어떻게 연결할지 검토할 것.
6. 실제 구현 변경 범위, 마이그레이션 필요 여부, CLI UX 변경안을 함께 제안할 것.

