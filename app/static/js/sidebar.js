document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.querySelector('.sidebar');
    const content = document.querySelector('.content-with-sidebar');
    const toggleBtn = document.querySelector('.sidebar-toggle');

    if (toggleBtn) {
        toggleBtn.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            content.classList.toggle('sidebar-collapsed');
        });
    }

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