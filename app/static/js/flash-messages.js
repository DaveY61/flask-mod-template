document.addEventListener('DOMContentLoaded', function() {
    var flashMessages = document.getElementById('flash-messages');
    if (flashMessages) {
      setTimeout(function() {
        var alerts = flashMessages.getElementsByClassName('alert');
        for (var i = 0; i < alerts.length; i++) {
          var alert = alerts[i];
          var closeButton = alert.querySelector('.btn-close');
          if (closeButton) {
            closeButton.click();
          }
        }
      }, 2000); // Auto-dismiss after x seconds (in milliseconds)
    }
  });