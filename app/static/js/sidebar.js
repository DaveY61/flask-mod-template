document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.querySelector('.sidebar');
    const content = document.querySelector('.content-with-sidebar');
    const toggleRows = document.querySelectorAll('.sidebar-toggle-row');

    function updateToggleContent() {
        const isCollapsed = sidebar.classList.contains('collapsed');
        toggleRows.forEach(row => {
            const icon = row.querySelector('.sidebar-toggle-icon');
            const text = row.querySelector('.sidebar-toggle-text');
            
            if (isCollapsed) {
                text.style.display = 'none';
            } else {
                text.style.display = 'inline';
            }
        });
    }

    function toggleSidebar() {
        sidebar.classList.toggle('collapsed');
        content.classList.toggle('sidebar-collapsed');
        updateToggleContent();
    }

    toggleRows.forEach(row => {
        row.addEventListener('click', toggleSidebar);
    });

    // Initialize toggle content
    updateToggleContent();

    // Add event listeners to sidebar menu items
    document.querySelectorAll('.sidebar-menu a').forEach(item => {
        item.addEventListener('click', function(event) {
            event.preventDefault();
            const action = this.getAttribute('data-action');
            const param = this.getAttribute('data-params');
            
            console.log('Action:', action);
            console.log('Param:', param);

            if (typeof window[action] === 'function') {
                window[action](param);
            } else if (typeof action === 'string') {
                if (action.startsWith('http') || action.startsWith('/')) {
                    window.location.href = action;
                } else if (action === 'showAdminSetup') {
                    // Handle showAdminSetup action
                    window.location.href = `/setup/${param}`;
                } else {
                    console.error('Invalid action:', action);
                }
            }
        });
    });
});