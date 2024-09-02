from flask import Blueprint, render_template, jsonify, request, current_app, redirect, url_for
from flask_login import login_required
from app.services.auth_service_db import admin_required
import os

blueprint = Blueprint('log', __name__, template_folder='log_templates')

@blueprint.route('/log_viewer')
@login_required
@admin_required
def log_viewer():
    log_dir = current_app.config['LOG_FILE_DIRECTORY']
    log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]

    # Sort log files based on modification time (most recent first)
    log_files.sort(key=lambda x: os.path.getmtime(os.path.join(log_dir, x)), reverse=True)
    
    return render_template('pages/log_viewer.html', log_files=log_files)

@blueprint.route('/log_content')
@login_required
@admin_required
def get_log_content():
    log_file = request.args.get('file')
    log_dir = current_app.config['LOG_FILE_DIRECTORY']
    try:
        file_path = os.path.join(log_dir, log_file)
    except:
        current_app.logger.warning(f"Missing/blank log file.")
        return redirect(url_for('log.log_viewer'))
    
    if not os.path.exists(file_path):
        current_app.logger.warning(f"Missing log file: {file_path}")
        return redirect(url_for('log.log_viewer'))

    with open(file_path, 'r') as f:
        lines = f.readlines()[1:]  # Skip the header line
    
    log_entries = []
    for line in lines:
        parts = line.strip().split('\t')
        if len(parts) == 11:
            log_entries.append({
                'timestamp': parts[0],
                'level': parts[1],
                'message': parts[3],
                'user_email': parts[5],
                'remote_addr': parts[6],
                'url': parts[7],
                'function': parts[8],
                'line': parts[9],
                'filename': parts[10]
            })
    
    return jsonify(log_entries)