document.addEventListener('DOMContentLoaded', () => {
    const convertForm = document.getElementById('convertForm');
    const actionArea = document.getElementById('actionArea');
    const progressArea = document.getElementById('progressArea');
    const aiAssistantArea = document.getElementById('aiAssistantArea');
    const resultBanner = document.getElementById('resultBanner');
    const playNowBtn = document.querySelector('.play-btn');
    const globalAudioPlayer = document.getElementById('globalAudioPlayer');
    const playerTitle = document.getElementById('playerTitle');
    const playerPlayBtn = document.getElementById('playerPlayBtn');
    const closePlayerBtn = document.getElementById('closePlayerBtn');
    const progressFill = document.querySelector('.progress-bar-fill');
    const progressThumb = document.querySelector('.progress-bar-thumb');
    const progressContainer = document.querySelector('.progress-bar-container');
    const currentTimeEl = document.querySelector('.time-current');
    const totalTimeEl = document.querySelector('.time-total');

    const CONTENT_SERVICE = 'http://192.168.0.100:8001';
    const PROCESS_SERVICE = 'http://192.168.0.100:8000';
    const TTS_SERVICE     = 'http://192.168.0.100:8010';

    let currentAudio = null;
    let currentAudioUrl = null;
    let articleTitle = '';

    const convertBtn = document.getElementById('convertBtn');
    if (convertBtn) {
        convertBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            const url = document.getElementById('articleUrl').value.trim();
            const language = document.getElementById('outputLanguage').value;
            const voice = document.getElementById('voiceProfile').value;
            if (!url || !language || !voice) {
                alert('Vui lòng điền đủ URL, chọn ngôn ngữ và giọng đọc.');
                return;
            }

            // Disable button to prevent multiple clicks
            convertBtn.disabled = true;
            convertBtn.innerText = "Processing...";

            actionArea.classList.add('hidden');
            progressArea.classList.remove('hidden');

            try {
                await runPipeline(url, language, voice);
            } catch (err) {
                console.error("Pipeline Error:", err);
                actionArea.classList.remove('hidden');
                progressArea.classList.add('hidden');
                alert(`Lỗi: ${err.message}`);
            } finally {
                convertBtn.disabled = false;
                convertBtn.innerText = "Generate Podcast";
            }
        });
    }

    if (playNowBtn) {
        playNowBtn.addEventListener('click', () => {
            playCurrentPodcast();
        });
    }

    if (playerPlayBtn) {
        playerPlayBtn.addEventListener('click', () => {
            if (!currentAudio) return;

            if (currentAudio.paused) {
                currentAudio.play();
            } else {
                currentAudio.pause();
            }
        });
    }

    if (closePlayerBtn) {
        closePlayerBtn.addEventListener('click', () => {
            if (currentAudio) {
                currentAudio.pause();
                currentAudio.currentTime = 0;
            }
            globalAudioPlayer.classList.add('hidden');
            updatePlayIcon(false);
            updateProgress(0, 0);
        });
    }

    if (progressContainer) {
        progressContainer.addEventListener('click', (e) => {
            if (!currentAudio || !currentAudio.duration) return;

            const rect = progressContainer.getBoundingClientRect();
            const ratio = Math.min(Math.max((e.clientX - rect.left) / rect.width, 0), 1);
            currentAudio.currentTime = ratio * currentAudio.duration;
        });
    }

    async function runPipeline(url, language, voice) {
        // Step 0 — Crawl
        activateStep(0);
        const crawlRes = await fetch(`${CONTENT_SERVICE}/crawl`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        if (!crawlRes.ok) throw new Error('Content service error');
        const crawlData = await crawlRes.json();
        const rawText = crawlData.text;
        articleTitle = crawlData.title || 'Generated Podcast';
        completeStep(0);

        // Step 1 — AI Processing
        activateStep(1);
        const processRes = await fetch(`${PROCESS_SERVICE}/process`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: rawText, language })
        });
        if (!processRes.ok) throw new Error('Process service error');
        const processData = await processRes.json();
        const ttsText = processData.script;

        const articleTextEl = document.querySelector('.article-text');
        if (articleTextEl && processData.summary) {
            articleTextEl.innerHTML = '';
            const summaryParagraph = document.createElement('p');
            summaryParagraph.textContent = processData.summary;
            articleTextEl.appendChild(summaryParagraph);
        }
        completeStep(1);

        // Step 2 — TTS
        activateStep(2);
        
        let cleanTtsText = ttsText ? ttsText.toString().trim() : "";
        console.log("TTS Payload Size:", cleanTtsText.length, "characters");

        const ttsRes = await fetch(`${TTS_SERVICE}/tts`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                text: "Xin chào, đây là bài test siêu ngắn để kiểm tra đường truyền.", 
                language: language, 
                voice: voice 
            })
        });

        if (!ttsRes.ok) {
            const errorBody = await ttsRes.text();
            throw new Error(`TTS Service error (${ttsRes.status}): ${errorBody}`);
        }

        const ttsData = await ttsRes.json();
        currentAudioUrl = `${TTS_SERVICE}${ttsData.audio_url}`;
        prepareAudio(currentAudioUrl);
        completeStep(2);

        resultBanner.classList.remove('hidden-banner');
        aiAssistantArea.classList.remove('hidden');
    }

    function prepareAudio(audioUrl) {
        if (currentAudio) {
            currentAudio.pause();
        }

        currentAudio = new Audio(audioUrl);
        currentAudio.preload = 'metadata';

        currentAudio.addEventListener('loadedmetadata', () => {
            updateProgress(currentAudio.currentTime, currentAudio.duration);
            updateDurationText(currentAudio.duration);
        });

        currentAudio.addEventListener('timeupdate', () => {
            updateProgress(currentAudio.currentTime, currentAudio.duration);
        });

        currentAudio.addEventListener('play', () => {
            updatePlayIcon(true);
        });

        currentAudio.addEventListener('pause', () => {
            updatePlayIcon(false);
        });

        currentAudio.addEventListener('ended', () => {
            updatePlayIcon(false);
            updateProgress(currentAudio.duration || 0, currentAudio.duration || 0);
        });
    }

    function playCurrentPodcast() {
        if (!currentAudioUrl) {
            alert('Chưa có file audio để phát. Vui lòng convert bài viết trước.');
            return;
        }

        if (!currentAudio) {
            prepareAudio(currentAudioUrl);
        }

        if (playerTitle) {
            playerTitle.textContent = articleTitle || 'Generated Podcast';
        }

        globalAudioPlayer.classList.remove('hidden');
        currentAudio.play().catch((err) => {
            console.error(err);
            alert('Không thể phát audio. Vui lòng kiểm tra file âm thanh hoặc service TTS.');
        });
    }

    function updatePlayIcon(isPlaying) {
        if (!playerPlayBtn) return;

        const icon = playerPlayBtn.querySelector('i');
        if (!icon) return;

        icon.className = isPlaying ? 'fas fa-pause' : 'fas fa-play';
    }

    function updateProgress(currentSeconds, totalSeconds) {
        const safeTotal = Number.isFinite(totalSeconds) && totalSeconds > 0 ? totalSeconds : 0;
        const safeCurrent = Number.isFinite(currentSeconds) ? currentSeconds : 0;
        const percent = safeTotal ? Math.min((safeCurrent / safeTotal) * 100, 100) : 0;

        if (progressFill) progressFill.style.width = `${percent}%`;
        if (progressThumb) progressThumb.style.left = `${percent}%`;
        if (currentTimeEl) currentTimeEl.textContent = formatTime(safeCurrent);
        if (totalTimeEl) totalTimeEl.textContent = safeTotal ? formatTime(safeTotal) : '0:00';
    }

    function updateDurationText(duration) {
        const durationText = Number.isFinite(duration) && duration > 0 ? formatTime(duration) : '0:00';
        const resultDuration = resultBanner ? resultBanner.querySelector('.result-text p') : null;

        if (resultDuration) resultDuration.textContent = `Duration: ${durationText}`;
        if (totalTimeEl) totalTimeEl.textContent = durationText;
    }

    function formatTime(seconds) {
        const totalSeconds = Math.floor(seconds || 0);
        const minutes = Math.floor(totalSeconds / 60);
        const remainingSeconds = totalSeconds % 60;
        return `${minutes}:${String(remainingSeconds).padStart(2, '0')}`;
    }

    function activateStep(index) {
        const step = document.getElementById(`step-${index}`);
        if (step) step.classList.add('active');
    }

    function completeStep(index) {
        const step = document.getElementById(`step-${index}`);
        if (step) {
            step.classList.remove('active');
            step.classList.add('completed');
        }
    }
});
