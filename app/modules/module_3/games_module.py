from flask import render_template

MODULE_INFO = {
    'blueprint_name': 'games',
    'view_name': 'games',
    'menu_name': 'Games'
}

def games():
    sidebar_menu = [
        {'icon': 'fas fa-table', 'text': 'Tic-Tac-Toe', 'action': 'showGame', 'params': ['tic-tac-toe']},
        {'icon': 'fas fa-chess-board', 'text': 'Checkers', 'action': 'showGame', 'params': ['checkers']},
        {'icon': 'fas fa-table-tennis', 'text': 'Pong', 'action': 'showGame', 'params': ['pong']}
    ]
    return render_template('pages/games.html', use_sidebar=True, sidebar_menu=sidebar_menu)