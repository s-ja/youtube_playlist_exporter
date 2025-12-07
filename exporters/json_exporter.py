"""
JSON 형식 출력 모듈
"""
import json
from pathlib import Path
from typing import Dict
from exporters.base_exporter import BaseExporter


class JSONExporter(BaseExporter):
    """JSON 형식으로 재생목록 데이터 출력"""
    
    def export(self, playlist_data: Dict) -> Path:
        """
        재생목록 데이터를 JSON 파일로 출력
        
        Args:
            playlist_data: 재생목록 정보와 영상 리스트
            
        Returns:
            생성된 파일 경로
        """
        # 재생목록별 폴더 생성
        playlist_dir = self.get_playlist_dir(playlist_data["title"])
        filename = self.sanitize_filename(playlist_data["title"])
        filepath = playlist_dir / f"{filename}.json"
        
        # JSON 직렬화 가능한 형태로 변환
        output_data = {
            "playlist_id": playlist_data["id"],
            "title": playlist_data["title"],
            "description": playlist_data.get("description", ""),
            "video_count": playlist_data.get("video_count", len(playlist_data["videos"])),
            "published_at": playlist_data.get("published_at", ""),
            "videos": playlist_data["videos"]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def get_file_extension(self) -> str:
        return ".json"

