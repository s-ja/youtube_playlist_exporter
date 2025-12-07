"""
YouTube 재생목록 추출 메인 실행 파일
"""
import argparse
import sys
from pathlib import Path
from youtube_api import YouTubeAPI
from playlist_extractor import PlaylistExtractor
from exporters.json_exporter import JSONExporter
from exporters.markdown_exporter import MarkdownExporter
from exporters.html_exporter import HTMLExporter
import config


def get_exporters(output_formats: list) -> list:
    """
    출력 형식에 맞는 Exporter 인스턴스 리스트 반환
    
    Args:
        output_formats: 출력 형식 리스트 ('json', 'markdown', 'html')
        
    Returns:
        Exporter 인스턴스 리스트
    """
    exporters = []
    output_dir = config.OUTPUT_DIR
    
    for fmt in output_formats:
        fmt = fmt.strip().lower()
        if fmt == 'json':
            exporters.append(JSONExporter(output_dir))
        elif fmt == 'markdown' or fmt == 'md':
            exporters.append(MarkdownExporter(output_dir))
        elif fmt == 'html':
            exporters.append(HTMLExporter(output_dir))
        else:
            print(f"경고: 알 수 없는 출력 형식 '{fmt}'는 무시됩니다.")
    
    return exporters


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="YouTube 재생목록을 추출하여 JSON, Markdown, HTML 형식으로 저장합니다."
    )
    parser.add_argument(
        '--playlist-id',
        type=str,
        help='특정 재생목록 ID만 추출 (지정하지 않으면 모든 재생목록 추출)'
    )
    parser.add_argument(
        '--format',
        type=str,
        default=','.join(config.OUTPUT_FORMATS),
        help='출력 형식 (쉼표로 구분: json,markdown,html)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        help='출력 디렉토리 경로 (기본값: ./output)'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=5,
        help='병렬 처리 워커 수 (기본값: 5)'
    )
    parser.add_argument(
        '--api-key',
        type=str,
        help='YouTube API 키 (선택사항, OAuth 2.0이 기본값이며 권장됩니다)'
    )
    
    args = parser.parse_args()
    
    # 출력 디렉토리 설정
    if args.output_dir:
        config.OUTPUT_DIR = Path(args.output_dir)
    
    # 출력 형식 파싱
    output_formats = [f.strip() for f in args.format.split(',')]
    exporters = get_exporters(output_formats)
    
    if not exporters:
        print("오류: 유효한 출력 형식이 없습니다.")
        sys.exit(1)
    
    # YouTube API 초기화
    print("YouTube API 초기화 중...")
    youtube_api = YouTubeAPI(api_key=args.api_key)
    
    # 재생목록 추출기 초기화
    extractor = PlaylistExtractor(youtube_api, max_workers=args.workers)
    
    try:
        # 재생목록 추출 및 파일 출력
        if args.playlist_id:
            print(f"재생목록 ID '{args.playlist_id}' 추출 중...")
            playlist_data = extractor.extract_single_playlist(args.playlist_id)
            playlists_data = [playlist_data]
            
            # 파일 출력
            print(f"\n재생목록을 {len(exporters)}가지 형식으로 저장 중...")
            total_files = 0
            for exporter in exporters:
                try:
                    filepath = exporter.export(playlist_data)
                    total_files += 1
                    print(f"  ✓ {filepath.name} 생성 완료")
                except Exception as e:
                    print(f"  ✗ {playlist_data['title']} ({exporter.get_file_extension()}) 저장 실패: {e}")
            
            print(f"\n완료! 총 {total_files}개의 파일이 생성되었습니다.")
            print(f"출력 디렉토리: {config.OUTPUT_DIR.absolute()}")
        else:
            print("모든 재생목록 추출 및 저장 중...")
            print(f"({len(exporters)}가지 형식으로 각 재생목록 저장)\n")
            
            total_files = 0
            total_playlists = 0
            
            # 재생목록을 하나씩 추출하고 즉시 저장
            playlists = extractor.youtube_api.get_all_playlists()
            print(f"총 {len(playlists)}개의 재생목록을 찾았습니다.\n")
            
            for idx, playlist in enumerate(playlists, 1):
                try:
                    print(f"[{idx}/{len(playlists)}] {playlist['title']} 처리 중...")
                    videos = extractor._extract_playlist_videos(playlist)
                    playlist_data = {
                        **playlist,
                        "videos": videos
                    }
                    print(f"✓ {playlist['title']}: {len(videos)}개 영상 추출 완료")
                    
                    # 즉시 파일 저장
                    for exporter in exporters:
                        try:
                            filepath = exporter.export(playlist_data)
                            total_files += 1
                            print(f"  → {filepath.parent.name}/{filepath.name} 저장 완료")
                        except Exception as e:
                            print(f"  ✗ {playlist['title']} ({exporter.get_file_extension()}) 저장 실패: {e}")
                    
                    total_playlists += 1
                    print()
                    
                except Exception as e:
                    print(f"✗ {playlist['title']} 추출 실패: {e}\n")
            
            print(f"\n{'='*50}")
            print(f"완료! 총 {total_playlists}개 재생목록, {total_files}개 파일이 생성되었습니다.")
            print(f"출력 디렉토리: {config.OUTPUT_DIR.absolute()}")
        
    except KeyboardInterrupt:
        print("\n\n작업이 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

