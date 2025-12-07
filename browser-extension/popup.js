/**
 * Popup 스크립트
 */

let extractedVideos = [];

// DOM 요소
const statusDiv = document.getElementById('status');
const progressDiv = document.getElementById('progress');
const extractBtn = document.getElementById('extractBtn');
const downloadButtons = document.getElementById('downloadButtons');
const downloadJsonBtn = document.getElementById('downloadJson');
const downloadMarkdownBtn = document.getElementById('downloadMarkdown');
const downloadHtmlBtn = document.getElementById('downloadHtml');

// 상태 업데이트
function updateStatus(message, type = 'info') {
    statusDiv.textContent = message;
    statusDiv.className = `status ${type}`;
}

// 진행 상황 업데이트
function updateProgress(message) {
    progressDiv.textContent = message;
    progressDiv.style.display = message ? 'block' : 'none';
}

// 추출 시작
extractBtn.addEventListener('click', async () => {
    extractBtn.disabled = true;
    updateStatus('추출 중...', 'info');
    updateProgress('영상 정보를 수집하고 있습니다...');
    downloadButtons.style.display = 'none';

    try {
        // 현재 활성 탭 가져오기
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        
        // Content Script에 메시지 전송
        chrome.tabs.sendMessage(tab.id, { action: 'extractWatchLater' }, (response) => {
            if (chrome.runtime.lastError) {
                updateStatus('오류: ' + chrome.runtime.lastError.message, 'error');
                extractBtn.disabled = false;
                return;
            }

            if (response.success) {
                extractedVideos = response.videos;
                updateStatus(`✓ ${response.count}개의 영상을 추출했습니다!`, 'success');
                updateProgress('');
                downloadButtons.style.display = 'block';
            } else {
                updateStatus('오류: ' + response.error, 'error');
            }
            extractBtn.disabled = false;
        });
    } catch (error) {
        updateStatus('오류: ' + error.message, 'error');
        extractBtn.disabled = false;
    }
});

// JSON 다운로드
downloadJsonBtn.addEventListener('click', () => {
    const data = {
        playlist_id: 'WL',
        title: '나중에 볼 동영상 (Watch Later)',
        video_count: extractedVideos.length,
        videos: extractedVideos
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = '나중에 볼 동영상 (Watch Later).json';
    a.click();
    URL.revokeObjectURL(url);
});

// Markdown 다운로드
downloadMarkdownBtn.addEventListener('click', () => {
    let markdown = `# 나중에 볼 동영상 (Watch Later)\n\n`;
    markdown += `**영상 개수:** ${extractedVideos.length}\n\n`;
    markdown += `---\n\n`;
    markdown += `## 영상 목록\n\n`;
    
    extractedVideos.forEach((video, idx) => {
        markdown += `${idx + 1}. [${video.title}](${video.url})\n`;
        if (video.channel_title) {
            markdown += `   - 채널: ${video.channel_title}\n`;
        }
        markdown += `\n`;
    });
    
    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = '나중에 볼 동영상 (Watch Later).md';
    a.click();
    URL.revokeObjectURL(url);
});

// HTML 다운로드 (Python 버전과 동일한 형식)
downloadHtmlBtn.addEventListener('click', () => {
    // Python의 HTML 템플릿과 동일한 형식 생성
    const html = generateHtml(extractedVideos);
    
    const blob = new Blob([html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = '나중에 볼 동영상 (Watch Later).html';
    a.click();
    URL.revokeObjectURL(url);
});

// HTML 생성 (Python 버전과 동일한 스타일)
function generateHtml(videos) {
    return `<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>나중에 볼 동영상 (Watch Later)</title>
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
        <h1>나중에 볼 동영상 (Watch Later)</h1>
        <div class="playlist-info">
            <div class="video-count">총 ${videos.length}개의 영상</div>
        </div>
        
        <div class="videos-grid">
            ${videos.map(video => `
            <div class="video-card">
                <a href="${video.url}" target="_blank">
                    <img src="${video.thumbnail || 'https://via.placeholder.com/320x180?text=No+Thumbnail'}" 
                         alt="${video.title}" class="video-thumbnail" 
                         onerror="this.src='https://via.placeholder.com/320x180?text=No+Thumbnail'">
                </a>
                <div class="video-info">
                    <div class="video-title">
                        <a href="${video.url}" target="_blank">${escapeHtml(video.title)}</a>
                    </div>
                    ${video.channel_title ? `<div class="video-meta video-channel">채널: ${escapeHtml(video.channel_title)}</div>` : ''}
                </div>
            </div>
            `).join('')}
        </div>
    </div>
</body>
</html>`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

