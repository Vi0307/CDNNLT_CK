document.addEventListener("DOMContentLoaded", () => {
    const GATEWAY = "http://localhost:8000";

    const topicInput      = document.getElementById("topic-input");
    const generateBtn     = document.getElementById("generate-btn");
    const btnLoader       = document.getElementById("btn-loader");
    const formContainer   = document.getElementById("form-container");
    const progressContainer = document.getElementById("progress-container");
    const resultContainer = document.getElementById("result-container");
    const audioPlayer     = document.getElementById("audio-player");
    const downloadBtn     = document.getElementById("download-btn");
    const saveBtn         = document.getElementById("save-btn");
    const resetBtn        = document.getElementById("reset-btn");
    const podcastTitle    = document.getElementById("podcast-title");
    const topicTag        = document.getElementById("topic-tag");
    const articleList     = document.getElementById("article-list");
    const articleCount    = document.getElementById("article-count");
    const summaryBox      = document.getElementById("summary-box");
    const scriptBox       = document.getElementById("script-box");
    const scriptToggle    = document.getElementById("script-toggle");
    const scriptChevron   = document.getElementById("script-chevron");
    const scriptTabs      = document.getElementById("script-tabs");
    const tabTranslated   = document.getElementById("tab-translated");
    const tabOriginal     = document.getElementById("tab-original");
    const langSelect      = document.getElementById("lang-select");
    const voiceSelect     = document.getElementById("voice-select");
    const errorToast      = document.getElementById("error-toast");
    const errorMsg        = document.getElementById("error-msg");
    const closeToastBtn   = document.getElementById("close-toast-btn");
    const chatMessages    = document.getElementById("chat-messages");
    const chatInput       = document.getElementById("chat-input");
    const chatSendBtn     = document.getElementById("chat-send-btn");
    const selTooltip      = document.getElementById("sel-tooltip");
    const explainPopup    = document.getElementById("explain-popup");
    const epWord          = document.getElementById("ep-word");
    const epLoading       = document.getElementById("ep-loading");
    const epContent       = document.getElementById("ep-content");
    const epMeaning       = document.getElementById("ep-meaning");
    const epExample       = document.getElementById("ep-example");
    const epError         = document.getElementById("ep-error");
    const epClose         = document.getElementById("ep-close");

    const steps = [1,2,3,4].map(i => document.getElementById("step-" + i));

    let currentScript   = "";
    let currentScriptVi = "";
    let currentContext  = "";
    let currentTopic    = "";

    const voiceMap = {
        vi: [{value:"vi-VN-Neural2-A",label:"Giong Nu (Mien Nam)"},{value:"vi-VN-Neural2-D",label:"Giong Nam (Mien Bac)"}],
        en: [{value:"en-US-Neural2-F",label:"Female (US English)"},{value:"en-US-Neural2-J",label:"Male (US English)"}],
        fr: [{value:"fr-FR-Neural2-A",label:"Giong Nu (Phap)"},{value:"fr-FR-Neural2-B",label:"Giong Nam (Phap)"}],
        ja: [{value:"ja-JP-Neural2-A",label:"Giong Nu (Nhat)"},{value:"ja-JP-Neural2-B",label:"Giong Nam (Nhat)"}]
    };
    const langLabels = {vi:"Tieng Viet",en:"English",fr:"Francais",ja:"Nhat"};

    langSelect.addEventListener("change", () => {
        const voices = voiceMap[langSelect.value] || voiceMap.vi;
        voiceSelect.innerHTML = voices.map(v => "<option value='" + v.value + "'>" + v.label + "</option>").join("");
    });

    document.querySelectorAll(".chip").forEach(chip => {
        chip.addEventListener("click", () => {
            document.querySelectorAll(".chip").forEach(c => c.classList.remove("active"));
            chip.classList.add("active");
            topicInput.value = chip.dataset.topic;
        });
    });

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

    generateBtn.addEventListener("click", async () => {
        const topic = topicInput.value.trim();
        if (!topic) { showError("Vui long nhap chu de tin tuc!"); return; }
        currentTopic = topic;
        startUI();

        const timers = [
            setTimeout(() => { setStep(0,"active","Dang tim bai bao..."); }, 100),
            setTimeout(() => { setStep(0,"done","Hoan tat"); setStep(1,"active","Dang crawl noi dung..."); }, 4500),
            setTimeout(() => { setStep(1,"done","Hoan tat"); setStep(2,"active","AI dang tong hop..."); }, 13000),
            setTimeout(() => { setStep(2,"done","Hoan tat"); setStep(3,"active","Dang tao audio..."); }, 35000),
        ];

        try {
            const res = await fetch(GATEWAY + "/generate-news-podcast", {
                method: "POST",
                headers: {"Content-Type":"application/json"},
                body: JSON.stringify({topic, language:langSelect.value, voice:voiceSelect.value, max_articles:5})
            });
            timers.forEach(t => clearTimeout(t));
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || "Loi " + res.status);
            }
            const data = await res.json();
            steps.forEach(s => { s.className = "step done"; s.querySelector(".status-text").textContent = "Hoan tat"; });
            showResult(data);
        } catch(err) {
            timers.forEach(t => clearTimeout(t));
            const active = steps.find(s => s.classList.contains("active"));
            if (active) { active.className = "step error"; active.querySelector(".status-text").textContent = "That bai"; }
            showError(err.message);
            setTimeout(resetUI, 3500);
        }
    });

    function showResult(data) {
        setTimeout(() => {
            progressContainer.classList.add("hidden");
            resultContainer.classList.remove("hidden");
            podcastTitle.textContent = data.title || ("Podcast: " + data.topic);
            topicTag.textContent = data.topic;
            summaryBox.textContent = data.summary || "";
            currentScript   = data.script    || "";
            currentScriptVi = data.script_vi || data.script || "";
            currentContext  = (data.summary || "") + "\n\n" + currentScriptVi;
            scriptBox.textContent = currentScript;
            scriptBox.style.display = "";
            scriptChevron.style.transform = "rotate(180deg)";
            const lang = langSelect.value;
            if (lang !== "vi") {
                scriptTabs.style.display = "flex";
                tabTranslated.textContent = langLabels[lang] || lang;
                tabOriginal.textContent   = "Tieng Viet";
                tabTranslated.classList.add("active"); tabOriginal.classList.remove("active");
            } else {
                scriptTabs.style.display = "none";
            }
            const audioUrl = GATEWAY + data.audio_url + "?t=" + Date.now();
            audioPlayer.src = audioUrl; audioPlayer.load();
            downloadBtn.href = audioUrl;
            downloadBtn.download = "podcast-" + data.topic + ".mp3";
            const arts = data.articles || [];
            articleCount.textContent = arts.length;
            articleList.innerHTML = "";
            arts.forEach((a, i) => {
                const div = document.createElement("div");
                div.className = "article-card";
                div.innerHTML = "<div class='article-num'>" + (i+1) + "</div>" +
                    "<div style='flex:1;min-width:0;'><a href='" + escHtml(a.url) + "' target='_blank' rel='noopener'>" + escHtml(a.title) + "</a>" +
                    "<div><span class='source-badge'>" + escHtml(a.source) + "</span></div></div>" +
                    "<a href='" + escHtml(a.url) + "' target='_blank' rel='noopener' style='color:#a78bfa;font-size:.8rem;flex-shrink:0;'><i class='fa-solid fa-arrow-up-right-from-square'></i></a>";
                articleList.appendChild(div);
            });
            chatMessages.innerHTML = "<div class='chat-msg'><div class='chat-avatar ai'><i class='fa-solid fa-robot'></i></div>" +
                "<div class='chat-bubble ai'>Toi da doc xong <strong>" + arts.length + "</strong> bai bao ve chu de <strong>" + escHtml(data.topic) + "</strong>. Ban muon hoi gi?</div></div>";
        }, 600);
    }

    resetBtn.addEventListener("click", resetUI);
    closeToastBtn.addEventListener("click", () => { errorToast.classList.add("hidden"); });
    saveBtn.addEventListener("click", () => {
        const h = JSON.parse(localStorage.getItem("podcastHistory") || "[]");
        h.unshift({id:Date.now().toString(), url:"news:"+currentTopic, title:podcastTitle.textContent, date:new Date().toISOString(), language:langSelect.value, audioUrl:audioPlayer.src, originalSummary:summaryBox.textContent});
        localStorage.setItem("podcastHistory", JSON.stringify(h));
        saveBtn.innerHTML = "<i class='fa-solid fa-check'></i> Da luu!";
        saveBtn.style.background = "#4ade80"; saveBtn.style.color = "#000";
        setTimeout(() => { saveBtn.innerHTML = "<i class='fa-solid fa-bookmark'></i> Luu vao thu vien"; saveBtn.style.background=""; saveBtn.style.color=""; }, 2500);
    });

    function startUI() {
        generateBtn.disabled = true;
        generateBtn.querySelector(".btn-text").style.display = "none";
        generateBtn.querySelector("i").style.display = "none";
        btnLoader.classList.remove("hidden");
        formContainer.classList.add("hidden");
        progressContainer.classList.remove("hidden");
        resultContainer.classList.add("hidden");
        steps.forEach(s => { s.className = "step pending"; s.querySelector(".status-text").textContent = "Dang cho..."; });
    }
    function resetUI() {
        generateBtn.disabled = false;
        generateBtn.querySelector(".btn-text").style.display = "";
        generateBtn.querySelector("i").style.display = "";
        btnLoader.classList.add("hidden");
        formContainer.classList.remove("hidden");
        progressContainer.classList.add("hidden");
        resultContainer.classList.add("hidden");
        audioPlayer.pause(); audioPlayer.src = "";
        currentScript = currentScriptVi = currentContext = "";
    }
    function setStep(idx, status, msg) {
        if (!steps[idx]) return;
        steps[idx].className = "step " + status;
        steps[idx].querySelector(".status-text").textContent = msg;
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
        const MAX_TOTAL   = 4500;
        const HEAD_SIZE   = 500;
        const KEYWORD_MAX = 2000;
        const TAIL_SIZE   = 300;
        const STOPWORDS = new Set(["la","va","co","khong","cua","trong","ve","de","cho",
            "voi","cac","mot","nhung","nay","do","duoc","tu","theo","khi","hay","hoac",
            "thi","ma","nen","vi","do","boi","tai","ra","vao","len","xuong","da","se",
            "dang","rat","cung","con","day","kia","nhu","hon","nhat","bao","nhieu",
            "là","và","có","không","của","trong","về","để","cho","với","các","một",
            "những","này","đó","được","từ","theo","khi","hay","hoặc","thì","mà",
            "nên","vì","bởi","tại","ra","vào","lên","xuống","đã","sẽ","đang","rất",
            "cũng","còn","đây","kia","như","hơn","nhất"]);

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
                method:"POST", headers:{"Content-Type":"application/json"},
                body: JSON.stringify({question:text, context:buildContext(currentContext, text), language:langSelect.value})
            });
            const data = await res.json();
            document.getElementById(loadId)?.remove();
            const conf = data.confidence || "low";
            const confColor = conf==="high"?"#4ade80":conf==="medium"?"#fbbf24":"#94a3b8";
            const confLabel = conf==="high"?"Chac chan":conf==="medium"?"Kha chac":"Khong chac";
            let html = "<div>" + escHtml(data.answer||"Khong co cau tra loi.") + "</div>";
            if (data.source) html += "<div class='src-quote'>\"" + escHtml(data.source) + "\"</div>";
            html += "<div class='conf-badge' style='color:" + confColor + ";'>● " + confLabel + "</div>";
            addMsg(html, "ai", null, true);
        } catch(err) {
            document.getElementById(loadId)?.remove();
            addMsg("Loi: " + err.message, "ai");
        } finally { chatSendBtn.disabled = false; }
    }
    function addMsg(content, type, id, isHtml) {
        const wrap = document.createElement("div");
        wrap.className = "chat-msg" + (type==="user"?" user":"");
        if (id) wrap.id = id;
        const av = document.createElement("div"); av.className = "chat-avatar " + type;
        av.innerHTML = type==="user"?"<i class='fa-solid fa-user'></i>":"<i class='fa-solid fa-robot'></i>";
        const bub = document.createElement("div"); bub.className = "chat-bubble " + type;
        if (isHtml) bub.innerHTML = content; else bub.textContent = content;
        wrap.appendChild(av); wrap.appendChild(bub);
        chatMessages.appendChild(wrap); chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    document.addEventListener("mouseup", e => {
        if (explainPopup.contains(e.target) || selTooltip.contains(e.target)) return;
        const sel = window.getSelection(); const word = sel ? sel.toString().trim() : "";
        if (word.length < 2 || word.length > 200) { selTooltip.style.display = "none"; return; }
        const zones = [scriptBox, summaryBox]; let inZone = false;
        try { const r = sel.getRangeAt(0); inZone = zones.some(z => z && z.contains(r.commonAncestorContainer)); } catch(_) {}
        if (!inZone) { selTooltip.style.display = "none"; return; }
        try {
            const r = sel.getRangeAt(0); const rect = r.getBoundingClientRect();
            selTooltip.style.display = "block";
            selTooltip.style.left = Math.max(8, rect.left + rect.width/2 - 55) + "px";
            selTooltip.style.top  = (rect.top - 44 + window.scrollY) + "px";
            selTooltip.dataset.word = word;
        } catch(_) {}
    });
    selTooltip.addEventListener("click", async () => {
        const word = selTooltip.dataset.word; if (!word) return;
        selTooltip.style.display = "none"; window.getSelection()?.removeAllRanges();
        epWord.textContent = '"' + word + '"';
        epLoading.style.display = "block"; epContent.style.display = "none"; epError.style.display = "none";
        explainPopup.style.display = "block";
        explainPopup.style.left = Math.min(window.innerWidth-330, Math.max(10, window.innerWidth/2-155)) + "px";
        explainPopup.style.top  = Math.max(10, window.innerHeight/2-100+window.scrollY) + "px";
        try {
            const res = await fetch(GATEWAY + "/explain", {
                method:"POST", headers:{"Content-Type":"application/json"},
                body: JSON.stringify({word, context:currentContext.slice(0,3000), language:langSelect.value})
            });
            if (!res.ok) throw new Error("Loi " + res.status);
            const data = await res.json();
            epMeaning.innerHTML = "<strong>Nghia:</strong> " + escHtml(data.meaning||"—");
            epExample.innerHTML = data.example ? "Vi du: " + escHtml(data.example) : "";
            epLoading.style.display = "none"; epContent.style.display = "block";
        } catch(err) {
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
        return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
    }
});
