document.addEventListener('DOMContentLoaded', () => {
    const libraryContent = document.getElementById('library-content');

    // Modal Elements
    const modal = document.getElementById('podcast-modal');
    const closeModalBtn = document.getElementById('close-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalMeta = document.getElementById('modal-meta');
    const modalAudio = document.getElementById('modal-audio');
    
    // Summary Tabs in Modal
    const tabOriginal = document.getElementById('modal-tab-original');
    const tabTranslated = document.getElementById('modal-tab-translated');
    const summaryContent = document.getElementById('modal-summary-content');
    
    // Chat in Modal
    const chatMessages = document.getElementById('modal-chat-messages');
    const chatInput = document.getElementById('modal-chat-input');
    const sendChatBtn = document.getElementById('modal-send-chat-btn');

    let currentItem = null;

    // Helper to format text with highlights
    function prepareHighlightableText(text) {
        if (!text) return '<p>Không có nội dung.</p>';
        const tokens = text.match(/[\s\S]*?(?:[.!?]+(?=\s|$)|\n|$)[\s]*/g).filter(t => t.length > 0);
        let html = '<p>';
        let charIndex = 0;
        tokens.forEach(token => {
            html += `<span class="highlightable-word" data-start="${charIndex}" data-end="${charIndex + token.length}" style="transition: background-color 0.15s ease; border-radius: 4px; padding: 2px 0;">${token}</span>`;
            charIndex += token.length;
        });
        html += '</p>';
        return html;
    }

    function loadHistory() {
        const history = JSON.parse(localStorage.getItem('podcastHistory') || '[]');
        
        if (history.length === 0) {
            libraryContent.innerHTML = `
                <div class="empty-state card glass-effect">
                    <i class="fa-solid fa-box-open"></i>
                    <h2>Thư viện trống</h2>
                    <p>Bạn chưa lưu podcast nào. Hãy quay lại trang chủ và chuyển đổi một bài viết!</p>
                </div>
            `;
            return;
        }

        libraryContent.innerHTML = '';
        
        history.forEach((item) => {
            const date = new Date(item.date).toLocaleDateString('vi-VN', {
                year: 'numeric', month: 'short', day: 'numeric',
                hour: '2-digit', minute: '2-digit'
            });
            
            const card = document.createElement('div');
            card.className = 'card glass-effect podcast-card';
            
            card.innerHTML = `
                <button class="delete-btn" data-id="${item.id}" title="Xóa podcast">
                    <i class="fa-solid fa-trash"></i>
                </button>
                <div style="padding-right: 30px;">
                    <h3 title="${item.title}">${item.title}</h3>
                    <div class="podcast-meta">
                        <span><i class="fa-regular fa-clock"></i> ${date}</span>
                        <span><i class="fa-solid fa-language"></i> ${item.language.toUpperCase()}</span>
                    </div>
                    <a href="${item.url}" target="_blank" class="podcast-url" title="${item.url}">
                        <i class="fa-solid fa-link"></i> ${item.url}
                    </a>
                </div>
                <div class="audio-player-container" style="padding: 10px; margin-top: auto;">
                    <audio controls preload="none" style="height: 35px;">
                        <source src="${item.audioUrl}" type="audio/mpeg">
                        Trình duyệt không hỗ trợ thẻ audio.
                    </audio>
                </div>
                <div style="display: flex; gap: 10px; margin-top: 10px;">
                    <a href="${item.audioUrl}" download class="btn btn-secondary" style="flex: 1; padding: 8px; font-size: 0.9rem;">
                        <i class="fa-solid fa-download"></i> Tải MP3
                    </a>
                </div>
            `;
            
            card.addEventListener('click', (e) => {
                // Prevent opening modal if clicking on buttons or links
                if (e.target.closest('button') || e.target.closest('a') || e.target.closest('audio')) {
                    return;
                }
                openModal(item, date);
            });
            
            libraryContent.appendChild(card);
        });
        
        // Add delete event listeners
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.currentTarget.getAttribute('data-id');
                deletePodcast(id);
            });
        });
    }

    // Modal Logic
    function openModal(item, formattedDate) {
        currentItem = item;
        
        modalTitle.textContent = item.title;
        modalMeta.innerHTML = `
            <span><i class="fa-regular fa-clock"></i> ${formattedDate}</span>
            <span><i class="fa-solid fa-language"></i> ${item.language.toUpperCase()}</span>
            <a href="${item.url}" target="_blank" style="color: var(--primary); text-decoration: none;"><i class="fa-solid fa-link"></i> Nguồn bài viết</a>
        `;
        
        // Setup Audio
        modalAudio.src = item.audioUrl;
        
        // Setup Summary Tabs
        tabOriginal.click(); // Default to original
        
        // Reset Chat
        chatMessages.innerHTML = `
            <div class="message ai-message">
                <div class="message-avatar"><i class="fa-solid fa-robot"></i></div>
                <div class="message-bubble">
                    Chào bạn! Tôi là trợ lý AI. Bạn có câu hỏi nào về podcast "${item.title}" không?
                </div>
            </div>
        `;
        chatInput.value = '';
        
        modal.classList.remove('hidden');
    }

    closeModalBtn.addEventListener('click', () => {
        modal.classList.add('hidden');
        modalAudio.pause();
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.add('hidden');
            modalAudio.pause();
        }
    });

    // Tab Switching
    tabOriginal.addEventListener('click', () => {
        tabOriginal.style.background = 'var(--primary)';
        tabOriginal.style.color = 'var(--bg-dark)';
        tabTranslated.style.background = 'transparent';
        tabTranslated.style.color = 'var(--text-muted)';
        if (currentItem) {
            summaryContent.innerHTML = prepareHighlightableText(currentItem.originalSummary);
        }
    });

    tabTranslated.addEventListener('click', () => {
        tabTranslated.style.background = 'var(--primary)';
        tabTranslated.style.color = 'var(--bg-dark)';
        tabOriginal.style.background = 'transparent';
        tabOriginal.style.color = 'var(--text-muted)';
        if (currentItem) {
            summaryContent.innerHTML = prepareHighlightableText(currentItem.translatedSummary);
        }
    });

    // Audio Sync for Highlights
    modalAudio.addEventListener('timeupdate', () => {
        if (!modalAudio.duration || modalAudio.paused || !currentItem) return;
        const progress = modalAudio.currentTime / modalAudio.duration;
        
        const isOriginalActive = tabOriginal.style.background !== 'transparent';
        const activeText = isOriginalActive ? currentItem.originalSummary : currentItem.translatedSummary;
        
        if (!activeText) return;
        
        const targetCharIndex = progress * activeText.length;
        const spans = summaryContent.querySelectorAll('.highlightable-word');
        
        spans.forEach(span => {
            const start = parseInt(span.getAttribute('data-start'));
            const end = parseInt(span.getAttribute('data-end'));
            
            if (targetCharIndex >= start && targetCharIndex <= end) {
                span.style.backgroundColor = '#ffd54f';
                span.style.color = '#000';
            } else {
                span.style.backgroundColor = 'transparent';
                span.style.color = 'inherit';
            }
        });
    });

    // Chat Logic
    sendChatBtn.addEventListener('click', sendChatMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChatMessage();
    });

    function sendChatMessage() {
        const text = chatInput.value.trim();
        if (!text) return;

        addChatMessage(text, 'user-message');
        chatInput.value = '';

        setTimeout(() => {
            addChatMessage('Trong chế độ Thư viện, trợ lý AI đang xem lại bản ghi. Các chức năng phân tích sâu đang được phát triển.', 'ai-message');
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

    function deletePodcast(id) {
        if(confirm('Bạn có chắc chắn muốn xóa podcast này khỏi thư viện?')) {
            let history = JSON.parse(localStorage.getItem('podcastHistory') || '[]');
            history = history.filter(item => item.id !== id);
            localStorage.setItem('podcastHistory', JSON.stringify(history));
            loadHistory();
        }
    }

    // Initial load
    loadHistory();
});
