from flask import Blueprint, render_template
from flask_login import login_required

blueprint = Blueprint('games', __name__,
                      static_folder='static',
                      static_url_path='/modules/module_4/static',
                      template_folder='templates')

@blueprint.route('/games', methods=['GET'])
@login_required
def games():
    return render_template('pages/games.html')
