document.addEventListener('DOMContentLoaded', function() {
  var flashMessages = document.getElementById('flash-messages');
  if (flashMessages) {
      var alerts = flashMessages.getElementsByClassName('alert');
      for (var i = 0; i < alerts.length; i++) {
          var alert = alerts[i];
          if (!alert.classList.contains('no-auto-dismiss')) {
              setTimeout(function(alertToClose) {
                  var closeButton = alertToClose.querySelector('.btn-close');
                  if (closeButton) {
                      closeButton.click();
                  }
              }, 2000, alert); // Auto-dismiss after 2 seconds for messages without 'no-auto-dismiss' class
          } else {
              // For 'no-auto-dismiss' messages, we'll add a custom close button
              var closeButton = alert.querySelector('.btn-close');
              if (closeButton) {
                  closeButton.classList.add('btn', 'btn-secondary', 'btn-sm');
                  closeButton.style.opacity = '1';
              }
          }
      }
  }
});