(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        initSidebar();
        initGlobalSearch();
        initMobileMenu();
    });

    function initSidebar() {
        const sidebar = document.getElementById('sidebar');
        const toggle = document.getElementById('sidebar-toggle');
        
        if (!sidebar || !toggle) return;

        toggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            localStorage.setItem('sidebar-collapsed', sidebar.classList.contains('collapsed'));
        });

        const savedState = localStorage.getItem('sidebar-collapsed');
        if (savedState === 'true') {
            sidebar.classList.add('collapsed');
        }
    }

    function initGlobalSearch() {
        const searchInput = document.getElementById('global-search');
        const resultsContainer = document.getElementById('global-search-results');
        
        if (!searchInput || !resultsContainer) return;

        let searchTimeout;
        
        searchInput.addEventListener('input', function() {
            const query = this.value.trim();
            
            clearTimeout(searchTimeout);
            
            if (query.length < 2) {
                resultsContainer.classList.remove('active');
                return;
            }

            searchTimeout = setTimeout(function() {
                fetch(`/admin/global-search/?q=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.results && data.results.length > 0) {
                            displaySearchResults(data.results, resultsContainer);
                            resultsContainer.classList.add('active');
                        } else {
                            resultsContainer.classList.remove('active');
                        }
                    })
                    .catch(error => {
                        console.error('Search error:', error);
                        resultsContainer.classList.remove('active');
                    });
            }, 300);
        });

        document.addEventListener('click', function(e) {
            if (!searchInput.contains(e.target) && !resultsContainer.contains(e.target)) {
                resultsContainer.classList.remove('active');
            }
        });
    }

    function displaySearchResults(results, container) {
        if (!results || results.length === 0) {
            container.innerHTML = '<div class="search-result-item">No results found</div>';
            return;
        }
        
        const grouped = {};
        
        results.forEach(result => {
            const key = `${result.app}.${result.model}`;
            if (!grouped[key]) {
                grouped[key] = {
                    app: result.app,
                    model: result.model,
                    model_verbose: result.model_verbose,
                    items: []
                };
            }
            grouped[key].items.push(result);
        });

        let html = '';
        for (const key in grouped) {
            const group = grouped[key];
            html += `<div class="search-result-group">`;
            html += `<div class="search-result-group-title">${escapeHtml(group.model_verbose)}</div>`;
            group.items.forEach(item => {
                html += `<div class="search-result-item" onclick="window.location.href='${escapeHtml(item.url)}'">`;
                html += `<div class="search-result-text">${highlightText(escapeHtml(item.object_str), searchInput.value)}</div>`;
                html += `<div class="search-result-meta">${escapeHtml(item.app)}.${escapeHtml(item.model)}</div>`;
                html += `</div>`;
            });
            html += `</div>`;
        }

        container.innerHTML = html;
    }
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function highlightText(text, query) {
        if (!query) return text;
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }

    function initMobileMenu() {
        const mobileToggle = document.getElementById('mobile-menu-toggle');
        const sidebar = document.getElementById('sidebar');
        
        if (!mobileToggle || !sidebar) return;

        mobileToggle.addEventListener('click', function() {
            sidebar.classList.toggle('open');
        });

        document.addEventListener('click', function(e) {
            if (!sidebar.contains(e.target) && !mobileToggle.contains(e.target)) {
                sidebar.classList.remove('open');
            }
        });
    }
})();

