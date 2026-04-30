document.addEventListener('DOMContentLoaded', () => {
    // Search functionality
    const searchInput = document.querySelector('.search-box input');
    const podcastCards = document.querySelectorAll('.podcast-card');

    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();

            podcastCards.forEach(card => {
                const title = card.querySelector('.podcast-title').textContent.toLowerCase();
                const source = card.querySelector('.podcast-source').textContent.toLowerCase();

                if (title.includes(searchTerm) || source.includes(searchTerm)) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }

    // Delete functionality
    const deleteButtons = document.querySelectorAll('.delete-btn');
    
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            // Optional: confirm before deletion
            if(confirm("Are you sure you want to delete this podcast?")) {
                const card = this.closest('.podcast-card');
                // Add fade out animation
                card.style.transition = 'opacity 0.3s, transform 0.3s';
                card.style.opacity = '0';
                card.style.transform = 'scale(0.9)';
                
                setTimeout(() => {
                    card.remove();
                }, 300);
            }
        });
    });
    
    // Highlight active nav item
    const currentPath = window.location.pathname;
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        const href = item.getAttribute('href');
        if (href && href !== '#' && currentPath.includes(href)) {
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
        }
    });
});
