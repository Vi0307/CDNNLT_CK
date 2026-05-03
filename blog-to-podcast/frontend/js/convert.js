document.addEventListener('DOMContentLoaded', () => {
    const convertForm = document.getElementById('convertForm');
    const actionArea = document.getElementById('actionArea');
    const progressArea = document.getElementById('progressArea');
    const aiAssistantArea = document.getElementById('aiAssistantArea');
    const resultBanner = document.getElementById('resultBanner');

    const CONTENT_SERVICE = 'http://localhost:8001';
    const PROCESS_SERVICE = 'http://localhost:8000';
    const TTS_SERVICE = 'http://localhost:8002';

    let currentAudio = null;
    let currentAudioUrl = null;
    let articleTitle = '';

    const convertBtn = document.getElementById('convertBtn');
    if (convertBtn) {
        convertBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            const url = document.getElementById('articleUrl').value.trim();
            const language = document.getElementById('outputLanguage').value;
            if (!url || !language) {
                alert("Vui lòng điền đủ URL và chọn ngôn ngữ.");
                return;
            }

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

    async function runPipeline(url, language) {
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
        articleTitle = crawlData.title;
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
        
        const articleTextEl = document.querySelector('.article-text');
        if (articleTextEl && processData.summary) {
            articleTextEl.innerHTML = `<p>${processData.summary}</p>`;
        }
        completeStep(1);

        // Step 2 — TTS
        activateStep(2);
        const ttsRes = await fetch(`${TTS_SERVICE}/tts`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: ttsText, language })
        });
        if (!ttsRes.ok) throw new Error("TTS service error");
        const ttsData = await ttsRes.json();
        currentAudioUrl = `${TTS_SERVICE}${ttsData.audio_url}`;
        completeStep(2);

        resultBanner.classList.remove('hidden-banner');
        aiAssistantArea.classList.remove('hidden');
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
