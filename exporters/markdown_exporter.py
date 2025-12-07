"""
Markdown 형식 출력 모듈
"""
from pathlib import Path
from typing import Dict
from exporters.base_exporter import BaseExporter


class MarkdownExporter(BaseExporter):
    """Markdown 형식으로 재생목록 데이터 출력"""
    
    def export(self, playlist_data: Dict) -> Path:
        """
        재생목록 데이터를 Markdown 파일로 출력
        
        Args:
            playlist_data: 재생목록 정보와 영상 리스트
            
        Returns:
            생성된 파일 경로
        """
        # 재생목록별 폴더 생성
        playlist_dir = self.get_playlist_dir(playlist_data["title"])
        filename = self.sanitize_filename(playlist_data["title"])
        filepath = playlist_dir / f"{filename}.md"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            # 헤더
            f.write(f"# {playlist_data['title']}\n\n")
            
            # 재생목록 정보
            if playlist_data.get("description"):
                f.write(f"{playlist_data['description']}\n\n")
            
            f.write(f"**영상 개수:** {len(playlist_data['videos'])}\n\n")
            f.write(f"**생성일:** {playlist_data.get('published_at', 'N/A')}\n\n")
            f.write("---\n\n")
            
            # 영상 목록
            f.write("## 영상 목록\n\n")
            
            for idx, video in enumerate(playlist_data["videos"], 1):
                f.write(f"{idx}. [{video['title']}]({video['url']})\n")
                if video.get("channel_title"):
                    f.write(f"   - 채널: {video['channel_title']}\n")
                if video.get("added_at"):
                    f.write(f"   - 추가일: {video['added_at']}\n")
                f.write("\n")
        
        return filepath
    
    def get_file_extension(self) -> str:
        return ".md"

