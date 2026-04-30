document.addEventListener('DOMContentLoaded', () => {
    const convertForm = document.getElementById('convertForm');
    const actionArea = document.getElementById('actionArea');
    const progressArea = document.getElementById('progressArea');
    const aiAssistantArea = document.getElementById('aiAssistantArea');
    const resultBanner = document.getElementById('resultBanner');
    
    // Form submission simulation
    if (convertForm) {
        convertForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // Check if URL is provided
            const urlInput = document.getElementById('articleUrl');
            if (!urlInput.value) return;

            // Hide action button
            actionArea.classList.add('hidden');
            
            // Show progress area
            progressArea.classList.remove('hidden');
            
            // Start simulation
            simulateProgress();
        });
    }

    async function simulateProgress() {
        // Step 0: Crawling
        await activateStep(0);
        await new Promise(r => setTimeout(r, 1500));
        completeStep(0);

        // Step 1: AI Processing
        await activateStep(1);
        await new Promise(r => setTimeout(r, 2000));
        completeStep(1);

        // Step 2: Audio Generation
        await activateStep(2);
        await new Promise(r => setTimeout(r, 2000));
        completeStep(2);

        // Show Result and AI Assistant
        resultBanner.classList.remove('hidden-banner');
        resultBanner.classList.add('fade-in');
        
        setTimeout(() => {
            aiAssistantArea.classList.remove('hidden');
            aiAssistantArea.classList.add('fade-in');
        }, 500);
    }

    function activateStep(index) {
        const step = document.getElementById(`step-${index}`);
        if (!step) return;
        step.classList.add('active');
        const icon = step.querySelector('.step-icon i');
        if (icon) icon.className = 'fas fa-spinner fa-spin';
    }

    function completeStep(index) {
        const step = document.getElementById(`step-${index}`);
        if (!step) return;
        step.classList.remove('active');
        step.classList.add('completed');
        const icon = step.querySelector('.step-icon i');
        if (icon) icon.className = 'fas fa-check';
        
        // Color the line
        const line = document.getElementById(`line-${index}`);
        if (line) {
            line.classList.add('completed-line');
        }
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

    // Text Selection Logic for Explain Tab
    const articleTextContainer = document.querySelector('.article-text');
    const explainPopup = document.getElementById('explainPopup');
    const popupSelectedText = document.getElementById('popupSelectedText');
    const closePopupBtn = document.getElementById('closePopupBtn');
    const explainTermBtn = document.getElementById('explainTermBtn');
    const explanationText = document.getElementById('explanationText');

    if (articleTextContainer && explainPopup) {
        document.addEventListener('mouseup', (e) => {
            // Only trigger if we are in the explain tab
            const explainTabContent = document.getElementById('tab-explain');
            if (!explainTabContent || !explainTabContent.classList.contains('active')) {
                return;
            }

            // Don't hide popup if clicking inside it
            if (explainPopup.contains(e.target)) return;

            const selection = window.getSelection();
            const selectedText = selection.toString().trim();

            if (selectedText.length > 0 && articleTextContainer.contains(selection.anchorNode)) {
                // Get bounding rect of the selection
                const range = selection.getRangeAt(0);
                const rect = range.getBoundingClientRect();

                // Position the popup
                explainPopup.style.left = `${rect.left + window.scrollX + (rect.width / 2) - 160}px`; // center it (width is 320)
                explainPopup.style.top = `${rect.bottom + window.scrollY + 10}px`;
                
                // Keep it within screen bounds roughly
                const popupLeft = parseInt(explainPopup.style.left);
                if (popupLeft < 10) explainPopup.style.left = '10px';
                
                // Set text
                popupSelectedText.textContent = `"${selectedText}"`;
                
                // Reset states
                explainTermBtn.classList.remove('hidden');
                explanationText.classList.add('hidden');
                explanationText.innerHTML = '';
                
                explainPopup.classList.remove('hidden');
                // Small timeout to allow display:block to apply before animating opacity
                setTimeout(() => explainPopup.classList.add('show'), 10);
            } else {
                hidePopup();
            }
        });
        
        closePopupBtn.addEventListener('click', () => {
            hidePopup();
            window.getSelection().removeAllRanges();
        });

        explainTermBtn.addEventListener('click', () => {
            explainTermBtn.classList.add('hidden');
            explanationText.classList.remove('hidden');
            explanationText.innerHTML = `<i class="fas fa-spinner fa-spin" style="margin-right: 8px;"></i> Generating explanation...`;
            
            // Simulate AI delay
            setTimeout(() => {
                const term = popupSelectedText.textContent.replace(/"/g, '');
                explanationText.innerHTML = `<strong>"${term}"</strong> — This term refers to a concept discussed in the article. In this context, it describes a key aspect of the topic being covered, relating to how modern systems process and transform content efficiently.`;
            }, 1000);
        });

        function hidePopup() {
            explainPopup.classList.remove('show');
            setTimeout(() => {
                if (!explainPopup.classList.contains('show')) {
                    explainPopup.classList.add('hidden');
                }
            }, 200); // match transition duration
        }
    }
});
