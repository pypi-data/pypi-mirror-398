(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        initDarkMode();
    });

    function initDarkMode() {
        const themeToggle = document.getElementById('theme-toggle');
        const darkStylesheet = document.getElementById('dark-mode-stylesheet');
        const body = document.body;
        
        if (!themeToggle || !darkStylesheet) return;

        const savedTheme = localStorage.getItem('theme') || 'light';
        applyTheme(savedTheme);

        themeToggle.addEventListener('click', function() {
            const currentTheme = body.classList.contains('dark-mode') ? 'dark' : 'light';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            applyTheme(newTheme);
            localStorage.setItem('theme', newTheme);
        });
    }

    function applyTheme(theme) {
        const body = document.body;
        const darkStylesheet = document.getElementById('dark-mode-stylesheet');
        
        if (theme === 'dark') {
            body.classList.add('dark-mode');
            body.setAttribute('data-theme', 'dark');
            if (darkStylesheet) {
                darkStylesheet.media = 'all';
            }
        } else {
            body.classList.remove('dark-mode');
            body.setAttribute('data-theme', 'light');
            if (darkStylesheet) {
                darkStylesheet.media = 'none';
            }
        }
    }
})();

