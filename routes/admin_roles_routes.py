"""Admin Roles & Permissions Routes"""
import logging
import sqlite3
from datetime import datetime, timedelta
from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from utils.rbac import role_required

logger = logging.getLogger(__name__)

admin_roles_bp = Blueprint('admin_roles', __name__, url_prefix='/admin/roles')


@admin_roles_bp.route('/')
@role_required("Administrator")
def roles():
    """Display roles and permissions management page"""
    # Import new functions and logging
    from admin_data_functions import get_role_permissions, get_all_permissions, add_log
    
    # Log access to roles page
    add_log(session.get('user_id'), 'Accessed roles management')
    
    # Get roles with their permissions and all available permissions
    roles_data = get_role_permissions()  # Returns all roles with permissions
    permissions = get_all_permissions()  # Returns all available permissions
    
    return render_template('admin/roles.html', role=session.get('role'), roles=roles_data, permissions=permissions)


@admin_roles_bp.route('/add-role', methods=['POST'])
@role_required("Administrator")
def add_role_route():
    """Add a new role"""
    # Import new function
    from admin_data_functions import add_role
    
    role_name = request.form.get('role_name', '').strip()
    
    if role_name and add_role(role_name):
        flash(f'Role "{role_name}" added successfully!', 'success')
    else:
        flash('Failed to add role. Role may already exist.', 'error')
    
    return redirect(url_for('admin_roles.roles'))


@admin_roles_bp.route('/assign-permissions', methods=['POST'])
@role_required("Administrator")
def assign_permissions():
    """Assign permissions to a role"""
    # Import new function
    from admin_data_functions import assign_permission
    
    role_id = request.form.get('role_id')
    permission_ids = request.form.getlist('permission_ids')
    
    if role_id and assign_permission(role_id, permission_ids):
        flash('Permissions assigned successfully!', 'success')
    else:
        flash('Failed to assign permissions.', 'error')
    
    return redirect(url_for('admin_roles.roles'))


@admin_roles_bp.route('/<role_name>/update', methods=['POST'])
@role_required("Administrator")
def update_permissions(role_name):
    """Update permissions for a specific role"""
    # Get kwargs from app context
    from flask import current_app
    role_permission_scope = current_app.config.get('role_permission_scope')
    main_db_getter = current_app.config.get('main_db_getter')
    log_activity = current_app.config.get('log_activity')
    log_audit_event = current_app.config.get('log_audit_event')
    
    role_scope = role_permission_scope(role_name)
    selected_permission_ids = {
        int(permission_id)
        for permission_id in request.form.getlist('permission_ids')
        if str(permission_id).isdigit()
    }
    
    conn = sqlite3.connect(main_db_getter())
    conn.row_factory = sqlite3.Row
    try:
        role_row = conn.execute('SELECT id, name FROM Roles WHERE name = ?', (role_scope,)).fetchone()
        if not role_row:
            flash('Role not found.', 'error')
            return redirect(url_for('admin_roles.roles'))
        
        conn.execute('DELETE FROM RolePermissions WHERE role_id = ?', (role_row['id'],))
        for permission_id in selected_permission_ids:
            conn.execute('INSERT INTO RolePermissions (role_id, permission_id) VALUES (?, ?)', 
                        (role_row['id'], permission_id))
        conn.commit()
        
        log_activity(session.get('user_id'), f'Permissions updated for {role_scope}')
        log_audit_event(session.get('user_id'), session.get('role', 'Administrator'), 
                      'PERMISSIONS_UPDATE', 'ROLE', 
                      f'Updated permissions for role {role_scope}', success=True)
        flash(f'Permissions updated for {role_scope}.', 'success')
    except Exception as exc:
        conn.rollback()
        logger.error(f"Error updating permissions for {role_name}: {exc}")
        flash(f'Error updating permissions: {exc}', 'error')
    finally:
        conn.close()
    return redirect(url_for('admin_roles.roles'))


