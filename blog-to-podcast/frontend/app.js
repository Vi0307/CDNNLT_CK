document.addEventListener('DOMContentLoaded', () => {

    // --- DOM Elements ---
    const form = document.getElementById('convert-form');
    const urlInput = document.getElementById('url-input');
    const langSelect = document.getElementById('language-select');
    const voiceSelect = document.getElementById('voice-select');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnIcon = submitBtn.querySelector('.fa-arrow-right');
    const btnLoader = document.getElementById('btn-loader');

    // Panel States
    const stateGenerating = document.getElementById('state-generating');
    const stateResult = document.getElementById('state-result');

    // Generating Steps
    const step1 = document.getElementById('step-1');
    const step2 = document.getElementById('step-2');
    const step3 = document.getElementById('step-3');

    // Audio Player & Controls
    const audioPlayer = document.getElementById('audio-player');
    const playPauseBtn = document.getElementById('play-pause-btn');
    const playPauseIcon = playPauseBtn.querySelector('i');
    const waveformContainer = document.getElementById('waveform-container');
    const waveformProgress = document.getElementById('waveform-progress');
    const timeDisplay = document.getElementById('time-display');

    const downloadBtn = document.getElementById('download-btn');
    const resetBtn = document.getElementById('reset-btn');

    // UI Result Elements
    const resultTitle = document.getElementById('result-title');
    const resultVoiceName = document.getElementById('result-voice-name');
    const dynamicSummaryContent = document.getElementById('dynamic-summary-content');
    const tabOriginal = document.getElementById('tab-original');
    const tabTranslated = document.getElementById('tab-translated');

    // Trending Chips
    const trendingChips = document.querySelectorAll('.topic-chip');

    // Chat
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const sendChatBtn = document.getElementById('send-chat-btn');

    // Toast
    const errorToast = document.getElementById('error-toast');
    const errorMsg = document.getElementById('error-msg');
    const closeToastBtn = document.getElementById('close-toast-btn');

    // --- Voice Mapping ---
    const voiceMap = {
        'vi': [
            { value: 'vi-VN-Neural2-A', label: 'Female Voice (Southern)' },
            { value: 'vi-VN-Neural2-D', label: 'Male Voice (Northern)' }
        ],
        'en': [
            { value: 'en-US-Neural2-F', label: 'Female (US English)' },
            { value: 'en-US-Neural2-J', label: 'Male (US English)' }
        ],
        'fr': [
            { value: 'fr-FR-Neural2-A', label: 'Female Voice (French)' },
            { value: 'fr-FR-Neural2-B', label: 'Male Voice (French)' }
        ],
        'ja': [
            { value: 'ja-JP-Neural2-A', label: 'Female Voice (Japanese)' },
            { value: 'ja-JP-Neural2-B', label: 'Male Voice (Japanese)' }
        ]
    };

    function updateVoiceOptions() {
        if (!langSelect || !voiceSelect) return;
        const selectedLang = langSelect.value;
        const voices = voiceMap[selectedLang] || voiceMap['vi'];
        
        voiceSelect.innerHTML = '';
        voices.forEach(voice => {
            const option = document.createElement('option');
            option.value = voice.value;
            option.textContent = voice.label;
            voiceSelect.appendChild(option);
        });
    }

    if (langSelect && voiceSelect) {
        langSelect.addEventListener('change', updateVoiceOptions);
        updateVoiceOptions();
    }

    // --- Trending Chips Fill ---
    trendingChips.forEach(chip => {
        chip.addEventListener('click', () => {
            urlInput.value = `https://example.com/topic/${chip.textContent.toLowerCase().replace(/\s+/g, '-')}`;
            urlInput.focus();
        });
    });

    // --- State Management ---
    function switchState(targetState) {
        // Only active class will show thanks to CSS
        [stateGenerating, stateResult].forEach(el => {
            if (!el) return;
            if (targetState && el === targetState) {
                el.classList.remove('hidden');
                // Use a tiny timeout to allow display:flex to apply before setting opacity
                setTimeout(() => el.classList.add('active'), 10);
            } else {
                el.classList.remove('active');
                setTimeout(() => el.classList.add('hidden'), 500); // Wait for fade out
            }
        });
    }

    let currentOriginalSummary = '';
    let currentTranslatedSummary = '';
    let currentOriginalHTML = '';
    let currentTranslatedHTML = '';
    let activeTab = 'original';
    let rawArticleText = '';

    function prepareHighlightableText(text) {
        if (!text) return '';
        const tokens = text.match(/[\s\S]*?(?:[.!?]+(?=\s|$)|\n|$)[\s]*/g).filter(t => t.length > 0);
        let html = '';
        let charIndex = 0;
        tokens.forEach(token => {
            html += `<span class="highlightable-word" data-start="${charIndex}" data-end="${charIndex + token.length}" style="transition: background-color 0.15s ease; border-radius: 4px; padding: 2px 0;">${token}</span>`;
            charIndex += token.length;
        });
        return html;
    }

    if (tabOriginal && tabTranslated && dynamicSummaryContent) {
        tabOriginal.addEventListener('click', () => {
            activeTab = 'original';
            tabOriginal.classList.add('active');
            tabTranslated.classList.remove('active');
            dynamicSummaryContent.innerHTML = currentOriginalHTML ? `<p>${currentOriginalHTML}</p>` : `<p>Summary not available.</p>`;
        });

        tabTranslated.addEventListener('click', () => {
            activeTab = 'translated';
            tabTranslated.classList.add('active');
            tabOriginal.classList.remove('active');
            dynamicSummaryContent.innerHTML = currentTranslatedHTML ? `<p>${currentTranslatedHTML}</p>` : `<p>Translation not available.</p>`;
        });
    }

    // --- Waveform & Audio Player Logic ---
    const NUM_BARS = 60;
    
    // Generate dummy bars for UI
    function generateWaveformBars() {
        waveformContainer.innerHTML = '<div class="waveform-progress" id="waveform-progress"></div>';
        const prog = document.getElementById('waveform-progress');
        for (let i = 0; i < NUM_BARS; i++) {
            const bar = document.createElement('div');
            bar.className = 'waveform-bar';
            // Random height between 20% and 100%
            const height = 20 + Math.random() * 80;
            bar.style.height = `${height}%`;
            waveformContainer.appendChild(bar);
        }
    }
    generateWaveformBars();

    let animationId;
    
    playPauseBtn.addEventListener('click', () => {
        if (audioPlayer.paused) {
            audioPlayer.play();
        } else {
            audioPlayer.pause();
        }
    });

    audioPlayer.addEventListener('play', () => {
        playPauseIcon.className = 'fa-solid fa-pause';
        animateWaveform();
    });

    audioPlayer.addEventListener('pause', () => {
        playPauseIcon.className = 'fa-solid fa-play';
        cancelAnimationFrame(animationId);
    });

    audioPlayer.addEventListener('ended', () => {
        playPauseIcon.className = 'fa-solid fa-play';
        cancelAnimationFrame(animationId);
        document.getElementById('waveform-progress').style.width = '0%';
    });

    function formatTime(seconds) {
        if (isNaN(seconds)) return '0:00';
        const m = Math.floor(seconds / 60);
        const s = Math.floor(seconds % 60);
        return `${m}:${s.toString().padStart(2, '0')}`;
    }

    audioPlayer.addEventListener('timeupdate', () => {
        if (!audioPlayer.duration) return;
        const progress = audioPlayer.currentTime / audioPlayer.duration;
        
        // Update waveform progress overlay
        const progEl = document.getElementById('waveform-progress');
        if (progEl) progEl.style.width = `${progress * 100}%`;
        
        // Update time display
        timeDisplay.textContent = `${formatTime(audioPlayer.currentTime)} / ${formatTime(audioPlayer.duration)}`;

        // Sync text highlight
        const activeText = activeTab === 'original' ? currentOriginalSummary : currentTranslatedSummary;
        if (!activeText) return;
        
        const targetCharIndex = progress * activeText.length;
        const spans = dynamicSummaryContent.querySelectorAll('.highlightable-word');
        let currentHighlighted = null;
        
        spans.forEach(span => {
            const start = parseInt(span.getAttribute('data-start'));
            const end = parseInt(span.getAttribute('data-end'));
            
            if (targetCharIndex >= start && targetCharIndex <= end) {
                span.classList.add('active');
                currentHighlighted = span;
            } else {
                span.classList.remove('active');
            }
        });
        
        if (currentHighlighted) {
            const containerRect = dynamicSummaryContent.getBoundingClientRect();
            const spanRect = currentHighlighted.getBoundingClientRect();
            if (spanRect.bottom > containerRect.bottom || spanRect.top < containerRect.top) {
                dynamicSummaryContent.scrollTop += (spanRect.top - containerRect.top) - (containerRect.height / 2);
            }
        }
    });

    audioPlayer.addEventListener('loadedmetadata', () => {
        timeDisplay.textContent = `0:00 / ${formatTime(audioPlayer.duration)}`;
    });

    // Click on waveform to seek
    waveformContainer.addEventListener('click', (e) => {
        if (!audioPlayer.duration) return;
        const rect = waveformContainer.getBoundingClientRect();
        const pos = (e.clientX - rect.left) / rect.width;
        audioPlayer.currentTime = pos * audioPlayer.duration;
    });

    function animateWaveform() {
        // Subtle random dance for the bars when playing
        const bars = waveformContainer.querySelectorAll('.waveform-bar');
        bars.forEach((bar, index) => {
            // Only animate occasionally to save CPU, and give it a pulsing feel
            if (Math.random() > 0.8) {
                const newHeight = 30 + Math.random() * 70;
                bar.style.height = `${newHeight}%`;
            }
        });
        animationId = requestAnimationFrame(animateWaveform);
    }

    // --- API & Processing ---
    const GATEWAY_URL = 'http://localhost:8000';
    const CONVERT_URL = `${GATEWAY_URL}/convert`;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const url = urlInput.value.trim();
        if (!url) {
            showError('Please enter an article URL!');
            return;
        }

        const lang  = langSelect.value;
        const voice = voiceSelect.value;

        startProcessUI();

        try {
            // Wait a tiny bit for UI to transition
            await new Promise(r => setTimeout(r, 500));
            updateStep(step1, 'active');

            const result = await fetchApi(CONVERT_URL, {
                url:      url,
                language: lang,
                voice:    voice,
            });

            updateStep(step1, 'done');
            updateStep(step2, 'done');
            updateStep(step3, 'done');

            if (!result.audio_url) throw new Error('Audio generation failed.');

            rawArticleText = result.raw_text || '';
            
            // Extract domain for title placeholder
            let domain = 'Article';
            try { domain = new URL(url).hostname.replace('www.', ''); } catch(e){}

            showResult(result.audio_url, result.script, result.original_script, domain, voiceSelect.options[voiceSelect.selectedIndex].text);

        } catch (error) {
            console.error('Pipeline Error:', error);
            handlePipelineError(error.message);
        }
    });

    function startProcessUI() {
        submitBtn.disabled = true;
        btnText.style.display = 'none';
        btnIcon.style.display = 'none';
        btnLoader.classList.remove('hidden');
        document.getElementById('main-right-panel').classList.remove('hidden');

        switchState(stateGenerating);

        // Simulated steps UX
        updateStep(step1, 'active');
        setTimeout(() => {
            if (stateGenerating.classList.contains('active')) {
                updateStep(step1, 'done');
                updateStep(step2, 'active');
            }
        }, 4000);
        setTimeout(() => {
            if (stateGenerating.classList.contains('active')) {
                updateStep(step2, 'done');
                updateStep(step3, 'active');
            }
        }, 10000);
    }

    function updateStep(stepEl, status) {
        stepEl.className = `p-step ${status}`;
    }

    function handlePipelineError(msg) {
        showError(msg);
        
        setTimeout(() => {
            resetUI();
        }, 3000);
    }

    function showResult(audioPath, summaryText, originalSummaryText, domain, voiceName) {
        // Complete steps visually
        updateStep(step1, 'done');
        updateStep(step2, 'done');
        updateStep(step3, 'done');

        setTimeout(() => {
            switchState(stateResult);

            // Setup Data
            resultTitle.textContent = `${domain} Podcast`;
            resultVoiceName.textContent = voiceName;

            const fullAudioUrl = `${GATEWAY_URL}${audioPath}?t=${Date.now()}`;
            audioPlayer.pause();
            audioPlayer.removeAttribute('src');
            audioPlayer.load();
            audioPlayer.src = fullAudioUrl;
            audioPlayer.load();
            downloadBtn.href = fullAudioUrl;
            
            currentOriginalSummary = originalSummaryText || '';
            currentTranslatedSummary = summaryText || '';
            currentContext = currentOriginalSummary || currentTranslatedSummary; 
            currentOriginalHTML = prepareHighlightableText(currentOriginalSummary);
            currentTranslatedHTML = prepareHighlightableText(currentTranslatedSummary);

            if (tabOriginal) {
                tabOriginal.click();
            }
            
            // Reset chat
            chatMessages.innerHTML = `
                <div class="message ai-message">
                    <div class="msg-avatar"><i class="fa-solid fa-robot"></i></div>
                    <div class="msg-bubble">
                        Podcast is ready! Ask me anything about the content.
                    </div>
                </div>
            `;
            
            // Generate new random bars
            generateWaveformBars();

            // Reset submit button
            submitBtn.disabled = false;
            btnText.style.display = 'block';
            btnIcon.style.display = 'block';
            btnLoader.classList.add('hidden');
            
            // Save state for page reload
            sessionStorage.setItem('podcastState', JSON.stringify({
                audioPath, summaryText, originalSummaryText, domain, voiceName, rawArticleText
            }));

        }, 1000);
    }

    function resetUI() {
        sessionStorage.removeItem('podcastState');
        switchState(null);
        document.getElementById('main-right-panel').classList.add('hidden');

        urlInput.value = '';
        rawArticleText = '';

        submitBtn.disabled = false;
        btnText.style.display = 'block';
        btnIcon.style.display = 'block';
        btnLoader.classList.add('hidden');

        [step1, step2, step3].forEach(step => updateStep(step, ''));

        audioPlayer.pause();
        audioPlayer.src = '';
        playPauseIcon.className = 'fa-solid fa-play';
        cancelAnimationFrame(animationId);
    }

    resetBtn.addEventListener('click', resetUI);

    async function fetchApi(url, body) {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || `API Error: ${response.status}`);
        }

        return await response.json();
    }

    function showError(msg) {
        errorMsg.textContent = msg;
        errorToast.classList.remove('hidden');
        // small timeout to allow display:flex to apply
        setTimeout(() => errorToast.classList.add('show'), 10);
        setTimeout(() => {
            errorToast.classList.remove('show');
            setTimeout(() => errorToast.classList.add('hidden'), 400);
        }, 5000);
    }

    closeToastBtn.addEventListener('click', () => {
        errorToast.classList.remove('show');
        setTimeout(() => errorToast.classList.add('hidden'), 400);
    });

    // --- Explain Term Tooltip & Popup ---
    const selectionTooltip = document.getElementById('selection-tooltip');
    const explainPopup     = document.getElementById('explain-popup');
    const explainPopupWord = document.getElementById('explain-popup-word');
    const explainLoading   = document.getElementById('explain-loading');
    const explainContent   = document.getElementById('explain-content');
    const explainMeaning   = document.getElementById('explain-meaning');
    const explainExample   = document.getElementById('explain-example');
    const explainError     = document.getElementById('explain-error');
    const explainClose     = document.getElementById('explain-popup-close');

    let currentContext = '';

    document.addEventListener('mouseup', (e) => {
        if (explainPopup.contains(e.target) || selectionTooltip.contains(e.target)) return;

        const selection = window.getSelection();
        const selectedText = selection ? selection.toString().trim() : '';

        if (selectedText.length < 2 || selectedText.length > 200) {
            selectionTooltip.style.display = 'none';
            return;
        }

        const summaryEl = document.getElementById('dynamic-summary-content');
        if (!summaryEl) return;
        const range = selection.getRangeAt(0);
        if (!summaryEl.contains(range.commonAncestorContainer)) {
            selectionTooltip.style.display = 'none';
            return;
        }

        const rect = range.getBoundingClientRect();
        selectionTooltip.style.display = 'block';
        selectionTooltip.style.left = `${rect.left + rect.width / 2 - selectionTooltip.offsetWidth / 2}px`;
        selectionTooltip.style.top  = `${rect.top - 44 + window.scrollY}px`;
        selectionTooltip.dataset.word = selectedText;
    });

    selectionTooltip.addEventListener('click', async () => {
        const word = selectionTooltip.dataset.word;
        if (!word) return;

        selectionTooltip.style.display = 'none';
        window.getSelection()?.removeAllRanges();

        explainPopupWord.textContent = `"${word}"`;
        explainLoading.style.display = 'block';
        explainContent.style.display = 'none';
        explainError.style.display   = 'none';
        explainPopup.style.display   = 'block';
        
        // Center popup in view
        explainPopup.style.left = `${window.innerWidth / 2 - 160}px`;
        explainPopup.style.top  = `${window.innerHeight / 2 - 100 + window.scrollY}px`;

        try {
            const res = await fetch(`${GATEWAY_URL}/explain`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ word, context: (rawArticleText || currentContext).slice(0, 3000), language: langSelect.value }),
            });
            if (!res.ok) throw new Error(`Error ${res.status}`);
            const data = await res.json();

            explainMeaning.innerHTML = `<strong>Definition:</strong> ${data.meaning || '—'}`;
            explainExample.innerHTML = data.example ? `"${data.example}"` : '';
            explainLoading.style.display = 'none';
            explainContent.style.display = 'block';
        } catch (err) {
            explainLoading.style.display = 'none';
            explainError.style.display   = 'block';
            explainError.textContent     = `Could not explain: ${err.message}`;
        }
    });

    explainClose.addEventListener('click', () => { explainPopup.style.display = 'none'; });
    document.addEventListener('mousedown', (e) => {
        if (!explainPopup.contains(e.target) && !selectionTooltip.contains(e.target)) {
            explainPopup.style.display = 'none';
        }
        if (!selectionTooltip.contains(e.target)) {
            selectionTooltip.style.display = 'none';
        }
    });

    // --- AI Chat ---
    sendChatBtn.addEventListener('click', sendChatMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChatMessage();
    });

    function buildContext(text, question) {
        if (!text) return '';
        const MAX_TOTAL = 4500;
        return text.length > MAX_TOTAL ? text.slice(0, MAX_TOTAL) : text; // Simplified for speed
    }

    function sendChatMessage() {
        const text = chatInput.value.trim();
        if (!text) return;

        addChatMessage(text, 'user-message');
        chatInput.value = '';

        const loadingId = 'loading-' + Date.now();
        addChatMessage('...', 'ai-message loading', loadingId);

        fetch(`${GATEWAY_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: text,
                context: buildContext(rawArticleText || currentContext, text),
                language: langSelect ? langSelect.value : 'vi'
            }),
        })
        .then(r => r.json())
        .then(data => {
            const loadingEl = document.getElementById(loadingId);
            if (loadingEl) loadingEl.remove();

            const answer = data.answer || 'No answer available.';
            addChatMessage(answer, 'ai-message');
        })
        .catch(err => {
            const loadingEl = document.getElementById(loadingId);
            if (loadingEl) loadingEl.remove();
            addChatMessage(`Error: ${err.message}`, 'ai-message');
        });
    }

    function addChatMessage(text, type, id) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${type}`;
        if (id) msgDiv.id = id;
        
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'msg-avatar';
        avatarDiv.innerHTML = type.includes('user-message') ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-robot"></i>';
        
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'msg-bubble';
        bubbleDiv.textContent = text;
        
        msgDiv.appendChild(avatarDiv);
        msgDiv.appendChild(bubbleDiv);
        
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // --- Restore State on Reload ---
    const savedState = sessionStorage.getItem('podcastState');
    if (savedState) {
        try {
            const data = JSON.parse(savedState);
            rawArticleText = data.rawArticleText || '';
            document.getElementById('main-right-panel').classList.remove('hidden');
            
            // Bypass the generating visual timeout by tweaking showResult or just calling it directly
            // For simplicity, we just call showResult which takes 1 second to transition
            switchState(stateGenerating); // Initial state
            showResult(data.audioPath, data.summaryText, data.originalSummaryText, data.domain, data.voiceName);
        } catch(e) {
            console.error("Failed to restore state", e);
        }
    }
});
