document.addEventListener('DOMContentLoaded', () => {

    // DOM Elements
    const form = document.getElementById('convert-form');
    const urlInput = document.getElementById('url-input');
    const langSelect = document.getElementById('language-select');
    const voiceSelect = document.getElementById('voice-select');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnIcon = submitBtn.querySelector('i');
    const btnLoader = document.getElementById('btn-loader');

    const formContainer = document.getElementById('form-container');
    const progressContainer = document.getElementById('progress-container');
    const resultContainer = document.getElementById('result-container');

    // Voice mapping based on language
    const voiceMap = {
        'vi': [
            { value: 'vi-VN-Neural2-A', label: 'Giọng Nữ (Miền Nam)' },
            { value: 'vi-VN-Neural2-D', label: 'Giọng Nam (Miền Bắc)' }
        ],
        'en': [
            { value: 'en-US-Neural2-F', label: 'Female (US English)' },
            { value: 'en-US-Neural2-J', label: 'Male (US English)' }
        ],
        'fr': [
            { value: 'fr-FR-Neural2-A', label: 'Giọng Nữ (Pháp)' },
            { value: 'fr-FR-Neural2-B', label: 'Giọng Nam (Pháp)' }
        ],
        'ja': [
            { value: 'ja-JP-Neural2-A', label: 'Giọng Nữ (Nhật)' },
            { value: 'ja-JP-Neural2-B', label: 'Giọng Nam (Nhật)' }
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
        updateVoiceOptions(); // Set initial options
    }

    // Steps
    const step1 = document.getElementById('step-1');
    const step2 = document.getElementById('step-2');
    const step3 = document.getElementById('step-3');

    // Audio Player
    const audioPlayer = document.getElementById('audio-player');
    const downloadBtn = document.getElementById('download-btn');
    const resetBtn = document.getElementById('reset-btn');
    const saveBtn = document.getElementById('save-btn');

    // New AI UI Elements
    const dynamicSummaryContent = document.getElementById('dynamic-summary-content');
    const tabOriginal = document.getElementById('tab-original');
    const tabTranslated = document.getElementById('tab-translated');

    let currentOriginalSummary = '';
    let currentTranslatedSummary = '';
    let currentOriginalHTML = '';
    let currentTranslatedHTML = '';
    let activeTab = 'original';

    function prepareHighlightableText(text) {
        if (!text) return '';
        // Phân tách theo câu (kết thúc bằng .!? theo sau là khoảng trắng hoặc xuống dòng)
        const tokens = text.match(/[\s\S]*?(?:[.!?]+(?=\s|$)|\n|$)[\s]*/g).filter(t => t.length > 0);
        let html = '';
        let charIndex = 0;
        tokens.forEach(token => {
            html += `<span class="highlightable-word" data-start="${charIndex}" data-end="${charIndex + token.length}" style="transition: background-color 0.15s ease; border-radius: 4px; padding: 2px 0;">${token}</span>`;
            charIndex += token.length;
        });
        return html;
    }

    // Tab switching logic
    if (tabOriginal && tabTranslated && dynamicSummaryContent) {
        tabOriginal.addEventListener('click', () => {
            activeTab = 'original';
            tabOriginal.style.background = 'var(--primary-color)';
            tabOriginal.style.color = 'white';
            tabTranslated.style.background = 'transparent';
            tabTranslated.style.color = 'var(--text-secondary)';
            
            if (currentOriginalHTML) {
                dynamicSummaryContent.innerHTML = `<p>${currentOriginalHTML}</p>`;
            } else {
                dynamicSummaryContent.innerHTML = `<p>Bản tóm tắt ngôn ngữ gốc không khả dụng.</p>`;
            }
        });

        tabTranslated.addEventListener('click', () => {
            activeTab = 'translated';
            tabTranslated.style.background = 'var(--primary-color)';
            tabTranslated.style.color = 'white';
            tabOriginal.style.background = 'transparent';
            tabOriginal.style.color = 'var(--text-secondary)';
            
            if (currentTranslatedHTML) {
                dynamicSummaryContent.innerHTML = `<p>${currentTranslatedHTML}</p>`;
            } else {
                dynamicSummaryContent.innerHTML = `<p>Bản tóm tắt ngôn ngữ chuyển đổi không khả dụng.</p>`;
            }
        });
    }

    // Audio highlight sync
    if (audioPlayer && dynamicSummaryContent) {
        audioPlayer.addEventListener('timeupdate', () => {
            if (!audioPlayer.duration || audioPlayer.paused) return;
            const progress = audioPlayer.currentTime / audioPlayer.duration;
            
            const activeText = activeTab === 'original' ? currentOriginalSummary : currentTranslatedSummary;
            if (!activeText) return;
            
            const targetCharIndex = progress * activeText.length;
            const spans = dynamicSummaryContent.querySelectorAll('.highlightable-word');
            let currentHighlighted = null;
            
            spans.forEach(span => {
                const start = parseInt(span.getAttribute('data-start'));
                const end = parseInt(span.getAttribute('data-end'));
                
                if (targetCharIndex >= start && targetCharIndex <= end) {
                    span.style.backgroundColor = '#ffd54f'; // Yellow highlight
                    span.style.color = '#000';
                    span.style.borderRadius = '3px';
                    span.classList.add('active');
                    currentHighlighted = span;
                } else {
                    span.style.backgroundColor = 'transparent';
                    span.style.color = 'inherit';
                    span.classList.remove('active');
                }
            });
            
            // Tự động cuộn đến từ đang đọc nếu nó ra ngoài vùng nhìn thấy
            if (currentHighlighted) {
                const containerRect = dynamicSummaryContent.getBoundingClientRect();
                const spanRect = currentHighlighted.getBoundingClientRect();
                if (spanRect.bottom > containerRect.bottom || spanRect.top < containerRect.top) {
                    dynamicSummaryContent.scrollTop += (spanRect.top - containerRect.top) - (containerRect.height / 2);
                }
            }
        });
    }

    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const sendChatBtn = document.getElementById('send-chat-btn');

    // Toast
    const errorToast = document.getElementById('error-toast');
    const errorMsg = document.getElementById('error-msg');
    const closeToastBtn = document.getElementById('close-toast-btn');

    // ── API: chỉ 1 endpoint duy nhất qua Gateway ──────────────────────
    const GATEWAY_URL = 'http://localhost:8000';
    const CONVERT_URL = `${GATEWAY_URL}/convert`;

    // ── Submit ─────────────────────────────────────────────────────────
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const url = urlInput.value.trim();
        if (!url) {
            showError('Vui lòng nhập đường dẫn bài viết!');
            return;
        }

        const lang  = langSelect.value;
        const voice = voiceSelect.value;

        startProcessUI();

        try {
            // Hiển thị các bước đang chạy tuần tự (UI feedback)
            updateStep(step1, 'active', 'Đang tải nội dung...');

            // Gọi 1 request duy nhất — gateway xử lý toàn bộ pipeline
            const result = await fetchApi(CONVERT_URL, {
                url:      url,
                language: lang,
                voice:    voice,
            }, (progressEvent) => {
                // Không có streaming, nhưng ta giả lập bước UI sau 2s và 5s
            });

            updateStep(step1, 'done', 'Hoàn tất');
            updateStep(step2, 'done', 'Hoàn tất');
            updateStep(step3, 'done', 'Hoàn tất');

            if (!result.audio_url) throw new Error('Tạo âm thanh thất bại.');

            showResult(result.audio_url, result.script, result.original_script);

        } catch (error) {
            console.error('Pipeline Error:', error);
            handlePipelineError(error.message);
        }
    });

    // Giả lập tiến trình bước UI trong khi chờ gateway (UX)
    function animateSteps() {
        return new Promise((resolve) => {
            setTimeout(() => updateStep(step1, 'active', 'Đang tải nội dung...'), 0);
            setTimeout(() => {
                updateStep(step1, 'done', 'Hoàn tất');
                updateStep(step2, 'active', 'Đang biên tập kịch bản...');
            }, 3000);
            setTimeout(() => {
                updateStep(step2, 'done', 'Hoàn tất');
                updateStep(step3, 'active', 'Đang tổng hợp giọng nói...');
                resolve();
            }, 8000);
        });
    }

    // ── Reset ──────────────────────────────────────────────────────────
    resetBtn.addEventListener('click', () => {
        resultContainer.classList.add('hidden');
        progressContainer.classList.add('hidden');
        formContainer.classList.remove('hidden');

        urlInput.value = '';

        submitBtn.disabled = false;
        btnText.style.display = 'block';
        btnIcon.style.display = 'block';
        btnLoader.classList.add('hidden');

        [step1, step2, step3].forEach(step => {
            step.className = 'step pending';
            step.querySelector('.status-text').textContent = 'Đang chờ...';
        });

        audioPlayer.pause();
        audioPlayer.src = '';
    });

    // ── Save ──────────────────────────────────────────────────────────
    if (saveBtn) {
        saveBtn.addEventListener('click', () => {
            const history = JSON.parse(localStorage.getItem('podcastHistory') || '[]');
            
            // Lấy domain từ URL
            let domain = 'Bài viết';
            try {
                const urlObj = new URL(urlInput.value);
                domain = urlObj.hostname;
            } catch (e) {}

            const newItem = {
                id: Date.now().toString(),
                url: urlInput.value,
                title: `Podcast từ ${domain}`,
                date: new Date().toISOString(),
                language: langSelect.value,
                audioUrl: audioPlayer.src,
                originalSummary: currentOriginalSummary,
                translatedSummary: currentTranslatedSummary
            };
            
            history.unshift(newItem); // Thêm lên đầu danh sách
            localStorage.setItem('podcastHistory', JSON.stringify(history));
            
            // Hiển thị thông báo thành công
            const originalText = saveBtn.innerHTML;
            saveBtn.innerHTML = '<i class="fa-solid fa-check"></i> Đã lưu';
            saveBtn.style.background = 'var(--success)';
            saveBtn.style.color = 'white';
            setTimeout(() => {
                saveBtn.innerHTML = originalText;
                saveBtn.style.background = 'var(--primary-dark)';
                saveBtn.style.color = 'var(--bg-dark)';
            }, 2000);
        });
    }

    // ── Close Toast ────────────────────────────────────────────────────
    closeToastBtn.addEventListener('click', () => {
        errorToast.classList.remove('show');
        errorToast.classList.add('hidden');
    });

    // ── Helpers ────────────────────────────────────────────────────────

    async function fetchApi(url, body) {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || `Lỗi API: ${response.status}`);
        }

        return await response.json();
    }

    function startProcessUI() {
        submitBtn.disabled = true;
        btnText.style.display = 'none';
        btnIcon.style.display = 'none';
        btnLoader.classList.remove('hidden');

        formContainer.classList.add('hidden');
        progressContainer.classList.remove('hidden');

        // Animate steps while waiting for gateway response
        updateStep(step1, 'active', 'Đang tải nội dung...');
        setTimeout(() => {
            if (document.querySelector('.step.active') === step1) {
                updateStep(step1, 'done', 'Hoàn tất');
                updateStep(step2, 'active', 'Đang biên tập kịch bản...');
            }
        }, 4000);
        setTimeout(() => {
            if (document.querySelector('.step.active') === step2) {
                updateStep(step2, 'done', 'Hoàn tất');
                updateStep(step3, 'active', 'Đang tổng hợp giọng nói...');
            }
        }, 10000);
    }

    function updateStep(stepEl, status, message) {
        stepEl.className = `step ${status}`;
        stepEl.querySelector('.status-text').textContent = message;
    }

    function handlePipelineError(msg) {
        const activeStep = document.querySelector('.step.active');
        if (activeStep) updateStep(activeStep, 'error', 'Thất bại');

        showError(msg);

        setTimeout(() => {
            submitBtn.disabled = false;
            btnText.style.display = 'block';
            btnIcon.style.display = 'block';
            btnLoader.classList.add('hidden');
            formContainer.classList.remove('hidden');
            progressContainer.classList.add('hidden');

            [step1, step2, step3].forEach(step => {
                step.className = 'step pending';
                step.querySelector('.status-text').textContent = 'Đang chờ...';
            });
        }, 3000);
    }

    function showResult(audioPath, summaryText, originalSummaryText) {
        // Đảm bảo tất cả steps đều done trước khi hiện kết quả
        updateStep(step1, 'done', 'Hoàn tất');
        updateStep(step2, 'done', 'Hoàn tất');
        updateStep(step3, 'done', 'Hoàn tất');

        setTimeout(() => {
            progressContainer.classList.add('hidden');
            resultContainer.classList.remove('hidden');

            // audio_url dạng /download/<filename> — proxy qua gateway.
            // Thêm cache-buster và ép audio.load() để tránh browser phát lại file cũ.
            const fullAudioUrl = `${GATEWAY_URL}${audioPath}?t=${Date.now()}`;
            audioPlayer.pause();
            audioPlayer.removeAttribute('src');
            audioPlayer.load();
            audioPlayer.src = fullAudioUrl;
            audioPlayer.load();
            downloadBtn.href = fullAudioUrl;
            
            // Update Summary
            currentOriginalSummary = originalSummaryText || '';
            currentTranslatedSummary = summaryText || '';
            currentContext = currentOriginalSummary || currentTranslatedSummary;  // dùng làm context cho explain
            currentOriginalHTML = prepareHighlightableText(currentOriginalSummary);
            currentTranslatedHTML = prepareHighlightableText(currentTranslatedSummary);

            // Mặc định chọn tab ngôn ngữ gốc khi có kết quả
            if (tabOriginal) {
                tabOriginal.click();
            } else if (dynamicSummaryContent) {
                dynamicSummaryContent.innerHTML = `<p>${currentOriginalHTML}</p>`;
            }
            
            // Reset chat
            chatMessages.innerHTML = `
                <div class="message ai-message">
                    <div class="message-avatar"><i class="fa-solid fa-robot"></i></div>
                    <div class="message-bubble">
                        Chào bạn! Tôi là trợ lý AI. Bạn có câu hỏi nào về nội dung của podcast này không?
                    </div>
                </div>
            `;
        }, 1000);
    }

    function showError(msg) {
        errorMsg.textContent = msg;
        errorToast.classList.remove('hidden');
        errorToast.classList.add('show');
        setTimeout(() => {
            errorToast.classList.remove('show');
            errorToast.classList.add('hidden');
        }, 5000);
    }

    // ── Explain Term (highlight → tooltip → popup) ────────────────────
    const selectionTooltip = document.getElementById('selection-tooltip');
    const explainPopup     = document.getElementById('explain-popup');
    const explainPopupWord = document.getElementById('explain-popup-word');
    const explainLoading   = document.getElementById('explain-loading');
    const explainContent   = document.getElementById('explain-content');
    const explainMeaning   = document.getElementById('explain-meaning');
    const explainExample   = document.getElementById('explain-example');
    const explainError     = document.getElementById('explain-error');
    const explainClose     = document.getElementById('explain-popup-close');

    let currentContext = '';  // lưu summary text hiện tại để làm context

    // Khi user bôi text trong summary → hiện tooltip "Giải thích"
    document.addEventListener('mouseup', (e) => {
        // Bỏ qua nếu click vào popup/tooltip
        if (explainPopup.contains(e.target) || selectionTooltip.contains(e.target)) return;

        const selection = window.getSelection();
        const selectedText = selection ? selection.toString().trim() : '';

        if (selectedText.length < 2 || selectedText.length > 200) {
            selectionTooltip.style.display = 'none';
            return;
        }

        // Chỉ hiện khi bôi trong vùng summary
        const summaryEl = document.getElementById('dynamic-summary-content');
        if (!summaryEl) return;
        const range = selection.getRangeAt(0);
        if (!summaryEl.contains(range.commonAncestorContainer)) {
            selectionTooltip.style.display = 'none';
            return;
        }

        // Hiện tooltip gần vị trí bôi
        const rect = range.getBoundingClientRect();
        selectionTooltip.style.display = 'block';
        selectionTooltip.style.left = `${rect.left + rect.width / 2 - selectionTooltip.offsetWidth / 2}px`;
        selectionTooltip.style.top  = `${rect.top - 44 + window.scrollY}px`;
        selectionTooltip.dataset.word = selectedText;
    });

    // Click tooltip → gọi API giải thích
    selectionTooltip.addEventListener('click', async () => {
        const word = selectionTooltip.dataset.word;
        if (!word) return;

        selectionTooltip.style.display = 'none';
        window.getSelection()?.removeAllRanges();

        // Hiện popup ở giữa màn hình
        explainPopupWord.textContent = `"${word}"`;
        explainLoading.style.display = 'block';
        explainContent.style.display = 'none';
        explainError.style.display   = 'none';
        explainPopup.style.display   = 'block';
        explainPopup.style.left = `${window.innerWidth / 2 - 160}px`;
        explainPopup.style.top  = `${window.innerHeight / 2 - 100 + window.scrollY}px`;

        try {
            const res = await fetch(`${GATEWAY_URL}/explain`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ word, context: currentContext, language: langSelect.value }),
            });
            if (!res.ok) throw new Error(`Lỗi ${res.status}`);
            const data = await res.json();

            explainMeaning.innerHTML = `<strong>Nghĩa:</strong> ${data.meaning || '—'}`;
            explainExample.innerHTML = data.example ? `Ví dụ: ${data.example}` : '';
            explainLoading.style.display = 'none';
            explainContent.style.display = 'block';
        } catch (err) {
            explainLoading.style.display = 'none';
            explainError.style.display   = 'block';
            explainError.textContent     = `Không giải thích được: ${err.message}`;
        }
    });

    // Đóng popup
    explainClose.addEventListener('click', () => { explainPopup.style.display = 'none'; });
    document.addEventListener('mousedown', (e) => {
        if (!explainPopup.contains(e.target) && !selectionTooltip.contains(e.target)) {
            explainPopup.style.display = 'none';
        }
        if (!selectionTooltip.contains(e.target)) {
            selectionTooltip.style.display = 'none';
        }
    });

    // ── AI Chat Logic ──────────────────────────────────────────────────
    sendChatBtn.addEventListener('click', sendChatMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChatMessage();
    });

    function sendChatMessage() {
        const text = chatInput.value.trim();
        if (!text) return;

        addChatMessage(text, 'user-message');
        chatInput.value = '';

        // Hiện loading
        const loadingId = 'loading-' + Date.now();
        addChatMessage('...', 'ai-message loading', loadingId);

        fetch(`${GATEWAY_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: text, context: currentContext, language: langSelect ? langSelect.value : 'vi' }),
        })
        .then(r => r.json())
        .then(data => {
            // Xóa loading
            const loadingEl = document.getElementById(loadingId);
            if (loadingEl) loadingEl.remove();

            const answer = data.answer || 'Không có câu trả lời.';
            const source = data.source || '';
            const confidence = data.confidence || 'low';

            const confidenceColor = confidence === 'high' ? '#4ade80' : confidence === 'medium' ? '#fbbf24' : '#94a3b8';
            const confidenceLabel = confidence === 'high' ? 'Chắc chắn' : confidence === 'medium' ? 'Khá chắc' : 'Không chắc';

            let html = `<div>${answer}</div>`;
            if (source) {
                html += `<div style="margin-top:8px; font-size:0.82rem; color:#94a3b8; border-left:2px solid #a78bfa; padding-left:8px; font-style:italic;">"${source}"</div>`;
            }
            html += `<div style="margin-top:6px; font-size:0.75rem; color:${confidenceColor};">● ${confidenceLabel}</div>`;

            addChatMessageHTML(html, 'ai-message');
        })
        .catch(err => {
            const loadingEl = document.getElementById(loadingId);
            if (loadingEl) loadingEl.remove();
            addChatMessage(`Lỗi: ${err.message}`, 'ai-message');
        });
    }

    function addChatMessage(text, type, id) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${type}`;
        if (id) msgDiv.id = id;
        
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        avatarDiv.innerHTML = type.includes('user-message') ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-robot"></i>';
        
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'message-bubble';
        bubbleDiv.textContent = text;
        
        msgDiv.appendChild(avatarDiv);
        msgDiv.appendChild(bubbleDiv);
        
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function addChatMessageHTML(html, type) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${type}`;
        
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        avatarDiv.innerHTML = '<i class="fa-solid fa-robot"></i>';
        
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'message-bubble';
        bubbleDiv.innerHTML = html;
        
        msgDiv.appendChild(avatarDiv);
        msgDiv.appendChild(bubbleDiv);
        
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});
