"""Admin User Management Routes"""
import logging
import sqlite3
from datetime import datetime, timedelta
from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from utils.rbac import role_required
from werkzeug.security import generate_password_hash

logger = logging.getLogger(__name__)

admin_user_bp = Blueprint('admin_users', __name__, url_prefix='/admin/users')


@admin_user_bp.route('/')
@role_required("Administrator")
def users():
    """Display users management page"""
    # Import simplified function and logging
    from admin_data_functions import get_all_users, add_log
    
    # Log access to users page
    add_log(session.get('user_id'), 'Accessed user management')
    
    # Get only users data
    users = get_all_users()
    
    return render_template('admin/users.html', role=session.get('role'), users=users)


@admin_user_bp.route('/add', methods=['POST'])
@role_required("Administrator")
def add_user():
    """Add a new user"""
    # Get kwargs from app context
    from flask import current_app
    default_query_limit = current_app.config.get('default_query_limit')
    role_choices = current_app.config.get('role_choices')
    require_admin = current_app.config.get('require_admin')
    fetch_activity_logs = current_app.config.get('fetch_activity_logs')
    get_db_connection = current_app.config.get('get_db_connection')
    get_user_with_details = current_app.config.get('get_user_with_details')
    normalize_role = current_app.config.get('normalize_role')
    role_permission_scope = current_app.config.get('role_permission_scope')
    set_setting = current_app.config.get('set_setting')
    sync_role_profile_tables = current_app.config.get('sync_role_profile_tables')
    validate_managed_user_form = current_app.config.get('validate_managed_user_form')
    log_activity = current_app.config.get('log_activity')
    log_audit_event = current_app.config.get('log_audit_event')
    
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    email = request.form.get('email', '').strip()
    role = request.form.get('role', '')
    
    # Validate input
    error = validate_managed_user_form(username, email, role, password, role_choices)
    if error:
        flash(error, 'error')
        return redirect(url_for('admin_users.users'))
    
    # Check if user already exists
    conn = get_db_connection()
    try:
        existing = conn.execute('SELECT id FROM Users WHERE username = ? OR email = ?', (username, email)).fetchone()
        if existing:
            flash('Username or email already exists.', 'error')
            return redirect(url_for('admin_users.users'))
        
        # Create new user
        hashed_password = generate_password_hash(password)
        conn.execute(
            'INSERT INTO Users (username, password, email, role, created_date) VALUES (?, ?, ?, ?, ?)',
            (username, hashed_password, email, role, datetime.now().isoformat())
        )
        conn.commit()
        
        log_activity(session.get('user_id'), f'Added new user: {username}')
        log_audit_event(session.get('user_id'), session.get('role', 'Administrator'), 
                      'USER_CREATE', 'USER', f'Created user {username}', success=True)
        flash(f'User {username} added successfully.', 'success')
        
    except Exception as exc:
        conn.rollback()
        logger.error(f"Error adding user: {exc}")
        flash(f'Error adding user: {exc}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_users.users'))


@admin_user_bp.route('/<int:user_id>/update', methods=['POST'])
@role_required("Administrator")
def update_user(user_id):
    """Update an existing user"""
    # Get kwargs from app context
    from flask import current_app
    default_query_limit = current_app.config.get('default_query_limit')
    role_choices = current_app.config.get('role_choices')
    require_admin = current_app.config.get('require_admin')
    fetch_activity_logs = current_app.config.get('fetch_activity_logs')
    get_db_connection = current_app.config.get('get_db_connection')
    get_user_with_details = current_app.config.get('get_user_with_details')
    normalize_role = current_app.config.get('normalize_role')
    role_permission_scope = current_app.config.get('role_permission_scope')
    set_setting = current_app.config.get('set_setting')
    sync_role_profile_tables = current_app.config.get('sync_role_profile_tables')
    validate_managed_user_form = current_app.config.get('validate_managed_user_form')
    log_activity = current_app.config.get('log_activity')
    log_audit_event = current_app.config.get('log_audit_event')
    
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    role = request.form.get('role', '')
    password = request.form.get('password', '')
    
    # Validate input
    error = validate_managed_user_form(username, email, role, password, role_choices, allow_empty_password=True)
    if error:
        flash(error, 'error')
        return redirect(url_for('admin_users.users'))
    
    conn = get_db_connection()
    try:
        # Check if user exists
        user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('admin_users.users'))
        
        # Check for conflicts
        existing = conn.execute(
            'SELECT id FROM Users WHERE (username = ? OR email = ?) AND id != ?', 
            (username, email, user_id)
        ).fetchone()
        if existing:
            flash('Username or email already exists.', 'error')
            return redirect(url_for('admin_users.users'))
        
        # Update user
        updates = ['username = ?', 'email = ?', 'role = ?']
        params = [username, email, role]
        
        if password:
            updates.append('password = ?')
            params.append(generate_password_hash(password))
        
        params.append(user_id)
        conn.execute(f'UPDATE Users SET {", ".join(updates)} WHERE id = ?', params)
        conn.commit()
        
        log_activity(session.get('user_id'), f'Updated user: {username}')
        log_audit_event(session.get('user_id'), session.get('role', 'Administrator'), 
                      'USER_UPDATE', 'USER', f'Updated user {username}', success=True)
        flash(f'User {username} updated successfully.', 'success')
        
    except Exception as exc:
        conn.rollback()
        logger.error(f"Error updating user: {exc}")
        flash(f'Error updating user: {exc}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_users.users'))


