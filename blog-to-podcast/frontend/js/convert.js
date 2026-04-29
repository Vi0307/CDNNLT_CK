document.addEventListener('DOMContentLoaded', () => {
    const convertForm = document.getElementById('convertForm');
    const actionArea = document.getElementById('actionArea');
    const progressArea = document.getElementById('progressArea');
    const aiAssistantArea = document.getElementById('aiAssistantArea');
    
    // Form submission simulation
    if (convertForm) {
        convertForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // Check if URL is provided
            const urlInput = document.getElementById('articleUrl');
            if (!urlInput.value) return;

            // Hide action button
            actionArea.classList.add('hidden');
            
            // Show progress and AI assistant areas
            progressArea.classList.remove('hidden');
            aiAssistantArea.classList.remove('hidden');
            
            // Here you could add logic to simulate the step-by-step progress
            // by adding/removing a 'completed' class to the steps over time.
        });
    }

    // Tab Switching Logic
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from all tabs and contents
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            // Add active class to clicked tab
            tab.classList.add('active');

            // Add active class to corresponding content
            const tabId = tab.getAttribute('data-tab');
            const targetContent = document.getElementById(`tab-${tabId}`);
            if (targetContent) {
                targetContent.classList.add('active');
            }
        });
    });
});
