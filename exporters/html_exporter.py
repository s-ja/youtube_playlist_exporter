"""
HTML 형식 출력 모듈 (썸네일 포함)
"""
from pathlib import Path
from typing import Dict
from jinja2 import Template
from exporters.base_exporter import BaseExporter


class HTMLExporter(BaseExporter):
    """HTML 형식으로 재생목록 데이터 출력 (썸네일 포함)"""
    
    HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ playlist_title }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #1a1a1a;
            margin-bottom: 10px;
            font-size: 2em;
        }
        .playlist-info {
            color: #666;
            margin-bottom: 20px;
            padding-bottom: 20px;
            border-bottom: 2px solid #eee;
        }
        .playlist-description {
            margin: 15px 0;
            color: #555;
        }
        .video-count {
            font-weight: 600;
            color: #d32f2f;
        }
        .videos-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .video-card {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
            transition: transform 0.2s, box-shadow 0.2s;
            background: white;
        }
        .video-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .video-thumbnail {
            width: 100%;
            height: 180px;
            object-fit: cover;
            display: block;
        }
        .video-info {
            padding: 15px;
        }
        .video-title {
            font-weight: 600;
            margin-bottom: 8px;
            font-size: 0.95em;
            line-height: 1.4;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        .video-title a {
            color: #1a1a1a;
            text-decoration: none;
        }
        .video-title a:hover {
            color: #d32f2f;
        }
        .video-meta {
            font-size: 0.85em;
            color: #666;
            margin-top: 8px;
        }
        .video-channel {
            margin-top: 5px;
        }
        @media (max-width: 768px) {
            .videos-grid {
                grid-template-columns: 1fr;
            }
            .container {
                padding: 15px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ playlist_title }}</h1>
        <div class="playlist-info">
            {% if playlist_description %}
            <div class="playlist-description">{{ playlist_description }}</div>
            {% endif %}
            <div class="video-count">총 {{ video_count }}개의 영상</div>
            {% if published_at %}
            <div style="margin-top: 5px; color: #999; font-size: 0.9em;">생성일: {{ published_at }}</div>
            {% endif %}
        </div>
        
        <div class="videos-grid">
            {% for video in videos %}
            <div class="video-card">
                <a href="{{ video.url }}" target="_blank">
                    <img src="{{ video.thumbnail }}" alt="{{ video.title }}" class="video-thumbnail" 
                         onerror="this.src='https://via.placeholder.com/320x180?text=No+Thumbnail'">
                </a>
                <div class="video-info">
                    <div class="video-title">
                        <a href="{{ video.url }}" target="_blank">{{ video.title }}</a>
                    </div>
                    {% if video.channel_title %}
                    <div class="video-meta video-channel">채널: {{ video.channel_title }}</div>
                    {% endif %}
                    {% if video.added_at %}
                    <div class="video-meta">추가일: {{ video.added_at[:10] }}</div>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""
    
    def export(self, playlist_data: Dict) -> Path:
        """
        재생목록 데이터를 HTML 파일로 출력
        
        Args:
            playlist_data: 재생목록 정보와 영상 리스트
            
        Returns:
            생성된 파일 경로
        """
        # 재생목록별 폴더 생성
        playlist_dir = self.get_playlist_dir(playlist_data["title"])
        filename = self.sanitize_filename(playlist_data["title"])
        filepath = playlist_dir / f"{filename}.html"
        
        template = Template(self.HTML_TEMPLATE)
        html_content = template.render(
            playlist_title=playlist_data["title"],
            playlist_description=playlist_data.get("description", ""),
            video_count=len(playlist_data["videos"]),
            published_at=playlist_data.get("published_at", ""),
            videos=playlist_data["videos"]
        )
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filepath
    
    def get_file_extension(self) -> str:
        return ".html"

