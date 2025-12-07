# YouTube 재생목록 추출기

YouTube 계정의 재생목록을 추출하여 JSON, Markdown, HTML 형식으로 백업하는 도구입니다.

## 주요 기능

### Python 스크립트
- ✅ YouTube 계정의 모든 재생목록 자동 추출 (API 기반)
- ✅ 재생목록별 영상 정보 수집 (제목, 링크, 썸네일, 채널 정보 등)
- ✅ 다중 형식 출력 지원 (JSON, Markdown, HTML)
- ✅ HTML 형식으로 썸네일 포함 시각적 확인 가능
- ✅ 순차 처리로 안정적인 데이터 수집
- ✅ 커서 에디터의 에이전트 분할 및 병렬 요청 처리 활용

### 브라우저 확장 프로그램 (개발 예정)
- 🚧 Watch Later 재생목록 추출 (API로 접근 불가능한 경우)
- 🚧 YouTube 웹 페이지에서 직접 데이터 추출
- 🚧 Python 스크립트와 동일한 출력 형식 지원

## 프로젝트 구조

```
youtube_playlist_export/
├── main.py                 # 메인 실행 파일
├── config.py              # 설정 관리
├── youtube_api.py         # YouTube API 연동
├── playlist_extractor.py  # 재생목록 추출 로직
├── exporters/             # 출력 모듈
│   ├── base_exporter.py
│   ├── json_exporter.py
│   ├── markdown_exporter.py
│   └── html_exporter.py
├── browser-extension/     # 브라우저 확장 프로그램 (Watch Later 추출)
│   ├── manifest.json
│   ├── content.js         # YouTube 페이지 주입
│   ├── popup.html         # 확장 프로그램 UI
│   ├── popup.js
│   └── background.js
├── utils/                 # 유틸리티 모듈
├── requirements.txt       # Python 패키지 의존성
├── .env.example          # 환경 변수 예시
├── ARCHITECTURE.md        # 아키텍처 문서
└── README.md            # 프로젝트 문서
```

## 설치 방법

### 1. 저장소 클론 및 의존성 설치

```bash
# Python 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. YouTube API 설정

**⚠️ 중요: 이 앱은 OAuth 2.0 인증을 기본으로 사용합니다.**

개인 재생목록을 조회하려면 OAuth 2.0 인증이 필수입니다. API 키만으로는 공개 재생목록만 조회할 수 있으며, 본인의 재생목록(`mine=true`)을 조회할 수 없습니다.

#### 방법 1: OAuth 2.0 사용 (권장 - 개인 재생목록 포함)

1. [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트 생성
2. YouTube Data API v3 활성화
3. OAuth 2.0 클라이언트 ID 생성:
   - 'API 및 서비스' > '사용자 인증 정보' 이동
   - '사용자 인증 정보 만들기' > 'OAuth 클라이언트 ID' 선택
   - 애플리케이션 유형: **'데스크톱 앱'** 선택
   - 이름 입력 후 생성
4. 생성된 클라이언트 ID의 JSON 파일을 다운로드
5. 다운로드한 파일을 `credentials.json`으로 이름 변경 후 프로젝트 루트에 저장

**⚠️ 중요: OAuth 동의 화면 설정 (403 오류 해결)**

OAuth 클라이언트 ID를 생성한 후, 반드시 OAuth 동의 화면을 설정해야 합니다:

1. Google Cloud Console에서 **'API 및 서비스' > 'OAuth 동의 화면'** 이동
2. **사용자 유형 선택**:
   - **외부**: 일반 사용자도 사용 가능 (Google Workspace가 아닌 경우 유일한 옵션)
   - **내부**: Google Workspace 조직 내부만 사용 (Google Workspace 사용자만 가능)
3. **앱 정보 입력**:
   - 앱 이름: 예) "YouTube 재생목록 추출기"
   - 사용자 지원 이메일: 본인 이메일
   - 앱 로고: 선택사항
4. **범위(Scopes) 추가**:
   - '범위 추가 또는 삭제' 클릭
   - `https://www.googleapis.com/auth/youtube.readonly` 선택
   - 저장

**403 오류 해결 방법 (두 가지 옵션):**

### 옵션 1: 테스트 모드 유지 (권장 - 개인 사용 시)

1. OAuth 동의 화면에서 **"테스트"** 상태 유지
2. **'테스트 사용자'** 섹션에서 '+ 사용자 추가' 클릭
3. **본인의 Google 계정 이메일 주소 추가** (매우 중요!)
4. 저장

**장점:**
- 설정이 간단함
- Google 검증 불필요
- 개인 사용 목적에 적합

**단점:**
- 테스트 사용자로 등록된 계정만 사용 가능
- 7일마다 동의 화면이 다시 표시될 수 있음

### 옵션 2: 앱 게시 (프로덕션 모드)

1. OAuth 동의 화면에서 **"앱 게시"** 클릭
2. 확인 대화상자에서 "게시" 선택

**장점:**
- 모든 사용자가 접근 가능 (테스트 사용자 등록 불필요)
- 동의 화면이 자주 표시되지 않음

**단점:**
- Google 검증이 필요할 수 있음 (앱이 공개적으로 사용되는 경우)
- 개인 사용 목적이라면 검증 없이도 사용 가능하지만, 일부 제한이 있을 수 있음
- "앱이 확인되지 않음" 경고가 표시될 수 있음

**개인 사용 목적이라면 옵션 1(테스트 모드)을 권장합니다.**

