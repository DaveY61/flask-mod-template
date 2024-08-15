document.addEventListener('DOMContentLoaded', function() {
    var flashMessages = document.getElementById('flash-messages');
    if (flashMessages) {
        var alerts = flashMessages.getElementsByClassName('alert');
        for (var i = 0; i < alerts.length; i++) {
            var alert = alerts[i];
            if (alert.classList.contains('alert-danger')) {
                // Error messages: stay until dismissed
                var closeButton = alert.querySelector('.btn-close');
                if (closeButton) {
                    closeButton.classList.add('btn', 'btn-secondary', 'btn-sm');
                    closeButton.style.opacity = '1';
                }
            } else {
                // Normal messages: auto-dismiss after 2000 ms
                setTimeout(function(alertToClose) {
                    var closeButton = alertToClose.querySelector('.btn-close');
                    if (closeButton) {
                        closeButton.click();
                    }
                }, 2000, alert);
            }
        }
    }
});