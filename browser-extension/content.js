/**
 * YouTube Watch Later 재생목록 추출기
 * Content Script - YouTube 페이지에 주입됨
 */

(function() {
    'use strict';

    // Watch Later 페이지인지 확인
    function isWatchLaterPage() {
        const urlParams = new URLSearchParams(window.location.search);
        const listParam = urlParams.get('list');
        return listParam === 'WL' || window.location.pathname.includes('/playlist') && listParam?.startsWith('WL');
    }

    // 영상 정보 추출
    function extractVideoInfo(videoElement) {
        try {
            // YouTube의 DOM 구조에 따라 셀렉터 조정 필요
            const titleElement = videoElement.querySelector('#video-title, a#video-title');
            const linkElement = videoElement.querySelector('a[href*="/watch"]');
            const thumbnailElement = videoElement.querySelector('img');
            const channelElement = videoElement.querySelector('#channel-name a, #text-container a');
            
            if (!titleElement || !linkElement) {
                return null;
            }

            const videoUrl = linkElement.href.split('&')[0]; // 쿼리 파라미터 제거
            const videoId = new URL(videoUrl).searchParams.get('v');

            return {
                video_id: videoId,
                title: titleElement.textContent.trim(),
                url: videoUrl,
                thumbnail: thumbnailElement?.src || thumbnailElement?.getAttribute('src') || '',
                channel_title: channelElement?.textContent?.trim() || '',
                added_at: '' // Watch Later에는 추가일 정보가 없을 수 있음
            };
        } catch (error) {
            console.error('영상 정보 추출 오류:', error);
            return null;
        }
    }

    // 모든 영상 수집 (무한 스크롤 처리)
    async function collectAllVideos() {
        const videos = [];
        const processedIds = new Set();
        let lastVideoCount = 0;
        let noChangeCount = 0;

        // 스크롤하여 모든 영상 로드
        while (noChangeCount < 3) {
            // 현재 페이지의 모든 영상 요소 찾기
            const videoElements = document.querySelectorAll(
                'ytd-playlist-video-renderer, ytd-playlist-video-list-renderer #content'
            );

            let newVideosFound = 0;

            videoElements.forEach(element => {
                const videoInfo = extractVideoInfo(element);
                if (videoInfo && !processedIds.has(videoInfo.video_id)) {
                    videos.push(videoInfo);
                    processedIds.add(videoInfo.video_id);
                    newVideosFound++;
                }
            });

            // 새 영상이 없으면 카운트 증가
            if (videos.length === lastVideoCount) {
                noChangeCount++;
            } else {
                noChangeCount = 0;
            }

            lastVideoCount = videos.length;

            // 페이지 하단으로 스크롤
            window.scrollTo(0, document.documentElement.scrollHeight);
            
            // 다음 영상 로드를 기다림
            await new Promise(resolve => setTimeout(resolve, 2000));
        }

        return videos;
    }

    // 메시지 리스너
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
        if (request.action === 'extractWatchLater') {
            if (!isWatchLaterPage()) {
                sendResponse({
                    success: false,
                    error: 'Watch Later 페이지가 아닙니다. https://www.youtube.com/playlist?list=WL 페이지를 열어주세요.'
                });
                return;
            }

            collectAllVideos()
                .then(videos => {
                    sendResponse({
                        success: true,
                        videos: videos,
                        count: videos.length
                    });
                })
                .catch(error => {
                    sendResponse({
                        success: false,
                        error: error.message
                    });
                });

            return true; // 비동기 응답
        }
    });

    // 페이지 로드 완료 후 초기화
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            console.log('YouTube 재생목록 추출기 로드됨');
        });
    } else {
        console.log('YouTube 재생목록 추출기 로드됨');
    }
})();

