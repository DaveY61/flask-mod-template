document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.querySelector('.sidebar');
    const content = document.querySelector('.content-with-sidebar');
    const toggleRows = document.querySelectorAll('.sidebar-toggle-row');

    function updateToggleText() {
        const isCollapsed = sidebar.classList.contains('collapsed');
        toggleRows.forEach(row => {
            if (isCollapsed) {
                row.innerHTML = '<i class="fas fa-chevron-right"></i>';
            } else {
                row.innerHTML = '<span class="sidebar-toggle-text"><i class="fas fa-chevron-left"></i> Collapse</span>';
            }
        });
    }

    function toggleSidebar() {
        sidebar.classList.toggle('collapsed');
        content.classList.toggle('sidebar-collapsed');
        updateToggleText();
    }

    toggleRows.forEach(row => {
        row.addEventListener('click', toggleSidebar);
    });

    // Initialize toggle text
    updateToggleText();

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
                } else {
                    console.error('Invalid action:', action);
                }
            }
        });
    });
});