(function() {
    let board = [];
    let selectedPiece = null;
    let currentPlayer = 'red';

    function initCheckers() {
        const boardElement = document.getElementById('checkers');
        boardElement.innerHTML = '';
        board = [];

        for (let i = 0; i < 8; i++) {
            board[i] = [];
            for (let j = 0; j < 8; j++) {
                const cell = document.createElement('div');
                cell.classList.add('cell');
                cell.classList.add((i + j) % 2 === 0 ? 'white' : 'black');
                cell.dataset.row = i;
                cell.dataset.col = j;
                
                if ((i + j) % 2 !== 0) {
                    if (i < 3) {
                        board[i][j] = 'red';
                        const piece = document.createElement('div');
                        piece.classList.add('piece', 'red');
                        cell.appendChild(piece);
                    } else if (i > 4) {
                        board[i][j] = 'black';
                        const piece = document.createElement('div');
                        piece.classList.add('piece', 'black');
                        cell.appendChild(piece);
                    } else {
                        board[i][j] = null;
                    }
                } else {
                    board[i][j] = null;
                }

                cell.addEventListener('click', cellClickHandler);
                boardElement.appendChild(cell);
            }
        }

        // Show instructions
        const instructionsElement = document.getElementById('game-instructions');
        instructionsElement.style.display = 'block';
        updateInstructions();
    }

    function updateInstructions() {
        const instructionsElement = document.getElementById('game-instructions');
        instructionsElement.innerHTML = `
            <h4>Checkers Instructions:</h4>
            <ol>
                <li>Click on a piece to select it.</li>
                <li>Click on an empty black square to move the selected piece.</li>
                <li>Jump over an opponent's piece to capture it.</li>
                <li>Red moves first, then players alternate turns.</li>
            </ol>
        `;
        instructionsElement.style.display = 'block';
    }

    function cellClickHandler(event) {
        const cell = event.currentTarget;
        const row = parseInt(cell.dataset.row);
        const col = parseInt(cell.dataset.col);

        if (board[row][col] === currentPlayer) {
            selectPiece(row, col, cell.firstChild);
        } else {
            moveSelectedPiece(row, col);
        }
    }

    function clearHighlights() {
        document.querySelectorAll('#checkers .cell').forEach(cell => cell.classList.remove('highlight-move'));
    }

    function selectPiece(row, col, pieceElement) {
        // Clear previous highlights
        clearHighlights();

        if (board[row][col] === currentPlayer) {
            if (selectedPiece) {
                selectedPiece.classList.remove('selected');
            }
            const availableMoves = getAvailableMoves(row, col);
            
            // Always select the piece, even if there are no available moves
            selectedPiece = pieceElement;
            selectedPiece.classList.add('selected');

            // Highlight available moves
            availableMoves.forEach(([r, c]) => {
                const cell = document.querySelector(`#checkers .cell[data-row="${r}"][data-col="${c}"]`);
                cell.classList.add('highlight-move');
            });
        } else {
            selectedPiece = null;
        }
    }

    function moveSelectedPiece(row, col) {
        if (selectedPiece && board[row][col] === null && (row + col) % 2 !== 0) {
            const oldRow = parseInt(selectedPiece.parentNode.dataset.row);
            const oldCol = parseInt(selectedPiece.parentNode.dataset.col);

            const availableMoves = getAvailableMoves(oldRow, oldCol);
            
            if (availableMoves.some(move => move[0] === row && move[1] === col)) {
                // Move the piece
                board[row][col] = currentPlayer;
                board[oldRow][oldCol] = null;

                const newCell = document.querySelector(`#checkers .cell[data-row="${row}"][data-col="${col}"]`);
                newCell.appendChild(selectedPiece);
                selectedPiece.classList.remove('selected');
                selectedPiece = null;

                // Check for capture
                if (Math.abs(row - oldRow) === 2) {
                    const capturedRow = (row + oldRow) / 2;
                    const capturedCol = (col + oldCol) / 2;
                    board[capturedRow][capturedCol] = null;
                    const capturedCell = document.querySelector(`#checkers .cell[data-row="${capturedRow}"][data-col="${capturedCol}"]`);
                    capturedCell.innerHTML = '';
                }

                // Clear highlights
                clearHighlights();

                // Switch players
                currentPlayer = currentPlayer === 'red' ? 'black' : 'red';
            }
        }
    }

    function getAvailableMoves(row, col) {
        const moves = [];
        const direction = (currentPlayer === 'red') ? 1 : -1;

        // Check normal moves
        [-1, 1].forEach(colDir => {
            let newRow = row + direction;
            let newCol = col + colDir;

            if (isInBounds(newRow, newCol)) {
                if (board[newRow][newCol] === null) {
                    moves.push([newRow, newCol]);
                }
            }
        });

        // Check capture moves
        [-1, 1].forEach(colDir => {
            let newRow = row + 2 * direction;
            let newCol = col + 2 * colDir;

            if (isInBounds(newRow, newCol)) {
                if (board[newRow][newCol] === null) {
                    const jumpedRow = row + direction;
                    const jumpedCol = col + colDir;
                    if (board[jumpedRow][jumpedCol] === (currentPlayer === 'red' ? 'black' : 'red')) {
                        moves.push([newRow, newCol]);
                    }
                }
            }
        });

        return moves;
    }

    function isInBounds(row, col) {
        return row >= 0 && row < 8 && col >= 0 && col < 8;
    }

    // Explicitly attach initCheckers to the global window object
    window.initCheckers = initCheckers;
})();