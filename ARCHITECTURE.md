# 프로젝트 아키텍처 제안

## 현재 상황 분석

### Python API 기반 접근의 한계
- ✅ 일반 재생목록: 완벽하게 추출 가능
- ❌ Watch Later: YouTube Data API v3에서 제공되지 않음
  - `relatedPlaylists.watchLater`가 API 응답에 없음
  - `channelId`로 조회해도 WL로 시작하는 재생목록 없음

### 브라우저 확장 프로그램의 장점
- ✅ YouTube 웹 페이지 DOM에 직접 접근
- ✅ Watch Later 페이지 직접 파싱 가능
- ✅ API 제한 없이 웹 인터페이스의 모든 정보 접근
- ✅ 사용자가 브라우저에서 직접 실행 가능
- ✅ 실시간 데이터 추출 가능

## 제안: 하이브리드 아키텍처

### 옵션 1: 모노레포 구조 (권장) ⭐

```
youtube_playlist_export/
├── python/                    # 기존 Python 프로젝트
│   ├── main.py
│   ├── youtube_api.py
│   ├── playlist_extractor.py
│   ├── exporters/
│   └── ...
├── browser-extension/         # 새로운 브라우저 확장 프로그램
│   ├── manifest.json
│   ├── src/
│   │   ├── background.js      # 백그라운드 스크립트
│   │   ├── content.js         # YouTube 페이지 주입
│   │   ├── popup.html         # 확장 프로그램 UI
│   │   └── popup.js
│   ├── watch-later-extractor.js  # Watch Later 추출 로직
│   └── package.json
├── shared/                    # 공통 유틸리티 (선택사항)
│   └── export-formats.js      # 출력 형식 공통 로직
└── README.md
```

**장점:**
- 하나의 저장소에서 관리
- 공통 로직 공유 가능
- 통합 문서화 용이
- 커서 에디터의 에이전트 분할 활용 가능

**단점:**
- 기술 스택이 다름 (Python + JavaScript)
- 빌드 프로세스 분리 필요

### 옵션 2: 별도 프로젝트

```
youtube_playlist_export/       # Python 프로젝트
youtube_playlist_export_extension/  # 브라우저 확장 프로그램
```

**장점:**
- 완전히 독립적인 프로젝트
- 각각의 기술 스택에 최적화

**단점:**
- 코드 중복 가능성
- 관리 복잡도 증가

## 권장 사항: 옵션 1 (모노레포)

### 구현 전략

1. **브라우저 확장 프로그램 개발**
   - Chrome/Edge 확장 프로그램 (Manifest V3)
   - YouTube Watch Later 페이지 감지
   - DOM 파싱을 통한 영상 정보 추출
   - JSON/CSV 다운로드 기능

2. **Python과의 통합**
   - 브라우저 확장 프로그램에서 추출한 데이터를 Python 스크립트로 전달
   - 또는 브라우저 확장 프로그램이 직접 파일 생성
   - 공통 출력 형식 유지 (JSON, Markdown, HTML)

3. **워크플로우**
   ```
   사용자 선택:
   ├─ Python 스크립트 실행 → 일반 재생목록 추출
   └─ 브라우저 확장 프로그램 → Watch Later 추출
   
   통합:
   └─ 두 결과를 하나의 출력 디렉토리에 통합
   ```

## 기술 스택

### 브라우저 확장 프로그램
- **언어**: JavaScript (ES6+)
- **프레임워크**: Vanilla JS (가벼움) 또는 React (복잡한 UI 필요 시)
- **매니페스트**: Manifest V3
- **빌드 도구**: Webpack 또는 Vite (선택사항)

## 구현 우선순위

1. **Phase 1**: Watch Later 추출 기능
   - YouTube Watch Later 페이지 감지
   - 영상 목록 파싱
   - JSON 출력

2. **Phase 2**: 통합 기능
   - Python 스크립트와 데이터 통합
   - 공통 출력 형식 지원

3. **Phase 3**: 고급 기능
   - 자동 스크롤 (무한 스크롤 처리)
   - 배치 다운로드
   - 진행 상황 표시

## 보안 및 프라이버시

- ✅ 모든 데이터는 로컬에서만 처리
- ✅ 외부 서버로 데이터 전송 없음
- ✅ YouTube 로그인 세션만 사용 (추가 인증 불필요)

## 유지보수 고려사항

- ⚠️ YouTube 웹 페이지 구조 변경에 민감
- ✅ 정기적인 DOM 셀렉터 업데이트 필요
- ✅ 버전 관리 및 테스트 중요