**첫 실행 시:**
- 브라우저가 자동으로 열리며 Google 계정 로그인 요청
- YouTube 데이터 읽기 권한 승인
- 인증 토큰이 `token.json` 파일로 저장되어 이후 자동 인증

#### 방법 2: API 키 사용 (공개 재생목록만 조회 가능)

⚠️ **주의**: API 키만으로는 개인 재생목록을 조회할 수 없습니다. 공개 재생목록만 조회 가능합니다.

**참고**: OAuth 2.0을 기본으로 사용하므로 `.env` 파일은 선택사항입니다. API 키를 사용하려는 경우에만 필요합니다.

1. [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트 생성
2. YouTube Data API v3 활성화
3. API 키 생성
4. `.env` 파일 생성 (선택사항):

```bash
cp .env.example .env
```

`.env` 파일에 API 키 추가:
```
YOUTUBE_API_KEY=your_api_key_here
```

## 사용 방법

### 기본 사용 (모든 재생목록 추출)

```bash
python main.py
```

### 특정 재생목록만 추출

```bash
python main.py --playlist-id PLxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 출력 형식 지정

```bash
# JSON만 출력
python main.py --format json

# JSON과 Markdown 출력
python main.py --format json,markdown

# 모든 형식 출력 (기본값)
python main.py --format json,markdown,html
```

### 출력 디렉토리 지정

```bash
python main.py --output-dir ./my_backup
```

### 병렬 처리 워커 수 조정

```bash
python main.py --workers 10
```

### 명령줄에서 API 키 지정

```bash
python main.py --api-key your_api_key_here
```

## 출력 구조

출력 파일은 재생목록별로 폴더가 생성되어 정리됩니다:

```
output/
├── 재생목록명1/
│   ├── 재생목록명1.json
│   ├── 재생목록명1.md
│   └── 재생목록명1.html
├── 재생목록명2/
│   ├── 재생목록명2.json
│   ├── 재생목록명2.md
│   └── 재생목록명2.html
└── ...
```

## 출력 형식

### JSON 형식

재생목록 정보와 영상 리스트를 구조화된 JSON 형식으로 저장합니다.

```json
{
  "playlist_id": "PLxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "title": "재생목록 이름",
  "description": "재생목록 설명",
  "video_count": 10,
  "published_at": "2024-01-01T00:00:00Z",
  "videos": [
    {
      "video_id": "xxxxxxxxxxx",
      "title": "영상 제목",
      "url": "https://www.youtube.com/watch?v=xxxxxxxxxxx",
      "thumbnail": "https://i.ytimg.com/...",
      "channel_title": "채널 이름",
      "added_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Markdown 형식

읽기 쉬운 Markdown 형식으로 저장합니다. 영상 목록과 링크가 포함됩니다.

### HTML 형식

썸네일 이미지가 포함된 시각적인 HTML 파일로 저장합니다. 브라우저에서 바로 확인할 수 있습니다.

## 커서 에디터 활용 전략

이 프로젝트는 커서 에디터의 고급 기능을 활용하도록 설계되었습니다:

### 1. 모듈화된 구조
- 각 기능이 독립적인 모듈로 분리되어 에이전트가 병렬로 작업 가능
- `exporters/` 디렉토리의 각 Exporter는 독립적으로 수정/확장 가능

### 2. 병렬 처리 최적화
- `PlaylistExtractor`는 `ThreadPoolExecutor`를 사용하여 여러 재생목록을 동시에 처리
- API 호출 제한을 고려한 워커 수 조정 가능

### 3. 확장 가능한 아키텍처
- `BaseExporter`를 상속하여 새로운 출력 형식 추가 용이
- 설정 파일을 통한 중앙 집중식 관리

### Watch Later 재생목록 추출

**⚠️ 중요**: YouTube Data API v3에서는 Watch Later 재생목록에 접근할 수 없을 수 있습니다.

### 해결 방법: 브라우저 확장 프로그램

Watch Later를 추출하려면 브라우저 확장 프로그램을 사용하세요:

1. `browser-extension/` 디렉토리로 이동
2. Chrome/Edge에서 확장 프로그램 로드
3. YouTube Watch Later 페이지 (`https://www.youtube.com/playlist?list=WL`) 열기
4. 확장 프로그램 아이콘 클릭 → "추출 시작"
5. 자동으로 모든 영상 수집 후 다운로드

자세한 내용은 `browser-extension/README.md`를 참고하세요.

## 향후 개선 제안

1. **브라우저 확장 프로그램 완성**: Watch Later 추출 기능 구현
2. **Python과 확장 프로그램 통합**: 두 결과를 하나의 출력으로 통합
3. **비동기 처리 강화**: `asyncio`와 `aiohttp`를 활용한 완전한 비동기 처리
4. **증분 백업**: 마지막 백업 이후 변경된 재생목록만 업데이트
5. **에러 복구**: 실패한 재생목록 재시도 로직
6. **통계 및 리포트**: 재생목록별 통계 정보 생성
7. **다중 계정 지원**: 여러 YouTube 계정의 재생목록 통합 관리

## 주의사항

- YouTube Data API v3는 일일 할당량이 있습니다 (기본 10,000 units/day)
- 재생목록 조회: 1 unit
- 재생목록 아이템 조회: 1 unit
- 대량의 재생목록이 있는 경우 할당량을 고려하여 사용하세요
- API 키는 절대 공개 저장소에 커밋하지 마세요

## 라이선스

MIT License

## 기여

이슈 및 풀 리퀘스트를 환영합니다!

