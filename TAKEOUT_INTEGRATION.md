# Google Takeout 데이터 통합 가이드

## 현재 상황

### 발견된 데이터
- Google Takeout에서 YouTube 재생목록 데이터 추출 완료
- 위치: `takeout_data/251216/Takeout 2/YouTube 및 YouTube Music/재생목록/`
- **Watch Later 포함** 모든 재생목록이 CSV 형식으로 제공됨

### 데이터 구조

#### 1. 재생목록 메타데이터 (`재생목록.csv`)
```
재생목록 ID, 상단에 새 동영상 추가, ..., 재생목록 제목(원본), 재생목록 생성 타임스탬프, ...
```

#### 2. 재생목록 영상 목록 (`{재생목록명}-동영상.csv`)
```
동영상 ID, 재생목록 동영상 생성 타임스탬프
```

## 구현 계획

### Phase 1: CSV 파서 개발
- `takeout_parser.py` 모듈 생성
- CSV 파일 읽기 및 파싱
- 재생목록 메타데이터와 영상 목록 결합

### Phase 2: 기존 Exporters 활용
- 기존 `exporters/` 모듈 재사용
- 동일한 출력 형식 (JSON, Markdown, HTML)
- 재생목록별 폴더 구조 유지

### Phase 3: 메인 스크립트 통합
- `main.py`에 `--takeout` 옵션 추가
- Takeout 모드와 API 모드 선택 가능
- 동일한 출력 디렉토리 사용

## 데이터 변환 로직

### 필요한 작업
1. CSV 파일에서 재생목록 목록 읽기
2. 각 재생목록의 영상 CSV 파일 읽기
3. 영상 ID로 YouTube API 호출하여 상세 정보 가져오기 (선택사항)
   - 또는 CSV 데이터만으로 기본 정보 구성
4. 기존 데이터 구조로 변환
5. 기존 exporters로 출력

## 주의사항

- CSV에는 영상 ID만 있음 → 제목, 썸네일 등은 YouTube API로 가져와야 함
- 또는 CSV 데이터만으로 기본 출력 (ID와 링크만)
- Watch Later는 `Watch later-동영상.csv` 파일로 제공됨

