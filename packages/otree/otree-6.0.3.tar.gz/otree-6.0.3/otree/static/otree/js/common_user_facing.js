function makeReconnectingWebSocket(path) {
    // https://github.com/pladaria/reconnecting-websocket/issues/91#issuecomment-431244323
    var ws_scheme = window.location.protocol === "https:" ? "wss" : "ws";
    var ws_path = ws_scheme + '://' + window.location.host + path;
    return new ReconnectingWebSocket(ws_path);
}

document.addEventListener('DOMContentLoaded', function () {
    let bodyTitle = document.getElementById('_otree-title');
    let bodyTitleText = bodyTitle ? bodyTitle.textContent : '';
    let tabTitle = document.querySelector('title');
    if (bodyTitleText && !tabTitle.textContent) {
        tabTitle.textContent = bodyTitleText;
    } else if (bodyTitleText && isDebug) {
        tabTitle.textContent += ` ${bodyTitleText} [debug]`;
    }

    // block the user from spamming the next button which can make congestion
    // problems worse.
    // i can't use addEventListener on the button itself
    // because disabling the button inside the handler interferes with form
    // submission.
    var form = document.getElementById('form');
    if (form) {
        form.addEventListener('submit', function () {
            document.querySelectorAll('.otree-btn-next').forEach(function (nextButton) {
                var originalState = nextButton.disabled;
                nextButton.disabled = true;
                setTimeout(function () {
                    // restore original state.
                    // it's possible the button was disabled in the first place?
                    nextButton.disabled = originalState;
                }, 5000);
            });
        });
    }
});
