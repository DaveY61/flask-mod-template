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

        console.log("Initial board state:", JSON.parse(JSON.stringify(board)));

        // Add instructions
        const instructions = document.createElement('div');
        instructions.id = 'checkers-instructions';
        instructions.innerHTML = `
            <p>Instructions:</p>
            <p>1. Click on a piece to select it.</p>
            <p>2. Click on an empty black square to move the selected piece.</p>
            <p>3. Jump over an opponent's piece to capture it.</p>
            <p>4. Red moves first, then players alternate turns.</p>
        `;
        boardElement.after(instructions);
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
        console.log(`Attempting to select piece at (${row}, ${col})`);
        console.log(`Current player: ${currentPlayer}`);
        console.log(`Piece at (${row}, ${col}):`, board[row][col]);
        console.log("Current board state:", JSON.parse(JSON.stringify(board)));

        // Clear previous highlights
        clearHighlights();

        if (board[row][col] === currentPlayer) {
            if (selectedPiece) {
                selectedPiece.classList.remove('selected');
            }
            const availableMoves = getAvailableMoves(row, col);
            console.log(`Available moves for piece at (${row}, ${col}):`, availableMoves);
            
            // Always select the piece, even if there are no available moves
            selectedPiece = pieceElement;
            selectedPiece.classList.add('selected');

            // Highlight available moves
            availableMoves.forEach(([r, c]) => {
                const cell = document.querySelector(`#checkers .cell[data-row="${r}"][data-col="${c}"]`);
                cell.classList.add('highlight-move');
            });
        } else {
            console.log('This piece does not belong to the current player');
            console.log(`Board value at (${row}, ${col}):`, board[row][col]);
            console.log(`Current player:`, currentPlayer);
            selectedPiece = null;
        }
    }

    function moveSelectedPiece(row, col) {
        console.log(`Attempting to move to (${row}, ${col})`);
        if (selectedPiece && board[row][col] === null && (row + col) % 2 !== 0) {
            const oldRow = parseInt(selectedPiece.parentNode.dataset.row);
            const oldCol = parseInt(selectedPiece.parentNode.dataset.col);

            const availableMoves = getAvailableMoves(oldRow, oldCol);
            console.log(`Available moves from (${oldRow}, ${oldCol}):`, availableMoves);
            
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
                console.log('Move successful. Current player:', currentPlayer);
                console.log("Updated board state:", JSON.parse(JSON.stringify(board)));
            } else {
                console.log('Move not allowed');
            }
        } else {
            console.log('Invalid move attempt');
        }
    }

    function getAvailableMoves(row, col) {
        const moves = [];
        const direction = (currentPlayer === 'red') ? 1 : -1;

        console.log(`Checking moves for piece at (${row}, ${col})`);

        // Check normal moves
        [-1, 1].forEach(colDir => {
            let newRow = row + direction;
            let newCol = col + colDir;
            console.log(`Checking normal move to (${newRow}, ${newCol})`);
            if (isInBounds(newRow, newCol)) {
                if (board[newRow][newCol] === null) {
                    moves.push([newRow, newCol]);
                    console.log(`Normal move available: (${newRow}, ${newCol})`);
                } else {
                    console.log(`Cell (${newRow}, ${newCol}) is occupied by:`, board[newRow][newCol]);
                }
            } else {
                console.log(`Normal move (${newRow}, ${newCol}) is out of bounds`);
            }
        });

        // Check capture moves
        [-1, 1].forEach(colDir => {
            let newRow = row + 2 * direction;
            let newCol = col + 2 * colDir;
            console.log(`Checking capture move to (${newRow}, ${newCol})`);
            if (isInBounds(newRow, newCol)) {
                if (board[newRow][newCol] === null) {
                    const jumpedRow = row + direction;
                    const jumpedCol = col + colDir;
                    if (board[jumpedRow][jumpedCol] === (currentPlayer === 'red' ? 'black' : 'red')) {
                        moves.push([newRow, newCol]);
                        console.log(`Capture move available: (${newRow}, ${newCol})`);
                    } else {
                        console.log(`No opponent piece to capture at (${jumpedRow}, ${jumpedCol})`);
                    }
                } else {
                    console.log(`Capture destination (${newRow}, ${newCol}) is occupied`);
                }
            } else {
                console.log(`Capture move (${newRow}, ${newCol}) is out of bounds`);
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

console.log("Checkers script loaded, initCheckers is:", typeof window.initCheckers);