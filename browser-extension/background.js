/**
 * Background Service Worker
 * 확장 프로그램의 백그라운드 작업 처리
 */

chrome.runtime.onInstalled.addListener(() => {
    console.log('YouTube 재생목록 추출기 설치됨');
});

// 필요 시 백그라운드 작업 추가