@admin_roles_bp.route('/<role_name>/reset', methods=['POST'])
@role_required("Administrator")
def reset_permissions(role_name):
    """Reset role permissions to defaults"""
    # Get kwargs from app context
    from flask import current_app
    role_permission_scope = current_app.config.get('role_permission_scope')
    main_db_getter = current_app.config.get('main_db_getter')
    log_activity = current_app.config.get('log_activity')
    log_audit_event = current_app.config.get('log_audit_event')
    
    role_scope = role_permission_scope(role_name)
    
    conn = sqlite3.connect(main_db_getter())
    conn.row_factory = sqlite3.Row
    try:
        role_row = conn.execute('SELECT id, name FROM Roles WHERE name = ?', (role_scope,)).fetchone()
        if not role_row:
            return jsonify({'success': False, 'error': 'Role not found'})
        
        # Get default permissions for this role
        default_permissions = get_default_permissions(role_name)
        
        # Clear existing permissions
        conn.execute('DELETE FROM RolePermissions WHERE role_id = ?', (role_row['id'],))
        
        # Add default permissions
        for perm_name in default_permissions:
            perm_row = conn.execute('SELECT id FROM Permissions WHERE name = ?', (perm_name,)).fetchone()
            if perm_row:
                conn.execute('INSERT INTO RolePermissions (role_id, permission_id) VALUES (?, ?)', 
                            (role_row['id'], perm_row['id']))
        
        conn.commit()
        
        log_activity(session.get('user_id'), f'Permissions reset to defaults for {role_scope}')
        log_audit_event(session.get('user_id'), session.get('role', 'Administrator'), 
                      'PERMISSIONS_RESET', 'ROLE', 
                      f'Reset permissions for role {role_scope} to defaults', success=True)
        
        return jsonify({'success': True})
    except Exception as exc:
        conn.rollback()
        logger.error(f"Error resetting permissions for {role_name}: {exc}")
        return jsonify({'success': False, 'error': str(exc)})
    finally:
        conn.close()


@admin_roles_bp.route('/summary', methods=['GET'])
@role_required("Administrator")
def permission_summary():
    """Get permission summary for all roles"""
    # Get kwargs from app context
    from flask import current_app
    main_db_getter = current_app.config.get('main_db_getter')
    
    conn = sqlite3.connect(main_db_getter())
    conn.row_factory = sqlite3.Row
    try:
        summary = {}
        
        # Get all roles
        roles = conn.execute('SELECT name FROM Roles').fetchall()
        
        for role in roles:
            role_name = role['name']
            summary[role_name] = {}
            
            # Get permissions for this role
            permissions = conn.execute('''
                SELECT p.name, p.category 
                FROM Permissions p 
                JOIN RolePermissions rp ON p.id = rp.permission_id 
                JOIN Roles r ON rp.role_id = r.id 
                WHERE r.name = ?
                ORDER BY p.category, p.name
            ''', (role_name,)).fetchall()
            
            for perm in permissions:
                category = perm['category']
                if category not in summary[role_name]:
                    summary[role_name][category] = []
                summary[role_name][category].append(perm['name'])
        
        return jsonify({'success': True, 'summary': summary})
    except Exception as exc:
        logger.error(f"Error getting permission summary: {exc}")
        return jsonify({'success': False, 'error': str(exc)})
    finally:
        conn.close()


@admin_roles_bp.route('/export', methods=['POST'])
@role_required("Administrator")
def export_permissions():
    """Export permissions configuration"""
    # Get kwargs from app context
    from flask import current_app
    main_db_getter = current_app.config.get('main_db_getter')
    
    conn = sqlite3.connect(main_db_getter())
    conn.row_factory = sqlite3.Row
    try:
        # Get complete permissions configuration
        config = conn.execute('''
            SELECT r.name as role, p.name as permission, p.category, p.description
            FROM Roles r
            LEFT JOIN RolePermissions rp ON r.id = rp.role_id
            LEFT JOIN Permissions p ON rp.permission_id = p.id
            ORDER BY r.name, p.category, p.name
        ''').fetchall()
        
        # Format as JSON
        export_data = {}
        for row in config:
            role = row['role']
            if role not in export_data:
                export_data[role] = {
                    'permissions': [],
                    'categories': {}
                }
            
            if row['permission']:
                export_data[role]['permissions'].append(row['permission'])
                
                category = row['category'] or 'General'
                if category not in export_data[role]['categories']:
                    export_data[role]['categories'][category] = []
                export_data[role]['categories'][category].append({
                    'name': row['permission'],
                    'description': row['description']
                })
        
        return jsonify({'success': True, 'data': export_data})
    except Exception as exc:
        logger.error(f"Error exporting permissions: {exc}")
        return jsonify({'success': False, 'error': str(exc)})
    finally:
        conn.close()


