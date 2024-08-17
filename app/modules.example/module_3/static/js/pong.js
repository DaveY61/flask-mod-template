let playerY = 160;
let aiY = 160;
let ballX = 300;
let ballY = 200;
let ballSpeedX = 3;
let ballSpeedY = 3;

function initPong() {
    const pongElement = document.getElementById('pong');
    pongElement.innerHTML = `
        <div id="player-paddle" class="paddle"></div>
        <div id="ai-paddle" class="paddle"></div>
        <div id="ball"></div>
    `;

    document.addEventListener('mousemove', movePaddle);
    requestAnimationFrame(updatePong);
}

function movePaddle(e) {
    const pongRect = document.getElementById('pong').getBoundingClientRect();
    playerY = e.clientY - pongRect.top - 40;
    if (playerY < 0) playerY = 0;
    if (playerY > 320) playerY = 320;
}

function updatePong() {
    // Move the ball
    ballX += ballSpeedX;
    ballY += ballSpeedY;

    // Ball collision with top and bottom
    if (ballY < 0 || ballY > 390) {
        ballSpeedY = -ballSpeedY;
    }

    // Ball collision with paddles
    if (ballX < 20 && ballY > playerY && ballY < playerY + 80) {
        ballSpeedX = -ballSpeedX;
    }
    if (ballX > 580 && ballY > aiY && ballY < aiY + 80) {
        ballSpeedX = -ballSpeedX;
    }

    // AI paddle movement
    if (aiY + 40 < ballY) {
        aiY += 3;
    } else if (aiY + 40 > ballY) {
        aiY -= 3;
    }

    // Reset ball if it goes out of bounds
    if (ballX < 0 || ballX > 600) {
        ballX = 300;
        ballY = 200;
    }

    // Update positions
    document.getElementById('player-paddle').style.top = `${playerY}px`;
    document.getElementById('ai-paddle').style.top = `${aiY}px`;
    document.getElementById('ball').style.left = `${ballX}px`;
    document.getElementById('ball').style.top = `${ballY}px`;

    requestAnimationFrame(updatePong);
}