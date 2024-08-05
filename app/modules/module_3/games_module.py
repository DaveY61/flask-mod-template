from flask import Blueprint, render_template
from flask_login import login_required
from app.app import module_access_required

blueprint = Blueprint('games', __name__,
                      static_folder='static',
                      static_url_path='/modules/module_3/static',
                      template_folder='templates')

@blueprint.route('/games', methods=['GET'])
@login_required
@module_access_required('app.modules.module_3.games_module')
def games():
    sidebar_menu = [
        {'icon': 'fas fa-table', 'text': 'Tic-Tac-Toe', 'action': 'showGame', 'params': ['tic-tac-toe']},
        {'icon': 'fas fa-chess-board', 'text': 'Checkers', 'action': 'showGame', 'params': ['checkers']},
        {'icon': 'fas fa-table-tennis', 'text': 'Pong', 'action': 'showGame', 'params': ['pong']}
    ]
    return render_template('pages/games.html', use_sidebar=True, sidebar_menu=sidebar_menu)