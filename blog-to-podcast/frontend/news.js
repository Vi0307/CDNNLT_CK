document.addEventListener("DOMContentLoaded", () => {
    const GATEWAY = "http://localhost:8000";

    const topicInput = document.getElementById("topic-input");
    const generateBtn = document.getElementById("generate-btn");
    const btnLoader = document.getElementById("btn-loader");
    const formContainer = document.getElementById("form-container");
    const progressContainer = document.getElementById("progress-container");
    const resultContainer = document.getElementById("result-container");
    const audioPlayer = document.getElementById("audio-player");
    const playPauseBtn = document.getElementById("play-pause-btn");
    const playPauseIcon = playPauseBtn ? playPauseBtn.querySelector("i") : null;
    const waveformContainer = document.getElementById("waveform-container");
    const timeDisplay = document.getElementById("time-display");
    const downloadBtn = document.getElementById("download-btn");
    const saveBtn = document.getElementById("save-btn");
    const resetBtn = document.getElementById("reset-btn");
    const podcastTitle = document.getElementById("podcast-title");
    const topicTag = document.getElementById("topic-tag");
    const articleList = document.getElementById("article-list");
    const articleCount = document.getElementById("article-count");
    const summaryBox = document.getElementById("summary-box");
    const scriptBox = document.getElementById("script-box");
    const scriptToggle = document.getElementById("script-toggle");
    const scriptChevron = document.getElementById("script-chevron");
    const scriptTabs = document.getElementById("script-tabs");
    const tabTranslated = document.getElementById("tab-translated");
    const tabOriginal = document.getElementById("tab-original");
    const langSelect = document.getElementById("lang-select");
    const voiceSelect = document.getElementById("voice-select");
    const errorToast = document.getElementById("error-toast");
    const errorMsg = document.getElementById("error-msg");
    const closeToastBtn = document.getElementById("close-toast-btn");
    const chatMessages = document.getElementById("chat-messages");
    const chatInput = document.getElementById("chat-input");
    const chatSendBtn = document.getElementById("chat-send-btn");
    const selTooltip = document.getElementById("sel-tooltip");
    const explainPopup = document.getElementById("explain-popup");
    const epWord = document.getElementById("ep-word");
    const epLoading = document.getElementById("ep-loading");
    const epContent = document.getElementById("ep-content");
    const epMeaning = document.getElementById("ep-meaning");
    const epExample = document.getElementById("ep-example");
    const epError = document.getElementById("ep-error");
    const epClose = document.getElementById("ep-close");

    const steps = [1, 2, 3, 4].map(i => document.getElementById("step-" + i));

    // Parse preview elements
    const parsePreview = document.getElementById("parse-preview");
    const parseLoading = document.getElementById("parse-loading");
    const parseOk = document.getElementById("parse-ok");
    const parseText = document.getElementById("parse-text");
    const parseKeywords = document.getElementById("parse-keywords");
    const parseReject = document.getElementById("parse-reject");
    const parseRejectMsg = document.getElementById("parse-reject-msg");

    let currentScript = "";
    let currentScriptVi = "";
    let currentContext = "";
    let currentTopic = "";
    let parsedResult = null;   // kết quả từ /parse-news-query
    let parseTimer = null;

    // Realtime detection (client-side, không cần AI)
    const REALTIME_MAP = {
        "gold": ["gold price", "gold sjc", "gold 9999", "gia vang", "vang sjc",
                 "giá vàng", "vàng sjc", "vàng hôm nay", "giá vàng hôm nay"],
        "exchange_rate": ["exchange rate", "usd price", "dollar", "foreign currency", "ty gia", "usd", "eur vnd",
                          "tỷ giá", "giá usd", "đô la hôm nay"],
        "fuel": ["fuel price", "gas price", "oil price", "gia xang", "xang dau", "petrolimex",
                 "giá xăng", "giá xăng hôm nay", "giá dầu", "xăng dầu hôm nay", "giá xăng dầu"],
        "weather": ["weather", "temperature", "forecast", "thoi tiet", "rain", "sunshine",
                    "thời tiết", "nhiệt độ hôm nay", "dự báo thời tiết"],
        "football": ["football", "soccer", "match schedule", "world cup", "premier league", "champions league", "v-league",
                     "lịch thi đấu", "kết quả bóng đá", "bóng đá hôm nay"]
    };

    function detectRealtime(query) {
        const q = query.toLowerCase();
        for (const [rtype, keywords] of Object.entries(REALTIME_MAP)) {
            if (keywords.some(kw => q.includes(kw))) return rtype;
        }
        return null;
    }

    // Category → topic mapping cho news-service
    const categoryToTopic = {
        "chinh-tri": "chính trị", "giao-duc": "giáo dục", "cong-nghe": "công nghệ",
        "y-te": "y tế", "kinh-te": "kinh tế", "the-thao": "thể thao", "giai-tri": "giải trí",
        "the-gioi": "thế giới", "phap-luat": "pháp luật", "moi-truong": "môi trường",
        "bat-dong-san": "bất động sản", "tai-chinh": "tài chính", "xa-hoi": "xã hội",
        "khoa-hoc": "khoa học", "other": "default"
    };

    const voiceMap = {
        vi: [{ value: "vi-VN-Neural2-A", label: "Female Voice (Southern)" }, { value: "vi-VN-Neural2-D", label: "Male Voice (Northern)" }],
        en: [{ value: "en-US-Neural2-F", label: "Female (US English)" }, { value: "en-US-Neural2-J", label: "Male (US English)" }],
        fr: [{ value: "fr-FR-Neural2-A", label: "Female Voice (French)" }, { value: "fr-FR-Neural2-B", label: "Male Voice (French)" }],
        ja: [{ value: "ja-JP-Neural2-A", label: "Female Voice (Japanese)" }, { value: "ja-JP-Neural2-B", label: "Male Voice (Japanese)" }]
    };
    const langLabels = { vi: "Vietnamese", en: "English", fr: "French", ja: "Japanese" };

    langSelect.addEventListener("change", () => {
        const voices = voiceMap[langSelect.value] || voiceMap.vi;
        voiceSelect.innerHTML = voices.map(v => "<option value='" + v.value + "'>" + v.label + "</option>").join("");
    });

    document.querySelectorAll(".chip").forEach(chip => {
        chip.addEventListener("click", () => {
            document.querySelectorAll(".chip").forEach(c => c.classList.remove("active"));
            chip.classList.add("active");
            topicInput.value = chip.dataset.topic;
            triggerParse(chip.dataset.topic);
        });
    });

    // --- Waveform & Audio Player Logic ---
    const NUM_BARS = 70;
    let animationId;

    function generateWaveformBars() {
        if (!waveformContainer) return;
        waveformContainer.innerHTML = '<div class="waveform-progress" id="waveform-progress"></div>';
        for (let i = 0; i < NUM_BARS; i++) {
            const bar = document.createElement('div');
            bar.className = 'waveform-bar';
            const height = 20 + Math.random() * 80;
            bar.style.height = `${height}%`;
            waveformContainer.appendChild(bar);
        }
    }
    generateWaveformBars();

    function animateWaveform() {
        if (!waveformContainer) return;
        const bars = waveformContainer.querySelectorAll('.waveform-bar');
        bars.forEach(bar => {
            if (Math.random() > 0.8) {
                const newHeight = 30 + Math.random() * 70;
                bar.style.height = `${newHeight}%`;
            }
        });
        animationId = requestAnimationFrame(animateWaveform);
    }

    if (playPauseBtn) {
        playPauseBtn.addEventListener('click', () => {
            if (audioPlayer.paused) audioPlayer.play();
            else audioPlayer.pause();
        });
    }

    audioPlayer.addEventListener('play', () => {
        if (playPauseIcon) playPauseIcon.className = 'fa-solid fa-pause';
        animateWaveform();
    });

    audioPlayer.addEventListener('pause', () => {
        if (playPauseIcon) playPauseIcon.className = 'fa-solid fa-play';
        cancelAnimationFrame(animationId);
    });

    audioPlayer.addEventListener('ended', () => {
        if (playPauseIcon) playPauseIcon.className = 'fa-solid fa-play';
        cancelAnimationFrame(animationId);
        const progEl = document.getElementById('waveform-progress');
        if (progEl) progEl.style.width = '0%';
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
        const progEl = document.getElementById('waveform-progress');
        if (progEl) progEl.style.width = `${progress * 100}%`;
        if (timeDisplay) timeDisplay.textContent = `${formatTime(audioPlayer.currentTime)} / ${formatTime(audioPlayer.duration)}`;
    });

    audioPlayer.addEventListener('loadedmetadata', () => {
        if (timeDisplay) timeDisplay.textContent = `0:00 / ${formatTime(audioPlayer.duration)}`;
    });

    if (waveformContainer) {
        waveformContainer.addEventListener('click', (e) => {
            if (!audioPlayer.duration) return;
            const rect = waveformContainer.getBoundingClientRect();
            const pos = (e.clientX - rect.left) / rect.width;
            audioPlayer.currentTime = pos * audioPlayer.duration;
        });
    }

    // Debounce parse khi gõ
    topicInput.addEventListener("input", () => {
        clearTimeout(parseTimer);
        parsedResult = null;
        const q = topicInput.value.trim();
        if (!q) { parsePreview.style.display = "none"; return; }
        parseTimer = setTimeout(() => triggerParse(q), 900);
    });

    async function triggerParse(query) {
        // Detect realtime ngay lập tức (không cần AI)
        const rtType = detectRealtime(query);
        if (rtType) {
            const rtLabels = {
                "gold": "📊 Gold Price (real-time data)",
                "exchange_rate": "💱 Exchange Rate (real-time data)",
                "fuel": "⛽ Fuel Price (real-time data)",
                "weather": "🌤️ Weather (real-time data)",
                "football": "⚽ Football News (real-time data)",
            };
            parsePreview.style.display = "block";
            parseLoading.style.display = "none";
            parseReject.style.display = "none";
            parseText.textContent = rtLabels[rtType] || rtType;
            parseKeywords.innerHTML = "<span style='background:rgba(74,222,128,.15);color:#4ade80;padding:2px 9px;border-radius:8px;font-size:.78rem;font-weight:600;'>Real-time data</span>";
            parseOk.style.display = "block";
            parsedResult = { is_valid_news_topic: true, search_keywords: [], category: "other", realtime_type: rtType };
            return;
        }

        parsePreview.style.display = "block";
        parseLoading.style.display = "block";
        parseOk.style.display = "none";
        parseReject.style.display = "none";
        try {
            const res = await fetch(GATEWAY + "/parse-news-query", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query })
            });
            if (!res.ok) throw new Error();
            const data = await res.json();
            parseLoading.style.display = "none";
            if (!data.is_valid_news_topic) {
                parseReject.style.display = "block";
                parseRejectMsg.textContent = data.rejection_reason || "Không phải chủ đề tin tức.";
                parsedResult = null;
            } else {
                parsedResult = data;
                const catLabel = categoryToTopic[data.category] || data.category;
                parseText.textContent = "Topic: " + catLabel;
                parseKeywords.innerHTML = (data.search_keywords || [])
                    .map(k => "<span style='background:rgba(139,92,246,.18);color:#c4b5fd;padding:2px 9px;border-radius:8px;font-size:.78rem;font-weight:600;'>" + k + "</span>")
                    .join("");
                parseOk.style.display = "block";
            }
        } catch {
            parseLoading.style.display = "none";
            parsePreview.style.display = "none";
        }
    }

    scriptToggle.addEventListener("click", () => {
        const hidden = scriptBox.style.display === "none";
        scriptBox.style.display = hidden ? "" : "none";
        scriptChevron.style.transform = hidden ? "rotate(180deg)" : "";
    });

    tabTranslated.addEventListener("click", () => {
        scriptBox.textContent = currentScript;
        tabTranslated.classList.add("active"); tabOriginal.classList.remove("active");
    });
    tabOriginal.addEventListener("click", () => {
        scriptBox.textContent = currentScriptVi;
        tabOriginal.classList.add("active"); tabTranslated.classList.remove("active");
    });

    document.getElementById("convert-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const query = topicInput.value.trim();
        if (!query) { showError("Vui lòng nhập chủ đề tin tức!"); return; }

        // Nếu parse xác định không hợp lệ → chặn
        if (parsedResult !== null && parsedResult.is_valid_news_topic === false) {
            showError(parsedResult.rejection_reason || "Not a valid news topic.");
            return;
        }

        // Nếu chưa parse → parse ngay trước khi generate
        if (!parsedResult) {
            try {
                const res = await fetch(GATEWAY + "/parse-news-query", {
                    method: "POST", headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ query })
                });
                if (res.ok) {
                    const d = await res.json();
                    if (!d.is_valid_news_topic) {
                        showError(d.rejection_reason || "Not a valid news topic.");
                        return;
                    }
                    parsedResult = d;
                }
            } catch { }
        }

        const topic = parsedResult ? (categoryToTopic[parsedResult.category] || query) : query;
        const keywords = parsedResult ? (parsedResult.search_keywords || []) : [];
        // Detect realtime client-side (nhanh hơn, không tốn API key)
        const rtType = detectRealtime(query);
        currentTopic = topic;
        startUI();

        const timers = [
            setTimeout(() => { setStep(0, "active", rtType ? "Fetching real-time data..." : "Finding articles..."); }, 100),
            setTimeout(() => { setStep(0, "done", "Done"); setStep(1, "active", "Crawling content..."); }, 4500),
            setTimeout(() => { setStep(1, "done", "Done"); setStep(2, "active", "AI synthesizing..."); }, 13000),
            setTimeout(() => { setStep(2, "done", "Done"); setStep(3, "active", "Generating audio..."); }, 35000),
        ];

        try {
            let res, data;
            if (rtType) {
                // Real-time pipeline
                res = await fetch(GATEWAY + "/realtime-podcast", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ query, rtype: rtType, language: langSelect.value, voice: voiceSelect.value })
                });
            } else {
                // News RSS pipeline
                res = await fetch(GATEWAY + "/generate-news-podcast", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ topic, keywords, language: langSelect.value, voice: voiceSelect.value, max_articles: 5 })
                });
            }
            timers.forEach(t => clearTimeout(t));
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || "Error " + res.status);
            }
            data = await res.json();
            // Normalize realtime response để dùng chung showResult
            if (rtType && !data.topic) {
                data.topic = query;
                data.summary = data.raw_data || "";
                data.articles = [];
            }
            // Với realtime, tạo 1 "source" giả từ thông tin scrape
            if (rtType && (!data.articles || data.articles.length === 0)) {
                const sourceMap = {
                    "gold": { title: "Giá vàng SJC - Ngọc Thịnh Jewelry", url: "https://ngocthinh-jewelry.vn/pages/bang-gia-vang", source: "Ngọc Thịnh Jewelry" },
                    "exchange_rate": { title: "Tỷ giá ngoại tệ - Vietcombank", url: "https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx", source: "Vietcombank" },
                    "fuel": { title: "Giá xăng dầu Petrolimex", url: "https://webgia.com/gia-xang-dau/petrolimex/", source: "Petrolimex / webgia.com" },
                    "weather": { title: "Thời tiết - OpenWeatherMap", url: "https://openweathermap.org", source: "OpenWeatherMap" },
                    "football": { title: "Lịch thi đấu bóng đá - Bongda.com.vn", url: "https://bongda.com.vn/lich-thi-dau", source: "Bongda.com.vn" },
                };
                const src = sourceMap[rtType];
                if (src) data.articles = [src];
            }
            steps.forEach(s => { s.className = "p-step active"; s.querySelector("span").textContent = "Done"; });
            showResult(data);
        } catch (err) {
            timers.forEach(t => clearTimeout(t));
            const active = steps.find(s => s.classList.contains("active"));
            if (active) { active.className = "p-step active"; active.querySelector("span").textContent = "Failed"; }
            const isOffline = err instanceof TypeError && (err.message.includes("Failed to fetch") || err.message.includes("NetworkError"));
            showError(isOffline
                ? "⚠️ Cannot connect to server. Make sure Docker is running (docker compose up) and try again!"
                : err.message);
            setTimeout(resetUI, 5000);
        }
    });

    function showResult(data) {
        setTimeout(() => {
            progressContainer.classList.remove("active");
            setTimeout(() => progressContainer.classList.add("hidden"), 500);

            resultContainer.classList.remove("hidden");
            setTimeout(() => resultContainer.classList.add("active"), 10);
            
            // Hide hero to focus on result
            document.getElementById('hero-section').classList.add('hidden');

            podcastTitle.textContent = data.title || ("Podcast: " + data.topic);
            topicTag.textContent = data.topic;
            summaryBox.textContent = data.summary || "";
            currentScript = data.script || "";
            currentScriptVi = data.script_vi || data.script || "";
            currentContext = (data.summary || "") + "\n\n" + currentScriptVi;
            scriptBox.textContent = currentScript;
            scriptBox.style.display = "";
            scriptChevron.style.transform = "rotate(180deg)";
            const lang = langSelect.value;
            if (lang !== "vi") {
                scriptTabs.style.display = "flex";
                tabTranslated.textContent = langLabels[lang] || lang;
                tabOriginal.textContent = "Vietnamese";
                tabTranslated.classList.add("active"); tabOriginal.classList.remove("active");
            } else {
                scriptTabs.style.display = "none";
            }
            const audioUrl = GATEWAY + data.audio_url + "?t=" + Date.now();
            audioPlayer.src = audioUrl; audioPlayer.load();
            downloadBtn.href = audioUrl;
            downloadBtn.download = "podcast-" + data.topic + ".mp3";
            
            // Regenerate bars for new track
            generateWaveformBars();
            if (timeDisplay) timeDisplay.textContent = "0:00 / 0:00";
            const arts = data.articles || [];
            articleCount.textContent = arts.length;
            articleList.innerHTML = "";
            arts.forEach((a, i) => {
                const div = document.createElement("div");
                div.className = "article-card";
                div.innerHTML = "<div class='article-num'>" + (i + 1) + "</div>" +
                    "<div style='flex:1;min-width:0;'><a href='" + escHtml(a.url) + "' target='_blank' rel='noopener'>" + escHtml(a.title) + "</a>" +
                    "<div><span class='source-badge'>" + escHtml(a.source) + "</span></div></div>" +
                    "<a href='" + escHtml(a.url) + "' target='_blank' rel='noopener' style='color:#a78bfa;font-size:.8rem;flex-shrink:0;'><i class='fa-solid fa-arrow-up-right-from-square'></i></a>";
                articleList.appendChild(div);
            });
            chatMessages.innerHTML = "<div class='message'><div class='msg-avatar ai'><i class='fa-solid fa-robot'></i></div>" +
                "<div class='msg-content ai'>I've finished reading <strong>" + arts.length + "</strong> articles about <strong>" + escHtml(data.topic) + "</strong>. What would you like to know?</div></div>";
        }, 600);
    }

    resetBtn.addEventListener("click", resetUI);
    closeToastBtn.addEventListener("click", () => { errorToast.classList.add("hidden"); });

    function generateBtn_startUI() {}
    function startUI() {
        generateBtn.disabled = true;
        generateBtn.querySelector(".btn-text").style.display = "none";
        generateBtn.querySelector("i").style.display = "none";
        btnLoader.classList.remove("hidden");
        formContainer.classList.add("hidden");
        
        progressContainer.classList.remove("hidden");
        setTimeout(() => progressContainer.classList.add("active"), 10);
        
        resultContainer.classList.add("hidden");
        resultContainer.classList.remove("active");

        steps.forEach(s => { s.className = "p-step"; s.querySelector("span").textContent = "Waiting..."; });
    }
    function resetUI() {
        generateBtn.disabled = false;
        generateBtn.querySelector(".btn-text").style.display = "";
        generateBtn.querySelector("i").style.display = "";
        btnLoader.classList.add("hidden");
        formContainer.classList.remove("hidden");
        
        document.getElementById('hero-section').classList.remove('hidden');
        
        progressContainer.classList.remove("active");
        progressContainer.classList.add("hidden");
        
        resultContainer.classList.remove("active");
        resultContainer.classList.add("hidden");

        audioPlayer.pause(); audioPlayer.src = "";
        if (playPauseIcon) playPauseIcon.className = 'fa-solid fa-play';
        cancelAnimationFrame(animationId);
        if (timeDisplay) timeDisplay.textContent = "0:00 / 0:00";
        const progEl = document.getElementById('waveform-progress');
        if (progEl) progEl.style.width = '0%';

        currentScript = currentScriptVi = currentContext = "";
        parsedResult = null;
        parsePreview.style.display = "none";
    }
    function setStep(idx, status, msg) {
        if (!steps[idx]) return;
        steps[idx].className = "p-step " + (status === "active" || status === "done" ? "active" : "");
        steps[idx].querySelector("span").textContent = msg;
    }
    function showError(msg) {
        errorMsg.textContent = msg;
        errorToast.classList.remove("hidden");
        errorToast.classList.add("show");
        setTimeout(() => { errorToast.classList.remove("show"); errorToast.classList.add("hidden"); }, 7000);
    }

    chatSendBtn.addEventListener("click", sendChat);
    chatInput.addEventListener("keypress", e => { if (e.key === "Enter") sendChat(); });

    // buildContext: cắt thông minh theo từ khóa câu hỏi
    function buildContext(text, question) {
        if (!text) return "";
        const MAX_TOTAL = 4500;
        const HEAD_SIZE = 500;
        const KEYWORD_MAX = 2000;
        const TAIL_SIZE = 300;
        const STOPWORDS = new Set(["la", "va", "co", "khong", "cua", "trong", "ve", "de", "cho",
            "voi", "cac", "mot", "nhung", "nay", "do", "duoc", "tu", "theo", "khi", "hay", "hoac",
            "thi", "ma", "nen", "vi", "do", "boi", "tai", "ra", "vao", "len", "xuong", "da", "se",
            "dang", "rat", "cung", "con", "day", "kia", "nhu", "hon", "nhat", "bao", "nhieu",
            "là", "và", "có", "không", "của", "trong", "về", "để", "cho", "với", "các", "một",
            "những", "này", "đó", "được", "từ", "theo", "khi", "hay", "hoặc", "thì", "mà",
            "nên", "vì", "bởi", "tại", "ra", "vào", "lên", "xuống", "đã", "sẽ", "đang", "rất",
            "cũng", "còn", "đây", "kia", "như", "hơn", "nhất"]);

        const keywords = question.toLowerCase()
            .replace(/[?!.,;:]/g, " ")
            .split(/\s+/)
            .filter(w => w.length > 1 && !STOPWORDS.has(w));

        if (keywords.length === 0) {
            if (text.length <= MAX_TOTAL) return text;
            return text.slice(0, 2000) + "\n...\n" + text.slice(-1000);
        }

        const paragraphs = text.split(/\n\n|\n/).filter(p => p.trim().length > 0);
        const head = text.slice(0, HEAD_SIZE);
        const tail = text.length > HEAD_SIZE + TAIL_SIZE ? text.slice(-TAIL_SIZE) : "";

        const matchedParagraphs = [];
        let keywordChars = 0;
        for (const para of paragraphs) {
            const lower = para.toLowerCase();
            const hasKeyword = keywords.some(kw => lower.includes(kw));
            if (hasKeyword && keywordChars < KEYWORD_MAX) {
                matchedParagraphs.push(para);
                keywordChars += para.length;
            }
        }

        const parts = [head];
        if (matchedParagraphs.length > 0) {
            const kSection = matchedParagraphs.join("\n");
            if (!head.includes(kSection.slice(0, 50))) parts.push(kSection);
        }
        if (tail && !head.includes(tail.slice(0, 50))) parts.push(tail);

        let result = parts.join("\n...\n");
        if (result.length > MAX_TOTAL) result = result.slice(0, MAX_TOTAL);
        return result;
    }

    async function sendChat() {
        const text = chatInput.value.trim();
        if (!text || !currentContext) return;
        addMsg(text, "user"); chatInput.value = ""; chatSendBtn.disabled = true;
        const loadId = "load-" + Date.now();
        addMsg("<i class='fa-solid fa-spinner fa-spin'></i>", "ai", loadId, true);
        try {
            const res = await fetch(GATEWAY + "/chat", {
                method: "POST", headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question: text, context: buildContext(currentContext, text), language: langSelect.value })
            });
            const data = await res.json();
            document.getElementById(loadId)?.remove();
            const conf = data.confidence || "low";
            const confColor = conf === "high" ? "#4ade80" : conf === "medium" ? "#fbbf24" : "#94a3b8";
            const confLabel = conf === "high" ? "Chac chan" : conf === "medium" ? "Kha chac" : "Khong chac";
            let html = "<div>" + renderMd(data.answer || "Khong co cau tra loi.") + "</div>";
            if (data.source) html += "<div class='src-quote'>\"" + escHtml(data.source) + "\"</div>";
            html += "<div class='conf-badge' style='color:" + confColor + ";'>● " + confLabel + "</div>";
            addMsg(html, "ai", null, true);
        } catch (err) {
            document.getElementById(loadId)?.remove();
            const isOffline = err instanceof TypeError && (err.message.includes("Failed to fetch") || err.message.includes("NetworkError"));
            addMsg(isOffline ? "⚠️ Server chưa chạy. Vui lòng khởi động Docker!" : "Loi: " + err.message, "ai");
        } finally { chatSendBtn.disabled = false; }
    }
    function addMsg(content, type, id, isHtml) {
        const wrap = document.createElement("div");
        const fullType = type === "user" ? "user-message" : "ai-message";
        wrap.className = `message ${fullType}`;
        if (id) wrap.id = id;
        
        const av = document.createElement("div"); 
        av.className = "msg-avatar";
        av.innerHTML = type === "user" ? "<i class='fa-solid fa-user'></i>" : "<i class='fa-solid fa-robot'></i>";
        
        const bub = document.createElement("div"); 
        bub.className = "msg-bubble";
        if (isHtml) bub.innerHTML = content; else bub.textContent = content;
        
        wrap.appendChild(av); 
        wrap.appendChild(bub);
        chatMessages.appendChild(wrap); 
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    document.addEventListener("mouseup", e => {
        if (explainPopup.contains(e.target) || selTooltip.contains(e.target)) return;
        const sel = window.getSelection(); const word = sel ? sel.toString().trim() : "";
        if (word.length < 2 || word.length > 200) { selTooltip.style.display = "none"; return; }
        const zones = [scriptBox, summaryBox]; let inZone = false;
        try { const r = sel.getRangeAt(0); inZone = zones.some(z => z && z.contains(r.commonAncestorContainer)); } catch (_) { }
        if (!inZone) { selTooltip.style.display = "none"; return; }
        try {
            const r = sel.getRangeAt(0); const rect = r.getBoundingClientRect();
            selTooltip.style.display = "block";
            selTooltip.style.left = Math.max(8, rect.left + rect.width / 2 - 55) + "px";
            selTooltip.style.top = (rect.top - 44 + window.scrollY) + "px";
            selTooltip.dataset.word = word;
        } catch (_) { }
    });
    selTooltip.addEventListener("click", async () => {
        const word = selTooltip.dataset.word; if (!word) return;
        selTooltip.style.display = "none"; window.getSelection()?.removeAllRanges();
        epWord.textContent = '"' + word + '"';
        epLoading.style.display = "block"; epContent.style.display = "none"; epError.style.display = "none";
        explainPopup.style.display = "block";
        explainPopup.style.left = Math.min(window.innerWidth - 330, Math.max(10, window.innerWidth / 2 - 155)) + "px";
        explainPopup.style.top = Math.max(10, window.innerHeight / 2 - 100 + window.scrollY) + "px";
        try {
            const res = await fetch(GATEWAY + "/explain", {
                method: "POST", headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ word, context: currentContext.slice(0, 3000), language: langSelect.value })
            });
            if (!res.ok) throw new Error("Loi " + res.status);
            const data = await res.json();
            epMeaning.innerHTML = "<strong>Nghia:</strong> " + escHtml(data.meaning || "—");
            epExample.innerHTML = data.example ? "Vi du: " + escHtml(data.example) : "";
            epLoading.style.display = "none"; epContent.style.display = "block";
        } catch (err) {
            epLoading.style.display = "none"; epError.style.display = "block";
            epError.textContent = "Khong giai thich duoc: " + err.message;
        }
    });
    epClose.addEventListener("click", () => { explainPopup.style.display = "none"; });
    document.addEventListener("mousedown", e => {
        if (!explainPopup.contains(e.target) && !selTooltip.contains(e.target)) explainPopup.style.display = "none";
        if (!selTooltip.contains(e.target)) selTooltip.style.display = "none";
    });

    function escHtml(s) {
        return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }

    // Chuyển Markdown đơn giản → HTML (bold, italic, bullet, xuống dòng)
    function renderMd(s) {
        let t = escHtml(String(s));
        // **bold** → <strong>
        t = t.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
        // *italic* → <em>
        t = t.replace(/\*(.+?)\*/g, "<em>$1</em>");
        // dòng bắt đầu bằng - hoặc • → <li>
        t = t.replace(/^[\-•]\s+(.+)$/gm, "<li>$1</li>");
        if (t.includes("<li>")) t = "<ul style='margin:6px 0 0 16px;padding:0;'>" + t + "</ul>";
        // Xuống dòng → <br>
        t = t.replace(/\n/g, "<br>");
        return t;
    }
});
