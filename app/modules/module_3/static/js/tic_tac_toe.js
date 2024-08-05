(function() {
    let currentPlayer = 'X';
    let gameBoard = ['', '', '', '', '', '', '', '', ''];
    let gameActive = true;

    function initTicTacToe() {
        const board = document.getElementById('tic-tac-toe');
        board.innerHTML = '';
        for (let i = 0; i < 9; i++) {
            const cell = document.createElement('div');
            cell.classList.add('cell');
            cell.dataset.index = i;
            cell.addEventListener('click', () => makeMove(i));
            board.appendChild(cell);
        }
        gameBoard = ['', '', '', '', '', '', '', '', ''];
        gameActive = true;
        currentPlayer = 'X';
    }

    function makeMove(index) {
        if (gameBoard[index] === '' && gameActive) {
            gameBoard[index] = currentPlayer;
            const cell = document.querySelector(`#tic-tac-toe .cell[data-index="${index}"]`);
            cell.textContent = currentPlayer;
            if (checkWin()) {
                setTimeout(() => {
                    alert(`${currentPlayer} wins!`);
                    initTicTacToe();
                }, 100);
                gameActive = false;
            } else if (gameBoard.every(cell => cell !== '')) {
                setTimeout(() => {
                    alert("It's a draw!");
                    initTicTacToe();
                }, 100);
                gameActive = false;
            } else {
                currentPlayer = currentPlayer === 'X' ? 'O' : 'X';
                if (currentPlayer === 'O') {
                    setTimeout(aiMove, 500);
                }
            }
        }
    }

    function aiMove() {
        const emptyCells = gameBoard.reduce((acc, cell, index) => {
            if (cell === '') acc.push(index);
            return acc;
        }, []);
        const randomIndex = emptyCells[Math.floor(Math.random() * emptyCells.length)];
        makeMove(randomIndex);
    }

    function checkWin() {
        const winPatterns = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],
            [0, 3, 6], [1, 4, 7], [2, 5, 8],
            [0, 4, 8], [2, 4, 6]
        ];
        return winPatterns.some(pattern =>
            gameBoard[pattern[0]] !== '' &&
            gameBoard[pattern[0]] === gameBoard[pattern[1]] &&
            gameBoard[pattern[1]] === gameBoard[pattern[2]]
        );
    }

    // Explicitly attach initTicTacToe to the global window object
    window.initTicTacToe = initTicTacToe;
})();