@admin_roles_bp.route('/import', methods=['POST'])
@role_required("Administrator")
def import_permissions():
    """Import permissions configuration"""
    # Get kwargs from app context
    from flask import current_app
    main_db_getter = current_app.config.get('main_db_getter')
    log_activity = current_app.config.get('log_activity')
    log_audit_event = current_app.config.get('log_audit_event')
    
    try:
        import_data = request.get_json()
        if not import_data:
            return jsonify({'success': False, 'error': 'No data provided'})
        
        conn = sqlite3.connect(main_db_getter())
        conn.row_factory = sqlite3.Row
        try:
            # Clear existing permissions
            conn.execute('DELETE FROM RolePermissions')
            
            # Import new permissions
            for role_name, role_data in import_data.items():
                role_row = conn.execute('SELECT id FROM Roles WHERE name = ?', (role_name,)).fetchone()
                if not role_row:
                    continue
                
                role_id = role_row['id']
                
                for permission_name in role_data.get('permissions', []):
                    perm_row = conn.execute('SELECT id FROM Permissions WHERE name = ?', (permission_name,)).fetchone()
                    if perm_row:
                        conn.execute('INSERT INTO RolePermissions (role_id, permission_id) VALUES (?, ?)', 
                                    (role_id, perm_row['id']))
            
            conn.commit()
            
            log_activity(session.get('user_id'), 'Permissions configuration imported')
            log_audit_event(session.get('user_id'), session.get('role', 'Administrator'), 
                          'PERMISSIONS_IMPORT', 'ROLE', 
                          'Imported permissions configuration', success=True)
            
            return jsonify({'success': True})
        except Exception as exc:
            conn.rollback()
            logger.error(f"Error importing permissions: {exc}")
            return jsonify({'success': False, 'error': str(exc)})
        finally:
            conn.close()
            
    except Exception as exc:
        logger.error(f"Error processing import data: {exc}")
        return jsonify({'success': False, 'error': 'Invalid data format'})


def get_default_permissions(role_name):
    """Get default permissions for a role"""
    defaults = {
        'Student': [
            'view_books',
            'search_books',
            'view_own_profile',
            'update_own_profile'
        ],
        'Faculty': [
            'view_books',
            'search_books',
            'add_books',
            'update_books',
            'view_own_profile',
            'update_own_profile',
            'view_student_records'
        ],
        'Librarian': [
            'view_books',
            'search_books',
            'add_books',
            'update_books',
            'delete_books',
            'manage_circulation',
            'view_reports',
            'manage_users_basic'
        ],
        'Administrator': [
            'view_books',
            'search_books',
            'add_books',
            'update_books',
            'delete_books',
            'manage_circulation',
            'view_reports',
            'manage_users',
            'manage_roles',
            'view_logs',
            'manage_settings',
            'manage_security'
        ]
    }
    return defaults.get(role_name, [])


def register_admin_roles_routes(app, **kwargs):
    """Register roles and permissions routes"""
    # Store kwargs in app config for route access
    app.config.update({
        'role_permission_scope': kwargs.get('role_permission_scope'),
        'main_db_getter': kwargs.get('main_db_getter'),
        'log_activity': kwargs.get('log_activity'),
        'log_audit_event': kwargs.get('log_audit_event'),
    })
    
    # Register the blueprint with the app
    app.register_blueprint(admin_roles_bp)
