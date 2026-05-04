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

            showResult(result.audio_url);

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

    function showResult(audioPath) {
        // Đảm bảo tất cả steps đều done trước khi hiện kết quả
        updateStep(step1, 'done', 'Hoàn tất');
        updateStep(step2, 'done', 'Hoàn tất');
        updateStep(step3, 'done', 'Hoàn tất');

        setTimeout(() => {
            progressContainer.classList.add('hidden');
            resultContainer.classList.remove('hidden');

            // audio_url dạng /download/<filename> — proxy qua gateway
            const fullAudioUrl = `${GATEWAY_URL}${audioPath}`;
            audioPlayer.src = fullAudioUrl;
            downloadBtn.href = fullAudioUrl;
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
});
