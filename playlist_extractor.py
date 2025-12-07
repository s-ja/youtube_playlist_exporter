"""
재생목록 추출 로직
병렬 처리 및 데이터 수집
"""
import asyncio
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from youtube_api import YouTubeAPI
import config


class PlaylistExtractor:
    """재생목록 추출 클래스"""
    
    def __init__(self, youtube_api: YouTubeAPI, max_workers: int = 5):
        """
        초기화
        
        Args:
            youtube_api: YouTube API 클라이언트
            max_workers: 병렬 처리 최대 워커 수 (SSL 오류 방지를 위해 1 권장)
        """
        self.youtube_api = youtube_api
        # SSL 오류 방지를 위해 워커 수를 1로 제한 (순차 처리)
        # 병렬 처리는 SSL 연결 충돌을 일으킬 수 있음
        self.max_workers = 1  # 순차 처리로 변경
        if max_workers > 1:
            print(f"⚠️  SSL 오류 방지를 위해 순차 처리 모드로 실행합니다 (워커 수: 1).")
    
    def extract_all_playlists(self) -> List[Dict]:
        """
        모든 재생목록과 영상 정보 추출
        
        Returns:
            재생목록 정보와 영상 리스트가 포함된 딕셔너리 리스트
        """
        import time
        
        print("재생목록 목록 조회 중...")
        playlists = self.youtube_api.get_all_playlists()
        print(f"총 {len(playlists)}개의 재생목록을 찾았습니다.")
        
        # 순차 처리로 각 재생목록의 영상 정보 수집 (SSL 오류 방지)
        results = []
        total = len(playlists)
        
        for idx, playlist in enumerate(playlists, 1):
            try:
                print(f"[{idx}/{total}] {playlist['title']} 처리 중...")
                videos = self._extract_playlist_videos(playlist)
                playlist_data = {
                    **playlist,
                    "videos": videos
                }
                results.append(playlist_data)
                print(f"✓ {playlist['title']}: {len(videos)}개 영상 추출 완료")
                
                # 재생목록 간 짧은 지연 (SSL 연결 안정화)
                if idx < total:
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"✗ {playlist['title']} 추출 실패: {e}")
                # 실패한 재생목록도 빈 영상 리스트로 추가
                results.append({
                    **playlist,
                    "videos": []
                })
                # 실패 후에도 짧은 지연
                time.sleep(0.5)
        
        # 재생목록 제목으로 정렬
        results.sort(key=lambda x: x["title"])
        return results
    
    def _extract_playlist_videos(self, playlist: Dict) -> List[Dict]:
        """
        단일 재생목록의 모든 영상 추출
        
        Args:
            playlist: 재생목록 정보
            
        Returns:
            영상 정보 리스트
        """
        videos = []
        try:
            for video in self.youtube_api.get_playlist_videos(playlist["id"]):
                videos.append(video)
        except Exception as e:
            print(f"재생목록 '{playlist['title']}' 영상 추출 중 오류: {e}")
            raise
        
        return videos
    
    def extract_single_playlist(self, playlist_id: str) -> Dict:
        """
        단일 재생목록 추출
        
        Args:
            playlist_id: 재생목록 ID
            
        Returns:
            재생목록 정보와 영상 리스트
        """
        # 재생목록 정보 조회
        playlists = self.youtube_api.get_all_playlists()
        playlist = next((p for p in playlists if p["id"] == playlist_id), None)
        
        if not playlist:
            raise ValueError(f"재생목록 ID '{playlist_id}'를 찾을 수 없습니다.")
        
        # 영상 정보 추출
        videos = self._extract_playlist_videos(playlist)
        
        return {
            **playlist,
            "videos": videos
        }

