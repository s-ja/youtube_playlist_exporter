"""
프로젝트 설정 관리 모듈
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드 (선택사항 - OAuth 2.0을 기본으로 사용하므로 필수 아님)
# .env 파일이 있으면 로드하고, 없어도 동작함
load_dotenv()

# 프로젝트 루트 디렉토리
PROJECT_ROOT = Path(__file__).parent

# YouTube API 설정 (선택사항 - OAuth 2.0이 기본값)
# .env 파일이 없어도 OAuth 2.0 인증으로 동작함
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")  # 선택사항
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")  # 선택사항
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")  # 선택사항
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8080")

# 출력 설정 (기본값 사용, .env에서 오버라이드 가능)
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./output"))
OUTPUT_FORMATS = os.getenv("OUTPUT_FORMAT", "json,markdown,html").split(",")

# API 호출 제한 설정
API_RATE_LIMIT = int(os.getenv("API_RATE_LIMIT", "10"))  # 초당 요청 수

# YouTube API 엔드포인트
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# OAuth 2.0 스코프
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

