from flask import Blueprint, render_template
from flask_login import login_required
from app.app import module_access_required
import os

# Automatically determine the module name
module_name = os.path.join('app', os.path.relpath(__file__, start=os.path.dirname(os.path.dirname(os.path.dirname(__file__))))).replace(os.path.sep, '.')[:-3]
blueprint = Blueprint('games', __name__,
                      static_folder='static',
                      static_url_path='/modules/module_3/static',
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