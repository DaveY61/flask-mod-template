from flask import Blueprint, render_template
from flask_login import login_required
from app.app import module_access_required
import os

# Automatically determine the module name and path
module_path = os.path.relpath(__file__, start=os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
module_name = f'app.{module_path[:-3].replace(os.path.sep, ".")}'
static_url_path = f'/modules/{os.path.dirname(module_path)}/static'

blueprint = Blueprint('games', __name__,
                      static_folder='static',
                      static_url_path=static_url_path,
                      template_folder='templates')

@blueprint.route('/games', methods=['GET'])
@login_required
@module_access_required(module_name)
def games():
    sidebar_menu = [
        {'icon': 'fas fa-table', 'text': 'Tic-Tac-Toe', 'action': 'showGame', 'params': ['tic-tac-toe']},
        {'icon': 'fas fa-chess-board', 'text': 'Checkers', 'action': 'showGame', 'params': ['checkers']},
        {'icon': 'fas fa-table-tennis', 'text': 'Pong', 'action': 'showGame', 'params': ['pong']}
    ]
    return render_template('pages/games.html', use_sidebar=True, sidebar_menu=sidebar_menu)