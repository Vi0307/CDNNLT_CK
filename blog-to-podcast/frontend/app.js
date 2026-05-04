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

    // Steps
    const step1 = document.getElementById('step-1');
    const step2 = document.getElementById('step-2');
    const step3 = document.getElementById('step-3');

    // Audio Player
    const audioPlayer = document.getElementById('audio-player');
    const downloadBtn = document.getElementById('download-btn');
    const resetBtn = document.getElementById('reset-btn');

    // New AI UI Elements
    const summaryContent = document.getElementById('summary-content');
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

            showResult(result.audio_url, result.summary);

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

    function showResult(audioPath, summaryText) {
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
            if (summaryText) {
                summaryContent.innerHTML = `<p>${summaryText}</p>`;
            } else {
                summaryContent.innerHTML = `<p>Đây là bản tóm tắt tự động nội dung bài viết. Bài viết cung cấp các thông tin chính yếu được trích xuất bằng AI, giúp bạn nắm bắt nhanh chóng ngữ cảnh trước khi nghe podcast.</p>`;
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

    // ── AI Chat Logic ──────────────────────────────────────────────────
    sendChatBtn.addEventListener('click', sendChatMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChatMessage();
    });

    function sendChatMessage() {
        const text = chatInput.value.trim();
        if (!text) return;

        // Add user message
        addChatMessage(text, 'user-message');
        chatInput.value = '';

        // Mute/Mock AI response
        setTimeout(() => {
            addChatMessage('Tôi đang phân tích câu hỏi của bạn. Tính năng trả lời tự động chuyên sâu theo ngữ cảnh podcast đang được phát triển.', 'ai-message');
        }, 1000);
    }

    function addChatMessage(text, type) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${type}`;
        
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        avatarDiv.innerHTML = type === 'user-message' ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-robot"></i>';
        
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'message-bubble';
        bubbleDiv.textContent = text;
        
        msgDiv.appendChild(avatarDiv);
        msgDiv.appendChild(bubbleDiv);
        
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});
