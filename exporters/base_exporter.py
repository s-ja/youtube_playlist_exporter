"""
출력 모듈 기본 클래스
"""
from abc import ABC, abstractmethod
from typing import List, Dict
from pathlib import Path
import config


class BaseExporter(ABC):
    """출력 모듈 기본 클래스"""
    
    def __init__(self, output_dir: Path = None):
        """
        초기화
        
        Args:
            output_dir: 출력 디렉토리 경로
        """
        self.base_output_dir = output_dir or config.OUTPUT_DIR
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
    
    def get_playlist_dir(self, playlist_title: str) -> Path:
        """
        재생목록별 디렉토리 경로 반환
        
        Args:
            playlist_title: 재생목록 제목
            
        Returns:
            재생목록별 디렉토리 경로
        """
        playlist_dir_name = self.sanitize_filename(playlist_title)
        playlist_dir = self.base_output_dir / playlist_dir_name
        playlist_dir.mkdir(parents=True, exist_ok=True)
        return playlist_dir
    
    def sanitize_filename(self, filename: str) -> str:
        """
        파일명에서 사용할 수 없는 문자 제거
        
        Args:
            filename: 원본 파일명
            
        Returns:
            정제된 파일명
        """
        # 파일명에 사용할 수 없는 문자 제거
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # 길이 제한 (확장자 제외)
        max_length = 200
        if len(filename) > max_length:
            filename = filename[:max_length]
        
        return filename.strip()
    
    @abstractmethod
    def export(self, playlist_data: Dict) -> Path:
        """
        재생목록 데이터를 파일로 출력
        
        Args:
            playlist_data: 재생목록 정보와 영상 리스트
            
        Returns:
            생성된 파일 경로
        """
        pass
    
    @abstractmethod
    def get_file_extension(self) -> str:
        """
        파일 확장자 반환
        
        Returns:
            파일 확장자 (예: '.json', '.md', '.html')
        """
        pass

