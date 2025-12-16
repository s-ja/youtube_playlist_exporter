"""
Google Takeout CSV 파일 파서
YouTube 재생목록 데이터를 CSV에서 읽어서 Python 데이터 구조로 변환
"""
import csv
from pathlib import Path
from typing import List, Dict, Optional
import re


class TakeoutParser:
    """Google Takeout CSV 파일 파서"""
    
    def __init__(self, takeout_dir: Path):
        """
        초기화
        
        Args:
            takeout_dir: Takeout 데이터 디렉토리 경로
                        예: takeout_data/251216/Takeout 2/YouTube 및 YouTube Music/재생목록/
        """
        self.takeout_dir = Path(takeout_dir)
        self.playlists_csv = self.takeout_dir / "재생목록.csv"
        self.videos_dir = self.takeout_dir
    
    def parse_playlists_metadata(self) -> List[Dict]:
        """
        재생목록 메타데이터 CSV 파일 파싱
        
        Returns:
            재생목록 메타데이터 리스트
        """
        playlists = []
        
        if not self.playlists_csv.exists():
            raise FileNotFoundError(f"재생목록.csv 파일을 찾을 수 없습니다: {self.playlists_csv}")
        
        with open(self.playlists_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                playlists.append({
                    "id": row["재생목록 ID"],
                    "title": row["재생목록 제목(원본)"],
                    "description": "",  # CSV에 설명이 없음
                    "thumbnail": row.get("재생목록 이미지 1 URL", "") or row.get("재생목록 이미지 2 URL", ""),
                    "video_count": 0,  # 영상 파일을 읽어야 알 수 있음
                    "published_at": row.get("재생목록 생성 타임스탬프", ""),
                    "updated_at": row.get("재생목록 업데이트 타임스탬프", ""),
                    "privacy_status": row.get("재생목록 공개 상태", "")
                })
        
        return playlists
    
    def parse_playlist_videos(self, playlist_title: str) -> List[Dict]:
        """
        특정 재생목록의 영상 CSV 파일 파싱
        
        Args:
            playlist_title: 재생목록 제목 (CSV 파일명에서 사용)
            
        Returns:
            영상 정보 리스트 (video_id, added_at 포함)
        """
        # CSV 파일명 생성: "{재생목록명}-동영상.csv"
        # 특수문자 처리 필요
        safe_title = playlist_title.replace("/", "_").replace("\\", "_")
        csv_filename = f"{safe_title}-동영상.csv"
        csv_path = self.videos_dir / csv_filename
        
        # 파일이 없으면 다른 패턴 시도
        if not csv_path.exists():
            # 모든 "-동영상.csv" 파일 검색
            for file in self.videos_dir.glob("*-동영상.csv"):
                # 파일명에서 재생목록명 추출
                file_stem = file.stem.replace("-동영상", "")
                # 정확히 일치하거나, 대소문자 무시 비교
                # 또는 "Watch later"와 "Watch Later" 같은 변형 처리
                title_lower = playlist_title.lower()
                file_stem_lower = file_stem.lower()
                
                if (file_stem == playlist_title or 
                    file_stem == safe_title or
                    file_stem_lower == title_lower or
                    # "Watch later"와 "Watch Later" 매칭
                    (title_lower in ["watch later", "나중에 볼 동영상"] and 
                     file_stem_lower in ["watch later", "watchlater"])):
                    csv_path = file
                    break
        
        if not csv_path.exists():
            print(f"⚠️  영상 CSV 파일을 찾을 수 없습니다: {csv_filename}")
            return []
        
        videos = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                video_id = row.get("동영상 ID", "").strip()
                if not video_id:
                    continue
                
                videos.append({
                    "video_id": video_id,
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "added_at": row.get("재생목록 동영상 생성 타임스탬프", ""),
                    # CSV에는 제목, 썸네일, 채널 정보가 없음
                    # YouTube API로 가져오거나 기본값 사용
                    "title": "",  # 나중에 API로 채울 수 있음
                    "description": "",
                    "thumbnail": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                    "channel_title": "",
                    "position": len(videos)  # 순서대로
                })
        
        return videos
    
    def get_all_playlists_with_videos(self) -> List[Dict]:
        """
        모든 재생목록과 영상 정보 파싱
        
        Returns:
            재생목록 정보와 영상 리스트가 포함된 딕셔너리 리스트
        """
        print("Takeout CSV 파일 파싱 중...")
        playlists_metadata = self.parse_playlists_metadata()
        print(f"총 {len(playlists_metadata)}개의 재생목록을 찾았습니다.")
        
        results = []
        for idx, playlist in enumerate(playlists_metadata, 1):
            print(f"[{idx}/{len(playlists_metadata)}] {playlist['title']} 처리 중...")
            videos = self.parse_playlist_videos(playlist["title"])
            playlist["video_count"] = len(videos)
            playlist["videos"] = videos
            results.append(playlist)
            print(f"✓ {playlist['title']}: {len(videos)}개 영상 발견")
        
        return results
    
    def enrich_video_info(self, videos: List[Dict], youtube_api=None) -> List[Dict]:
        """
        영상 ID로 YouTube API를 호출하여 상세 정보 가져오기 (선택사항)
        
        Args:
            videos: 영상 ID 리스트
            youtube_api: YouTubeAPI 인스턴스 (선택사항)
            
        Returns:
            상세 정보가 포함된 영상 리스트
        """
        if not youtube_api:
            return videos
        
        # TODO: YouTube API를 사용하여 영상 제목, 채널 정보 등 가져오기
        # 현재는 기본 정보만 반환
        return videos

