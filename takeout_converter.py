"""
Google Takeout CSV 파일을 JSON, Markdown, HTML 형식으로 변환
"""
import argparse
import sys
from pathlib import Path
from takeout_parser import TakeoutParser
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
        description="Google Takeout CSV 파일을 JSON, Markdown, HTML 형식으로 변환합니다."
    )
    parser.add_argument(
        '--takeout-dir',
        type=str,
        required=True,
        help='Takeout 데이터 디렉토리 경로 (예: takeout_data/251216/Takeout 2/YouTube 및 YouTube Music/재생목록/)'
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
        '--enrich',
        action='store_true',
        help='YouTube API를 사용하여 영상 상세 정보 가져오기 (선택사항, API 키 필요)'
    )
    
    args = parser.parse_args()
    
    # 출력 디렉토리 설정
    # 기본값: ./output_takeout (Takeout 데이터와 API 데이터 구분)
    if args.output_dir:
        config.OUTPUT_DIR = Path(args.output_dir)
    else:
        # 기본값을 output_takeout으로 설정하여 API 기반 추출과 구분
        config.OUTPUT_DIR = Path("./output_takeout")
    
    # Takeout 디렉토리 확인
    takeout_dir = Path(args.takeout_dir)
    if not takeout_dir.exists():
        print(f"오류: Takeout 디렉토리를 찾을 수 없습니다: {takeout_dir}")
        sys.exit(1)
    
    # 출력 형식 파싱
    output_formats = [f.strip() for f in args.format.split(',')]
    exporters = get_exporters(output_formats)
    
    if not exporters:
        print("오류: 유효한 출력 형식이 없습니다.")
        sys.exit(1)
    
    try:
        # Takeout 파서 초기화
        print(f"Takeout 데이터 디렉토리: {takeout_dir.absolute()}")
        takeout_parser = TakeoutParser(takeout_dir)
        
        # 재생목록 및 영상 정보 파싱
        playlists_data = takeout_parser.get_all_playlists_with_videos()
        
        # YouTube API로 정보 보강 (선택사항)
        youtube_api = None
        if args.enrich:
            print("\nYouTube API로 영상 정보 보강 중...")
            try:
                from youtube_api import YouTubeAPI
                youtube_api = YouTubeAPI()
                # TODO: 영상 정보 보강 로직 구현
                print("⚠️  영상 정보 보강 기능은 아직 구현되지 않았습니다.")
            except Exception as e:
                print(f"⚠️  YouTube API 초기화 실패: {e}")
                print("기본 정보만으로 진행합니다.")
        
        # 파일 출력
        print(f"\n{len(playlists_data)}개의 재생목록을 {len(exporters)}가지 형식으로 저장 중...\n")
        
        total_files = 0
        for playlist_data in playlists_data:
            for exporter in exporters:
                try:
                    filepath = exporter.export(playlist_data)
                    total_files += 1
                    print(f"  ✓ {filepath.parent.name}/{filepath.name} 저장 완료")
                except Exception as e:
                    print(f"  ✗ {playlist_data['title']} ({exporter.get_file_extension()}) 저장 실패: {e}")
        
        print(f"\n{'='*50}")
        print(f"완료! 총 {len(playlists_data)}개 재생목록, {total_files}개 파일이 생성되었습니다.")
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

