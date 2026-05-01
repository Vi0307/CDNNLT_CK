document.addEventListener('DOMContentLoaded', () => {
    const convertForm = document.getElementById('convertForm');
    const actionArea = document.getElementById('actionArea');
    const progressArea = document.getElementById('progressArea');
    const aiAssistantArea = document.getElementById('aiAssistantArea');
    const resultBanner = document.getElementById('resultBanner');

    const CONTENT_SERVICE = 'http://localhost:8001';
    const PROCESS_SERVICE = 'http://localhost:8000';
    const TTS_SERVICE     = 'http://localhost:8002';

    // Holds real audio state
    let currentAudio = null;
    let currentAudioUrl = null;
    let articleTitle = '';

    // ── Form Submit ───────────────────────────────────────────────────────────
    if (convertForm) {
        convertForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const url      = document.getElementById('articleUrl').value.trim();
            const language = document.getElementById('outputLanguage').value;
            if (!url || !language) return;

            actionArea.classList.add('hidden');
            progressArea.classList.remove('hidden');

            try {
                await runPipeline(url, language);
            } catch (err) {
                console.error(err);
                actionArea.classList.remove('hidden');
                progressArea.classList.add('hidden');
                alert(`Lỗi: ${err.message}`);
            }
        });
    }

    // ── Pipeline ──────────────────────────────────────────────────────────────
    async function runPipeline(url, language) {

        // Step 0 — Crawl
        activateStep(0);
        const crawlRes = await fetch(`${CONTENT_SERVICE}/crawl`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        if (!crawlRes.ok) {
            const e = await crawlRes.json().catch(() => ({}));
            throw new Error(e.detail || `Content service: ${crawlRes.status}`);
        }
        const crawlData = await crawlRes.json();
        // CrawlResponse: { url, title, text, word_count, is_mock }
        const rawText = crawlData.text;
        articleTitle  = crawlData.title || 'Generated Podcast';
        completeStep(0);

        // Step 1 — AI Processing (process-service)
        activateStep(1);
        const processRes = await fetch(`${PROCESS_SERVICE}/process`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: rawText, language })
        });
        if (!processRes.ok) {
            const e = await processRes.json().catch(() => ({}));
            throw new Error(e.detail || `Process service: ${processRes.status}`);
        }
        const processData = await processRes.json();
        // ProcessResponse: { request_id, summary, script, status, language }
        const ttsText = processData.script || processData.summary || rawText;

        // Populate Explain tab with the summary
        const articleTextEl = document.querySelector('.article-text');
        if (articleTextEl && processData.summary) {
            articleTextEl.innerHTML = processData.summary
                .split('\n')
                .filter(p => p.trim())
                .map(p => `<p>${p}</p>`)
                .join('');
        }
        completeStep(1);

        // Step 2 — TTS
        activateStep(2);
        const ttsRes = await fetch(`${TTS_SERVICE}/tts`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: ttsText, language })
        });
        if (!ttsRes.ok) {
            const e = await ttsRes.json().catch(() => ({}));
            throw new Error(e.detail || `TTS service: ${ttsRes.status}`);
        }
        const ttsData = await ttsRes.json();
        // TTSResponse: { status, audio_url, message }  audio_url = "/download/<uuid>.mp3"
        currentAudioUrl = `${TTS_SERVICE}${ttsData.audio_url}`;
        completeStep(2);

        // Update player title
        const playerTitleEl = document.getElementById('playerTitle');
        if (playerTitleEl) playerTitleEl.textContent = articleTitle;

        // Show result banner
        resultBanner.classList.remove('hidden-banner');
        resultBanner.classList.add('fade-in');

        // Pre-load audio to get real duration
        const tempAudio = new Audio(currentAudioUrl);
        tempAudio.addEventListener('loadedmetadata', () => {
            const dur = Math.round(tempAudio.duration);
            const m = Math.floor(dur / 60);
            const s = (dur % 60).toString().padStart(2, '0');
            const durationEl = resultBanner.querySelector('.result-text p');
            if (durationEl) durationEl.textContent = `Duration: ${m}:${s}`;
            document.querySelector('.time-total').textContent = `${m}:${s}`;
        });

        // Show AI assistant
        setTimeout(() => {
            aiAssistantArea.classList.remove('hidden');
            aiAssistantArea.classList.add('fade-in');
        }, 500);
    }

    // ── Step helpers ──────────────────────────────────────────────────────────
    function activateStep(index) {
        const step = document.getElementById(`step-${index}`);
        if (!step) return;
        step.classList.add('active');
        const icon = step.querySelector('.step-icon i');
        if (icon) icon.className = 'fas fa-spinner fa-spin';
    }

    function completeStep(index) {
        const step = document.getElementById(`step-${index}`);
        if (!step) return;
        step.classList.remove('active');
        step.classList.add('completed');
        const icon = step.querySelector('.step-icon i');
        if (icon) icon.className = 'fas fa-check';
        const line = document.getElementById(`line-${index}`);
        if (line) line.classList.add('completed-line');
    }

    // ── Tab Switching ─────────────────────────────────────────────────────────
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            const target = document.getElementById(`tab-${tab.getAttribute('data-tab')}`);
            if (target) target.classList.add('active');
        });
    });

    // ── Explain Popup ─────────────────────────────────────────────────────────
    const articleTextContainer = document.querySelector('.article-text');
    const explainPopup    = document.getElementById('explainPopup');
    const popupSelectedText = document.getElementById('popupSelectedText');
    const closePopupBtn   = document.getElementById('closePopupBtn');
    const explainTermBtn  = document.getElementById('explainTermBtn');
    const explanationText = document.getElementById('explanationText');

    function hidePopup() {
        explainPopup.classList.remove('show');
        setTimeout(() => {
            if (!explainPopup.classList.contains('show')) explainPopup.classList.add('hidden');
        }, 200);
    }

    if (articleTextContainer && explainPopup) {
        document.addEventListener('mouseup', (e) => {
            const explainTab = document.getElementById('tab-explain');
            if (!explainTab?.classList.contains('active')) return;
            if (explainPopup.contains(e.target)) return;

            const selection = window.getSelection();
            const selectedText = selection.toString().trim();

            if (selectedText.length > 0 && articleTextContainer.contains(selection.anchorNode)) {
                const rect = selection.getRangeAt(0).getBoundingClientRect();
                explainPopup.style.left = `${Math.max(10, rect.left + window.scrollX + rect.width / 2 - 160)}px`;
                explainPopup.style.top  = `${rect.bottom + window.scrollY + 10}px`;
                popupSelectedText.textContent = `"${selectedText}"`;
                explainTermBtn.classList.remove('hidden');
                explanationText.classList.add('hidden');
                explanationText.innerHTML = '';
                explainPopup.classList.remove('hidden');
                setTimeout(() => explainPopup.classList.add('show'), 10);
            } else {
                hidePopup();
            }
        });

        closePopupBtn.addEventListener('click', () => {
            hidePopup();
            window.getSelection().removeAllRanges();
        });

        explainTermBtn.addEventListener('click', () => {
            explainTermBtn.classList.add('hidden');
            explanationText.classList.remove('hidden');
            explanationText.innerHTML = `<i class="fas fa-spinner fa-spin" style="margin-right:8px"></i> Generating explanation...`;
            setTimeout(() => {
                const term = popupSelectedText.textContent.replace(/"/g, '');
                explanationText.innerHTML = `<strong>"${term}"</strong> — This term refers to a concept discussed in the article. In this context, it describes a key aspect of the topic being covered, relating to how modern systems process and transform content efficiently.`;
            }, 1000);
        });
    }

    // ── Audio Player ──────────────────────────────────────────────────────────
    const playBtn           = document.querySelector('.play-btn');
    const globalAudioPlayer = document.getElementById('globalAudioPlayer');
    const closePlayerBtn    = document.getElementById('closePlayerBtn');
    const playerPlayBtn     = document.getElementById('playerPlayBtn');
    const progressBarFill   = document.querySelector('.progress-bar-fill');
    const progressBarThumb  = document.querySelector('.progress-bar-thumb');
    const progressBarContainer = document.querySelector('.progress-bar-container');
    const timeCurrent       = document.querySelector('.time-current');
    const timeTotal         = document.querySelector('.time-total');

    function getAudio() {
        if (!currentAudio || currentAudio.src !== currentAudioUrl) {
            if (currentAudio) currentAudio.pause();
            currentAudio = new Audio(currentAudioUrl);

            currentAudio.addEventListener('timeupdate', () => {
                const dur = currentAudio.duration || 0;
                if (!dur) return;
                const cur = currentAudio.currentTime;
                const pct = (cur / dur) * 100;
                progressBarFill.style.width  = `${pct}%`;
                progressBarThumb.style.left  = `${pct}%`;
                const m = Math.floor(cur / 60);
                const s = Math.floor(cur % 60).toString().padStart(2, '0');
                timeCurrent.textContent = `${m}:${s}`;
            });

            currentAudio.addEventListener('loadedmetadata', () => {
                const dur = currentAudio.duration;
                const m = Math.floor(dur / 60);
                const s = Math.floor(dur % 60).toString().padStart(2, '0');
                timeTotal.textContent = `${m}:${s}`;
            });

            currentAudio.addEventListener('ended', () => {
                playerPlayBtn.querySelector('i').className = 'fas fa-play';
                if (playBtn) playBtn.innerHTML = '<i class="fas fa-play-circle"></i> Play Now';
            });
        }
        return currentAudio;
    }

    // Seek
    if (progressBarContainer) {
        progressBarContainer.addEventListener('click', (e) => {
            if (!currentAudio) return;
            const rect = progressBarContainer.getBoundingClientRect();
            currentAudio.currentTime = ((e.clientX - rect.left) / rect.width) * currentAudio.duration;
        });
    }

    function setPlayingUI(playing) {
        playerPlayBtn.querySelector('i').className = playing ? 'fas fa-pause' : 'fas fa-play';
        if (playBtn) playBtn.innerHTML = playing
            ? '<i class="fas fa-pause-circle"></i> Playing...'
            : '<i class="fas fa-play-circle"></i> Play Now';
    }

    if (playBtn && globalAudioPlayer) {
        playBtn.addEventListener('click', () => {
            if (!currentAudioUrl) return;
            globalAudioPlayer.classList.remove('hidden');
            setTimeout(() => globalAudioPlayer.classList.add('show'), 10);
            getAudio().play();
            setPlayingUI(true);
        });

        playerPlayBtn.addEventListener('click', () => {
            if (!currentAudioUrl) return;
            const audio = getAudio();
            if (audio.paused) { audio.play(); setPlayingUI(true); }
            else              { audio.pause(); setPlayingUI(false); }
        });

        closePlayerBtn.addEventListener('click', () => {
            globalAudioPlayer.classList.remove('show');
            setTimeout(() => {
                if (!globalAudioPlayer.classList.contains('show')) globalAudioPlayer.classList.add('hidden');
            }, 300);
            if (currentAudio) { currentAudio.pause(); setPlayingUI(false); }
        });
    }
});
