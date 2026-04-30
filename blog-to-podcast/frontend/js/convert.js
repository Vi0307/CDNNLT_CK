// ============================================================
// Config
// ============================================================
const API_BASE = "http://localhost:8001";

// ============================================================
// Helpers
// ============================================================
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function setStepState(stepEl, state) {
    // state: 'pending' | 'active' | 'completed' | 'error'
    stepEl.classList.remove('pending', 'active', 'completed', 'error');
    stepEl.classList.add(state);
    const icon = stepEl.querySelector('.step-icon i');
    if (state === 'completed') icon.className = 'fas fa-check';
    else if (state === 'active')   icon.className = 'fas fa-spinner fa-spin';
    else if (state === 'error')    icon.className = 'fas fa-times';
    else                           icon.className = 'fas fa-circle';
}

// ============================================================
// Main Form Logic
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    const convertForm     = document.getElementById('convertForm');
    const actionArea      = document.getElementById('actionArea');
    const progressArea    = document.getElementById('progressArea');
    const aiAssistantArea = document.getElementById('aiAssistantArea');

    // Lấy các bước trong stepper
    const steps = document.querySelectorAll('.stepper .step');
    // steps[0] = Crawling Article
    // steps[1] = AI Processing
    // steps[2] = Audio Generation

    // Hiển thị text nhận từ API vào tab Explain
    const articleTextEl = document.querySelector('.article-text');

    // -------------------------------------------------------
    // Form Submit
    // -------------------------------------------------------
    if (convertForm) {
        convertForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const urlInput = document.getElementById('articleUrl');
            const url = urlInput.value.trim();
            if (!url) return;

            // Reset UI
            actionArea.classList.add('hidden');
            progressArea.classList.remove('hidden');
            aiAssistantArea.classList.add('hidden');

            // Đặt tất cả steps về pending
            steps.forEach(s => setStepState(s, 'pending'));

            // -----------------------------------------------
            // Bước 1: Crawl Article → gọi content-service
            // -----------------------------------------------
            setStepState(steps[0], 'active');
            await sleep(500); // nhỏ delay để user thấy animation

            let crawlData = null;
            try {
                const res = await fetch(`${API_BASE}/crawl`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ url })
                });

                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail || "Crawl thất bại");
                }

                crawlData = await res.json();
                setStepState(steps[0], 'completed');

                // Hiển thị text bài viết vào tab Explain
                if (articleTextEl && crawlData.text) {
                    articleTextEl.innerHTML = `
                        <p><strong>${crawlData.title}</strong></p>
                        ${crawlData.text.split('\n\n').map(p => `<p>${p.trim()}</p>`).join('')}
                        ${crawlData.is_mock ? '<p class="mock-badge"><i class="fas fa-flask"></i> Mock data · ' + crawlData.word_count + ' words</p>' : ''}
                    `;
                }

            } catch (err) {
                setStepState(steps[0], 'error');
                showError(`❌ Lỗi crawl: ${err.message}`);
                actionArea.classList.remove('hidden');
                return;
            }

            // -----------------------------------------------
            // Bước 2: AI Processing (chưa có API → mock delay)
            // TODO: Kết nối API /process của bạn bè ở đây
            // -----------------------------------------------
            setStepState(steps[1], 'active');
            await sleep(1800); // giả lập thời gian xử lý AI
            setStepState(steps[1], 'completed');

            // -----------------------------------------------
            // Bước 3: Audio Generation (chưa có API → mock delay)
            // TODO: Kết nối API /tts sau này
            // -----------------------------------------------
            setStepState(steps[2], 'active');
            await sleep(1500);
            setStepState(steps[2], 'completed');

            // -----------------------------------------------
            // Hiện kết quả và AI Assistant
            // -----------------------------------------------
            aiAssistantArea.classList.remove('hidden');
        });
    }

    // -------------------------------------------------------
    // Tab Switching
    // -------------------------------------------------------
    const tabs        = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            const tabId = tab.getAttribute('data-tab');
            const targetContent = document.getElementById(`tab-${tabId}`);
            if (targetContent) targetContent.classList.add('active');
        });
    });

    // -------------------------------------------------------
    // Error helper
    // -------------------------------------------------------
    function showError(message) {
        let errEl = document.getElementById('errorMsg');
        if (!errEl) {
            errEl = document.createElement('div');
            errEl.id = 'errorMsg';
            errEl.style.cssText = 'color:#ff6b6b;padding:12px;background:rgba(255,107,107,0.1);border-radius:8px;margin-top:12px;font-size:14px;';
            progressArea.appendChild(errEl);
        }
        errEl.textContent = message;
        errEl.style.display = 'block';
    }
});
