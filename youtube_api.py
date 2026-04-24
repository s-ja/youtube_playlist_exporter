"""
YouTube API 연동 모듈
OAuth 2.0 인증 및 API 호출 처리
"""
import os
import json
import time
import ssl
from typing import List, Dict, Optional, Iterator
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import httplib2
import config


class YouTubeAPI:
    """YouTube Data API v3 클라이언트"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        YouTube API 클라이언트 초기화
        
        Args:
            api_key: YouTube API 키 (선택사항, OAuth 사용 시 불필요)
                    개인 재생목록 조회를 위해서는 OAuth 2.0 인증이 필수입니다.
        """
        self.api_key = api_key or config.YOUTUBE_API_KEY
        self.service = None
        self.credentials = None
        # OAuth 2.0을 기본 인증 방식으로 사용
        self.use_oauth = True
        # 재시도 설정
        self.max_retries = 5  # 재시도 횟수 증가
        self.retry_delay = 3  # 초 (지연 시간 증가)
        
    def authenticate(self) -> bool:
        """
        OAuth 2.0 인증 수행
        
        Returns:
            인증 성공 여부
        """
        creds = None
        token_file = config.PROJECT_ROOT / "token.json"
        
        # 저장된 토큰이 있으면 로드
        if token_file.exists():
            if not self._token_has_required_scopes(token_file):
                print("\n⚠️  기존 token.json의 OAuth 권한이 현재 작업에 부족합니다.")
                print("   재생목록 항목 삭제를 위해 YouTube 계정 관리 권한 재승인이 필요합니다.")
                print("   기존 토큰은 무시하고 새 권한으로 인증을 진행합니다.")
                print("   인증 문제가 계속되면 token.json을 삭제한 뒤 다시 실행하세요.\n")
            else:
                creds = Credentials.from_authorized_user_file(
                    str(token_file), config.YOUTUBE_SCOPES
                )
        
        # 토큰이 없거나 만료된 경우 새로 인증
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                credentials_file = config.PROJECT_ROOT / "credentials.json"
                if not credentials_file.exists():
                    print("\n❌ OAuth 2.0 인증이 필요합니다.")
                    print("\n개인 재생목록을 조회하려면 OAuth 2.0 인증이 필수입니다.")
                    print("\n설정 방법:")
                    print("1. Google Cloud Console (https://console.cloud.google.com/) 접속")
                    print("2. 프로젝트 선택 또는 생성")
                    print("3. 'API 및 서비스' > '사용자 인증 정보' 이동")
                    print("4. '사용자 인증 정보 만들기' > 'OAuth 클라이언트 ID' 선택")
                    print("5. 애플리케이션 유형: '데스크톱 앱' 선택")
                    print("6. 생성된 클라이언트 ID의 JSON 파일을 다운로드")
                    print("7. 다운로드한 파일을 'credentials.json'으로 이름 변경 후 프로젝트 루트에 저장")
                    print("\n⚠️  OAuth 동의 화면 설정도 필요합니다:")
                    print("   - 'OAuth 동의 화면' 메뉴에서 앱 정보 입력")
                    print("   - '테스트 사용자'에 본인 이메일 추가 (테스트 모드인 경우)")
                    print("\n또는 README.md 파일의 '설치 방법' 섹션을 참고하세요.\n")
                    return False
                
                print("\n🔐 OAuth 2.0 인증을 시작합니다...")
                print("브라우저가 열리면 Google 계정으로 로그인하고 권한을 승인해주세요.\n")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_file), config.YOUTUBE_SCOPES
                )
                creds = flow.run_local_server(
                    port=8080,
                    open_browser=True,
                    prompt='consent'  # 항상 동의 화면 표시
                )
            
            # 토큰 저장
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        
        self.credentials = creds
        
        # credentials를 사용할 때는 http를 직접 전달하지 않음
        # google-auth-httplib2가 자동으로 처리함
        self.service = build(
            config.YOUTUBE_API_SERVICE_NAME,
            config.YOUTUBE_API_VERSION,
            credentials=creds
        )
        return True

    def _token_has_required_scopes(self, token_file) -> bool:
        """
        저장된 token.json이 현재 설정된 OAuth scope를 포함하는지 확인합니다.
        과거 readonly 토큰으로 삭제 API를 호출하는 실수를 막기 위한 사전 점검입니다.
        """
        try:
            with open(token_file, "r", encoding="utf-8") as f:
                token_data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return False

        token_scopes = token_data.get("scopes")
        if isinstance(token_scopes, str):
            token_scope_set = set(token_scopes.split())
        elif isinstance(token_scopes, list):
            token_scope_set = set(token_scopes)
        else:
            return False

        return set(config.YOUTUBE_SCOPES).issubset(token_scope_set)
    
    def get_service(self, require_oauth: bool = True):
        """
        YouTube API 서비스 객체 반환
        
        Args:
            require_oauth: OAuth 인증이 필수인지 여부 (기본값: True)
                         개인 재생목록 조회를 위해 OAuth 2.0이 기본값입니다.
        
        Returns:
            YouTube API 서비스 객체
        """
        if not self.service:
            # OAuth 2.0을 기본 인증 방식으로 사용
            if require_oauth or self.use_oauth:
                if not self.authenticate():
                    raise Exception(
                        "YouTube API OAuth 인증 실패. "
                        "개인 재생목록을 조회하려면 credentials.json 파일이 필요합니다. "
                        "OAuth 동의 화면 설정도 확인해주세요. "
                        "자세한 내용은 README.md를 참고하세요."
                    )
            elif self.api_key:
                # API 키 사용 (공개 데이터만 조회 가능, 제한적 사용)
                print("⚠️  경고: API 키만으로는 개인 재생목록을 조회할 수 없습니다.")
                self.service = build(
                    config.YOUTUBE_API_SERVICE_NAME,
                    config.YOUTUBE_API_VERSION,
                    developerKey=self.api_key
                )
            else:
                # 인증 방법이 없는 경우 OAuth 강제
                if not self.authenticate():
                    raise Exception(
                        "YouTube API 인증 실패. "
                        "credentials.json 파일이 필요합니다. "
                        "자세한 내용은 README.md를 참고하세요."
                    )
        
        return self.service
    
    def _execute_with_retry(self, request_func):
        """
        재시도 로직이 포함된 API 요청 실행
        
        Args:
            request_func: 요청 객체를 생성하는 함수 (매번 새로운 요청 생성)
            
        Returns:
            API 응답
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                request = request_func()
                return request.execute()
            except (HttpError, ssl.SSLError, OSError, ConnectionError, Exception) as e:
                last_exception = e
                # SSL 오류나 연결 오류인 경우에만 재시도
                error_str = str(e).lower()
                is_retryable = (
                    'ssl' in error_str or 
                    'connection' in error_str or 
                    'network' in error_str or
                    'timeout' in error_str or
                    'record layer' in error_str or
                    isinstance(e, (ssl.SSLError, OSError, ConnectionError))
                )
                
                if is_retryable and attempt < self.max_retries - 1:
                    # Exponential backoff with jitter
                    wait_time = self.retry_delay * (2 ** attempt) + (time.time() % 1)
                    print(f"  재시도 중... ({attempt + 1}/{self.max_retries}, {wait_time:.1f}초 대기)")
                    time.sleep(wait_time)
                    # 재시도 전에 서비스 객체 재생성 (SSL 연결 초기화)
                    if attempt >= 2:  # 세 번째 재시도부터
                        try:
                            # 서비스 객체만 초기화 (인증은 유지)
                            if self.service:
                                self.service = None
                        except:
                            pass
                else:
                    if attempt >= self.max_retries - 1:
                        print(f"  최대 재시도 횟수 초과")
                    raise
        
        raise last_exception
    
    def get_all_playlists(self) -> List[Dict]:
        """
        사용자의 모든 재생목록 조회 (Watch Later 포함)
        
        Returns:
            재생목록 정보 리스트
        
        Note:
            mine=True 파라미터 사용을 위해 OAuth 2.0 인증이 필요합니다.
            Watch Later는 시스템 재생목록이므로 채널 정보에서 가져옵니다.
        """
        # mine=True 사용 시 OAuth 인증 필수
        service = self.get_service(require_oauth=True)
        playlists = []
        next_page_token = None
        
        try:
            # 일반 재생목록 조회
            while True:
                response = self._execute_with_retry(
                    lambda: service.playlists().list(
                        part="snippet,contentDetails",
                        mine=True,
                        maxResults=50,
                        pageToken=next_page_token
                    )
                )
                
                for item in response.get("items", []):
                    playlists.append({
                        "id": item["id"],
                        "title": item["snippet"]["title"],
                        "description": item["snippet"].get("description", ""),
                        "thumbnail": item["snippet"]["thumbnails"].get("high", {}).get("url", ""),
                        "video_count": int(item["contentDetails"]["itemCount"]),
                        "published_at": item["snippet"]["publishedAt"]
                    })
                
                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break
            
            # Watch Later 재생목록 추가 (시스템 재생목록)
            try:
                # 채널 정보 조회 (channelId와 relatedPlaylists 모두 가져오기)
                channel_response = self._execute_with_retry(
                    lambda: service.channels().list(
                        part="contentDetails,id",
                        mine=True
                    )
                )
                
                if channel_response.get("items"):
                    channel = channel_response["items"][0]
                    channel_id = channel.get("id")
                    related_playlists = channel.get("contentDetails", {}).get("relatedPlaylists", {})
                    watch_later_id = related_playlists.get("watchLater")
                    
                    # 방법 1: relatedPlaylists에서 watchLater ID 직접 사용
                    if watch_later_id:
                        try:
                            # Watch Later 재생목록 정보 조회
                            watch_later_response = self._execute_with_retry(
                                lambda: service.playlists().list(
                                    part="snippet,contentDetails",
                                    id=watch_later_id
                                )
                            )
                            
                            if watch_later_response.get("items"):
                                item = watch_later_response["items"][0]
                                # 이미 목록에 있는지 확인 (중복 방지)
                                existing_ids = [p["id"] for p in playlists]
                                if item["id"] not in existing_ids:
                                    playlists.append({
                                        "id": item["id"],
                                        "title": "나중에 볼 동영상 (Watch Later)",  # 구분을 위해 명시
                                        "description": item["snippet"].get("description", ""),
                                        "thumbnail": item["snippet"]["thumbnails"].get("high", {}).get("url", ""),
                                        "video_count": int(item["contentDetails"]["itemCount"]),
                                        "published_at": item["snippet"]["publishedAt"]
                                    })
                                    print(f"✓ Watch Later 재생목록 추가됨 (ID: {watch_later_id}, 영상 수: {item['contentDetails']['itemCount']})")
                                else:
                                    print(f"ℹ️  Watch Later 재생목록이 이미 일반 재생목록 목록에 포함되어 있습니다.")
                        except Exception as e:
                            print(f"⚠️  Watch Later 재생목록 조회 실패 (ID: {watch_later_id}): {e}")
                    
                    # 방법 2: channelId를 사용하여 모든 재생목록 조회 (Watch Later 포함)
                    if channel_id and not watch_later_id:
                        try:
                            print(f"ℹ️  channelId를 사용하여 재생목록 추가 검색 중... (채널 ID: {channel_id})")
                            # channelId로 재생목록 조회 (Watch Later는 WL로 시작)
                            channel_playlists_response = self._execute_with_retry(
                                lambda: service.playlists().list(
                                    part="snippet,contentDetails",
                                    channelId=channel_id,
                                    maxResults=50
                                )
                            )
                            
                            existing_ids = [p["id"] for p in playlists]
                            found_watch_later = False
                            
                            for item in channel_playlists_response.get("items", []):
                                playlist_id = item["id"]
                                # Watch Later는 보통 "WL"로 시작하거나 특정 패턴을 가짐
                                # 또는 제목이 "Watch Later" 또는 "나중에 볼 동영상"인 경우
                                title = item["snippet"].get("title", "").lower()
                                is_watch_later = (
                                    playlist_id.startswith("WL") or
                                    "watch later" in title or
                                    "나중에 볼" in title
                                )
                                
                                if is_watch_later and playlist_id not in existing_ids:
                                    playlists.append({
                                        "id": playlist_id,
                                        "title": item["snippet"]["title"],
                                        "description": item["snippet"].get("description", ""),
                                        "thumbnail": item["snippet"]["thumbnails"].get("high", {}).get("url", ""),
                                        "video_count": int(item["contentDetails"]["itemCount"]),
                                        "published_at": item["snippet"]["publishedAt"]
                                    })
                                    print(f"✓ Watch Later 재생목록 발견 및 추가됨 (ID: {playlist_id}, 제목: {item['snippet']['title']})")
                                    found_watch_later = True
                            
                            if not found_watch_later:
                                print(f"ℹ️  channelId로 조회했지만 Watch Later 재생목록을 찾을 수 없습니다.")
                        except Exception as e:
                            print(f"⚠️  channelId를 사용한 재생목록 조회 실패: {e}")
                    
                    if not watch_later_id and not channel_id:
                        print(f"ℹ️  Watch Later 재생목록을 찾을 수 없습니다. (관련 재생목록: {list(related_playlists.keys())})")
                        print(f"   이는 계정 설정 또는 YouTube API 제한일 수 있습니다.")
                        print(f"   사용자가 직접 만든 '나중에 볼 동영상' 재생목록은 이미 포함되어 있습니다.")
            except Exception as e:
                print(f"⚠️  Watch Later 재생목록 조회 중 오류 (무시하고 계속): {e}")
                import traceback
                traceback.print_exc()
                    
        except (HttpError, ssl.SSLError, OSError, ConnectionError) as e:
            print(f"재생목록 조회 중 오류 발생: {e}")
            raise
        
        return playlists
    
    def get_playlist_videos(self, playlist_id: str) -> Iterator[Dict]:
        """
        재생목록의 모든 영상 조회 (페이지네이션 처리)
        
        Args:
            playlist_id: 재생목록 ID
            
        Yields:
            영상 정보 딕셔너리
        """
        # OAuth 2.0 인증 사용 (기본값)
        service = self.get_service(require_oauth=True)
        next_page_token = None
        
        try:
            while True:
                response = self._execute_with_retry(
                    lambda: service.playlistItems().list(
                        part="snippet,contentDetails",
                        playlistId=playlist_id,
                        maxResults=50,
                        pageToken=next_page_token
                    )
                )
                
                for item in response.get("items", []):
                    # 삭제된 영상 처리
                    if "contentDetails" not in item or "videoId" not in item["contentDetails"]:
                        continue
                    
                    video_id = item["contentDetails"]["videoId"]
                    snippet = item["snippet"]
                    
                    # 썸네일 우선순위: high > medium > default
                    thumbnails = snippet.get("thumbnails", {})
                    thumbnail_url = (
                        thumbnails.get("high", {}).get("url") or
                        thumbnails.get("medium", {}).get("url") or
                        thumbnails.get("default", {}).get("url") or
                        ""
                    )
                    
                    yield {
                        "playlist_item_id": item["id"],
                        "video_id": video_id,
                        "title": snippet.get("title", "제목 없음"),
                        "description": snippet.get("description", ""),
                        "thumbnail": thumbnail_url,
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                        "position": snippet.get("position", 0),
                        "added_at": snippet.get("publishedAt", ""),
                        "channel_title": snippet.get("videoOwnerChannelTitle", "")
                    }
                
                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break
                
                # API 호출 간 지연 (Rate limiting 및 SSL 안정화)
                time.sleep(0.3)
                    
        except (HttpError, ssl.SSLError, OSError, ConnectionError) as e:
            print(f"재생목록 영상 조회 중 오류 발생 (재생목록 ID: {playlist_id}): {e}")
            raise
