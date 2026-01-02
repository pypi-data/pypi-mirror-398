// Dark Theme Loader for Read the Docs
// This ensures the dark theme loads properly on Read the Docs

(function() {
    'use strict';

    // Function to apply dark theme
    function applyDarkTheme() {
        // Add dark theme class to html and body
        document.documentElement.classList.add('dark-theme');
        document.body.classList.add('dark-theme');

        // Force dark theme on all elements that might have been missed
        const elements = document.querySelectorAll('*');
        elements.forEach(function(el) {
            if (el.style && el.style.backgroundColor === 'white') {
                el.style.backgroundColor = '#2d2d2d';
            }
            if (el.style && el.style.color === 'black') {
                el.style.color = '#e0e0e0';
            }
        });

        // Ensure proper CSS loading
        const darkCSS = document.querySelector('link[href*="dark_theme.css"]');
        if (darkCSS) {
            darkCSS.disabled = false;
        }
    }

    // Apply theme immediately
    applyDarkTheme();

    // Apply theme when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyDarkTheme);
    }

    // Apply theme when everything is loaded
    window.addEventListener('load', applyDarkTheme);

    // Watch for any dynamic content changes
    if (window.MutationObserver) {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    // Reapply theme to new elements
                    setTimeout(applyDarkTheme, 100);
                }
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

})();