@admin_user_bp.route('/<int:user_id>/delete', methods=['POST'])
@role_required("Administrator")
def delete_user(user_id):
    """Delete a user"""
    # Get kwargs from app context
    from flask import current_app
    log_activity = current_app.config.get('log_activity')
    log_audit_event = current_app.config.get('log_audit_event')
    
    conn = get_db_connection()
    try:
        user = conn.execute('SELECT username FROM Users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'})
        
        username = user['username']
        
        # Don't allow deleting the current admin user
        if username == session.get('user_id'):
            return jsonify({'success': False, 'error': 'Cannot delete your own account'})
        
        conn.execute('DELETE FROM Users WHERE id = ?', (user_id,))
        conn.commit()
        
        log_activity(session.get('user_id'), f'Deleted user: {username}')
        log_audit_event(session.get('user_id'), session.get('role', 'Administrator'), 
                      'USER_DELETE', 'USER', f'Deleted user {username}', success=True)
        
        return jsonify({'success': True})
        
    except Exception as exc:
        conn.rollback()
        logger.error(f"Error deleting user: {exc}")
        return jsonify({'success': False, 'error': str(exc)})
    finally:
        conn.close()


@admin_user_bp.route('/<int:user_id>/change_role', methods=['POST'])
@role_required("Administrator")
def change_role(user_id):
    """Change user role"""
    # Get kwargs from app context
    from flask import current_app
    role_permission_scope = current_app.config.get('role_permission_scope')
    log_activity = current_app.config.get('log_activity')
    log_audit_event = current_app.config.get('log_audit_event')
    
    new_role = request.form.get('role')
    if not new_role:
        return jsonify({'success': False, 'error': 'No role specified'})
    
    conn = get_db_connection()
    try:
        user = conn.execute('SELECT username FROM Users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'})
        
        username = user['username']
        
        # Don't allow changing the current admin's role to non-admin
        if username == session.get('user_id') and new_role != 'Administrator':
            return jsonify({'success': False, 'error': 'Cannot change your own role to non-administrator'})
        
        conn.execute('UPDATE Users SET role = ? WHERE id = ?', (new_role, user_id))
        conn.commit()
        
        log_activity(session.get('user_id'), f'Changed role for {username} to {new_role}')
        log_audit_event(session.get('user_id'), session.get('role', 'Administrator'), 
                      'ROLE_CHANGE', 'USER', f'Changed role for {username} to {new_role}', success=True)
        
        return jsonify({'success': True})
        
    except Exception as exc:
        conn.rollback()
        logger.error(f"Error changing user role: {exc}")
        return jsonify({'success': False, 'error': str(exc)})
    finally:
        conn.close()


@admin_user_bp.route('/<int:user_id>/edit', methods=['GET'])
@role_required("Administrator")
def edit_user(user_id):
    """Get user data for editing (AJAX endpoint)"""
    # Get kwargs from app context
    from flask import current_app
    get_db_connection = current_app.config.get('get_db_connection')
    
    conn = get_db_connection()
    try:
        user = conn.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'})
        
        return jsonify({'success': True, 'user': dict(user)})
        
    except Exception as exc:
        logger.error(f"Error getting user data: {exc}")
        return jsonify({'success': False, 'error': str(exc)})
    finally:
        conn.close()


def register_admin_user_routes(app, **kwargs):
    """Register user management routes"""
    # Store kwargs in app config for route access
    app.config.update({
        'default_query_limit': kwargs.get('default_query_limit'),
        'role_choices': kwargs.get('role_choices'),
        'require_admin': kwargs.get('require_admin'),
        'fetch_activity_logs': kwargs.get('fetch_activity_logs'),
        'get_db_connection': kwargs.get('get_db_connection'),
        'get_user_with_details': kwargs.get('get_user_with_details'),
        'normalize_role': kwargs.get('normalize_role'),
        'role_permission_scope': kwargs.get('role_permission_scope'),
        'set_setting': kwargs.get('set_setting'),
        'sync_role_profile_tables': kwargs.get('sync_role_profile_tables'),
        'validate_managed_user_form': kwargs.get('validate_managed_user_form'),
        'log_activity': kwargs.get('log_activity'),
        'log_audit_event': kwargs.get('log_audit_event'),
    })
    
    # Register the blueprint with the app
    app.register_blueprint(admin_user_bp)


# Register blueprint with app (alternative method)
def register_blueprint(app):
    app.register_blueprint(admin_user_bp)
