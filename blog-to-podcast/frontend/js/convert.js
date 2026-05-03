document.addEventListener('DOMContentLoaded', () => {
    const BUILD_ID = 'convert-js-trace-2026-05-04-00-31';
    const expectedScriptUrl = new URL('../js/convert.js', window.location.href).href;
    window.__B2C_CONVERT_BUILD__ = BUILD_ID;
    console.info('[Blog2Cast Trace] Runtime info', {
        buildId: BUILD_ID,
        pageHref: window.location.href,
        pagePath: window.location.pathname,
        expectedScriptUrl
    });

    const convertForm = document.getElementById('convertForm');
    const actionArea = document.getElementById('actionArea');
    const progressArea = document.getElementById('progressArea');
    const aiAssistantArea = document.getElementById('aiAssistantArea');
    const resultBanner = document.getElementById('resultBanner');
    const articleUrlInput = document.getElementById('articleUrl');
    const voiceSelect = document.getElementById('voiceProfile');
    const languageSelect = document.getElementById('outputLanguage');
    const convertBtn = document.getElementById('convertBtn');
    const playNowBtn = document.querySelector('.play-btn');
    const globalAudioPlayer = document.getElementById('globalAudioPlayer');
    const closePlayerBtn = document.getElementById('closePlayerBtn');
    const playerPlayBtn = document.getElementById('playerPlayBtn');
    const playerTitle = document.getElementById('playerTitle');
    const articleTextEl = document.querySelector('.article-text');
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');
    const explainPopup = document.getElementById('explainPopup');
    const closePopupBtn = document.getElementById('closePopupBtn');
    const popupSelectedText = document.getElementById('popupSelectedText');
    const explainTermBtn = document.getElementById('explainTermBtn');
    const explanationText = document.getElementById('explanationText');
    const askInput = document.querySelector('#tab-ask .chat-input-area input');
    const sendBtn = document.querySelector('#tab-ask .send-btn');
    const chatArea = document.querySelector('#tab-ask .chat-area');

    const CONTENT_SERVICE = 'http://localhost:8001';
    const PROCESS_SERVICE = 'http://localhost:8000';
    const TTS_SERVICE = 'http://localhost:8005';
    const STATIC_TTS_OPTIONS = {
        languages: [
            { code: 'vi', name: 'Vietnamese' },
            { code: 'en', name: 'English' },
            { code: 'es', name: 'Spanish' },
            { code: 'fr', name: 'French' },
            { code: 'de', name: 'German' }
        ],
        voices: [
            { id: 'vi-VN-HoaiMyNeural', name: 'HoaiMy (Nữ)', language: 'vi' },
            { id: 'vi-VN-NamMinhNeural', name: 'NamMinh (Nam)', language: 'vi' },
            { id: 'en-US-AriaNeural', name: 'Aria (Female)', language: 'en' },
            { id: 'en-US-GuyNeural', name: 'Guy (Male)', language: 'en' },
            { id: 'en-GB-SoniaNeural', name: 'Sonia (British)', language: 'en' },
            { id: 'es-ES-ElviraNeural', name: 'Elvira (Femenino)', language: 'es' },
            { id: 'fr-FR-DeniseNeural', name: 'Denise (Féminin)', language: 'fr' },
            { id: 'de-DE-KatjaNeural', name: 'Katja (Weiblich)', language: 'de' }
        ]
    };

    let currentAudio = null;
    let currentAudioUrl = null;
    let articleTitle = '';
    let currentContext = '';
    let currentLanguage = 'vi';
    let ttsOptions = { languages: [], voices: [] };

    const handleConvert = async (e) => {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }

        const url = articleUrlInput.value.trim();
        const language = languageSelect.value;
        const voice = voiceSelect.value;
        if (!url || !language || !voice) {
            alert("Vui lòng điền URL, chọn ngôn ngữ và giọng đọc.");
            return;
        }

        actionArea.classList.add('hidden');
        progressArea.classList.remove('hidden');
        convertBtn.disabled = true;

        try {
            currentLanguage = language;
            await runPipeline({ url, language, voice });
        } catch (err) {
            console.error(err);
            actionArea.classList.remove('hidden');
            progressArea.classList.add('hidden');
            alert(`Lỗi: ${err.message}`);
        } finally {
            convertBtn.disabled = false;
        }
    };

    if (convertBtn) {
        convertBtn.addEventListener('click', handleConvert);
    }

    if (languageSelect) {
        languageSelect.addEventListener('change', () => {
            renderVoicesByLanguage(languageSelect.value);
        });
    }

    initStaticVoiceLanguageOptions();
    initTabs();
    initExplainPopup();
    initAskChat();
    initAudioPlayer();

    function initStaticVoiceLanguageOptions() {
        ttsOptions = STATIC_TTS_OPTIONS;
        renderLanguageOptions();
        languageSelect.value = ttsOptions.languages[0]?.code || '';
        renderVoicesByLanguage(languageSelect.value);
    }

    function renderLanguageOptions() {
        if (!ttsOptions.languages.length) {
            languageSelect.innerHTML = '<option value="" disabled selected>No language available</option>';
            return;
        }

        const options = ['<option value="" disabled selected>Select Language</option>'];
        for (const lang of ttsOptions.languages) {
            options.push(`<option value="${lang.code}">${lang.name}</option>`);
        }
        languageSelect.innerHTML = options.join('');
    }

    function renderVoicesByLanguage(languageCode) {
        if (!ttsOptions.voices.length) {
            voiceSelect.innerHTML = '<option value="" disabled selected>No voice available</option>';
            return;
        }

        const filteredVoices = languageCode
            ? ttsOptions.voices.filter((v) => v.language === languageCode)
            : ttsOptions.voices;

        if (!filteredVoices.length) {
            voiceSelect.innerHTML = '<option value="" disabled selected>No voice for selected language</option>';
            return;
        }

        const options = ['<option value="" disabled selected>Select Voice</option>'];
        for (const voice of filteredVoices) {
            options.push(`<option value="${voice.id}">${voice.name}</option>`);
        }
        voiceSelect.innerHTML = options.join('');
    }

    async function runPipeline({ url, language, voice }) {
        // Step 0 — Crawl
        activateStep(0);
        const crawlRes = await fetch(`${CONTENT_SERVICE}/crawl`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        if (!crawlRes.ok) throw new Error("Content service error");
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
        if (!processRes.ok) throw new Error("Process service error");
        const processData = await processRes.json();
        const ttsText = processData.script;
        
        if (articleTextEl && processData.summary) {
            articleTextEl.innerHTML = `<p>${processData.summary}</p>`;
        }
        currentContext = [rawText, processData.summary, processData.script].filter(Boolean).join('\n\n');
        completeStep(1);

        // Step 2 — TTS
        activateStep(2);
        const ttsRes = await fetch(`${TTS_SERVICE}/tts`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: ttsText, language, voice })
        });
        if (!ttsRes.ok) throw new Error("TTS service error");
        const ttsData = await ttsRes.json();
        currentAudioUrl = `${TTS_SERVICE}${ttsData.audio_url}`;
        completeStep(2);

        const resultText = resultBanner.querySelector('.result-text p');
        if (resultText) {
            resultText.textContent = 'Duration: ~5:30';
        }

        resultBanner.classList.remove('hidden-banner');
        aiAssistantArea.classList.remove('hidden');
    }

    function initTabs() {
        tabs.forEach((tab) => {
            tab.addEventListener('click', () => {
                const target = tab.dataset.tab;
                tabs.forEach((t) => t.classList.remove('active'));
                tabContents.forEach((c) => c.classList.remove('active'));
                tab.classList.add('active');
                const activeContent = document.getElementById(`tab-${target}`);
                if (activeContent) activeContent.classList.add('active');
            });
        });
    }

    function initExplainPopup() {
        if (!articleTextEl || !explainPopup) return;

        articleTextEl.addEventListener('mouseup', () => {
            const selectedText = window.getSelection()?.toString().trim();
            if (!selectedText) return;
            popupSelectedText.textContent = `"${selectedText}"`;
            explanationText.classList.add('hidden');
            explanationText.innerHTML = '';
            explainPopup.classList.remove('hidden');
            explainPopup.classList.add('show');
        });

        if (closePopupBtn) {
            closePopupBtn.addEventListener('click', () => {
                explainPopup.classList.remove('show');
                explainPopup.classList.add('hidden');
            });
        }

        if (explainTermBtn) {
            explainTermBtn.addEventListener('click', async () => {
                const selected = popupSelectedText.textContent.replace(/^"|"$/g, '').trim();
                explanationText.classList.remove('hidden');
                explanationText.innerHTML = '<p>Đang giải thích...</p>';
                try {
                    const response = await fetch(`${PROCESS_SERVICE}/explain`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            term: selected,
                            context: currentContext || articleTextEl?.innerText || selected,
                            language: currentLanguage
                        })
                    });
                    if (!response.ok) throw new Error('Explain service error');
                    const data = await response.json();
                    explanationText.innerHTML = `<p>${escapeHtml(data.explanation || 'Không có nội dung giải thích.')}</p>`;
                } catch (error) {
                    console.error(error);
                    explanationText.innerHTML = '<p>Không thể lấy giải thích từ AI lúc này.</p>';
                }
            });
        }
    }

    function initAskChat() {
        if (!askInput || !sendBtn || !chatArea) return;

        const sendMessage = () => {
            const question = askInput.value.trim();
            if (!question) return;

            const userMessage = document.createElement('div');
            userMessage.className = 'chat-message user';
            userMessage.innerHTML = `
                <div class="message-bubble">${escapeHtml(question)}</div>
            `;
            chatArea.appendChild(userMessage);

            const botMessage = document.createElement('div');
            botMessage.className = 'chat-message bot';
            botMessage.innerHTML = `
                <div class="avatar"><i class="fas fa-robot"></i></div>
                <div class="message-bubble">Đang trả lời...</div>
            `;
            chatArea.appendChild(botMessage);
            askInput.value = '';
            chatArea.scrollTop = chatArea.scrollHeight;

            fetch(`${PROCESS_SERVICE}/ask`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question,
                    context: currentContext || articleTextEl?.innerText || question,
                    language: currentLanguage
                })
            })
                .then(async (response) => {
                    if (!response.ok) throw new Error('Ask service error');
                    return response.json();
                })
                .then((data) => {
                    const bubble = botMessage.querySelector('.message-bubble');
                    if (bubble) {
                        bubble.textContent = data.answer || 'Không có câu trả lời.';
                    }
                })
                .catch((error) => {
                    console.error(error);
                    const bubble = botMessage.querySelector('.message-bubble');
                    if (bubble) {
                        bubble.textContent = 'Không thể lấy câu trả lời từ AI lúc này.';
                    }
                });
        };

        sendBtn.addEventListener('click', sendMessage);
        askInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                sendMessage();
            }
        });
    }

    function initAudioPlayer() {
        if (playNowBtn) {
            playNowBtn.addEventListener('click', async () => {
                globalAudioPlayer.classList.remove('hidden');
                globalAudioPlayer.classList.add('show');
                playerTitle.textContent = articleTitle || 'Generated Podcast';
                await togglePlayback(true);
            });
        }

        if (playerPlayBtn) {
            playerPlayBtn.addEventListener('click', async () => {
                await togglePlayback();
            });
        }

        if (closePlayerBtn) {
            closePlayerBtn.addEventListener('click', () => {
                globalAudioPlayer.classList.remove('show');
                globalAudioPlayer.classList.add('hidden');
                if (currentAudio) {
                    currentAudio.pause();
                }
                updatePlayerButton(false);
            });
        }
    }

    async function togglePlayback(forcePlay = false) {
        if (!playerPlayBtn) return;

        if (currentAudioUrl) {
            if (!currentAudio) {
                currentAudio = new Audio(currentAudioUrl);
                currentAudio.addEventListener('ended', () => updatePlayerButton(false));
            }

            if (forcePlay || currentAudio.paused) {
                await currentAudio.play();
                updatePlayerButton(true);
            } else {
                currentAudio.pause();
                updatePlayerButton(false);
            }
            return;
        }

        alert('Chưa có audio từ API. Vui lòng Convert thành công rồi thử lại.');
        updatePlayerButton(false);
    }

    function updatePlayerButton(isPlaying) {
        const icon = playerPlayBtn?.querySelector('i');
        if (!icon) return;
        icon.className = isPlaying ? 'fas fa-pause' : 'fas fa-play';
    }

    function escapeHtml(text) {
        return text
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#039;');
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
