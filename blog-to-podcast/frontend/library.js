document.addEventListener('DOMContentLoaded', () => {
    const libraryContent = document.getElementById('library-content');

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
