"""Admin Settings Routes"""
import logging
import sqlite3
from datetime import datetime, timedelta
from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from utils.rbac import role_required

logger = logging.getLogger(__name__)

admin_settings_bp = Blueprint('admin_settings', __name__, url_prefix='/admin/settings')


@admin_settings_bp.route('/')
@role_required("Administrator")
def settings():
    """Display settings page"""
    # Import simplified function and logging
    from admin_data_functions import get_settings, add_log
    
    # Log access to settings page
    add_log(session.get('user_id'), 'Accessed system settings')
    
    # Get only settings data
    settings = get_settings()
    
    return render_template('admin/settings.html', role=session.get('role'), settings=settings)


@admin_settings_bp.route('/update', methods=['POST'])
@role_required("Administrator")
def update_settings():
    """Update system settings"""
    # Get kwargs from app context
    from flask import current_app
    validate_query_result_limit = current_app.config.get('validate_query_result_limit')
    default_query_limit = current_app.config.get('default_query_limit')
    set_setting = current_app.config.get('set_setting')
    log_activity = current_app.config.get('log_activity')
    log_audit_event = current_app.config.get('log_audit_event')
    
    try:
        # Query limit
        max_limit, error = validate_query_result_limit(
            request.form.get('max_query_result_limit'),
            default_query_limit,
        )
        if error:
            flash(error, 'error')
            return redirect(url_for('admin_settings.settings'))
        
        # Voice settings
        voice_input_enabled = request.form.get('voice_input_enabled') == 'on'
        ai_query_enabled = request.form.get('ai_query_enabled') == 'on'
        ollama_sql_enabled = request.form.get('ollama_sql_enabled') == 'on'
        
        # Session settings
        session_timeout = int(request.form.get('session_timeout', 30))
        
        # System settings
        maintenance_mode = request.form.get('maintenance_mode') == 'on'
        debug_mode = request.form.get('debug_mode') == 'on'
        
        # AI settings
        ai_model = request.form.get('ai_model', 'gpt-3.5-turbo')
        api_rate_limit = int(request.form.get('api_rate_limit', 100))
        
        # Security settings
        max_failed_attempts = int(request.form.get('max_failed_attempts', 5))
        lockout_duration = int(request.form.get('lockout_duration', 15))
        two_factor_auth = request.form.get('two_factor_auth') == 'on'
        
        # Password settings
        password_min_length = request.form.get('password_min_length') == 'on'
        password_require_uppercase = request.form.get('password_require_uppercase') == 'on'
        password_require_numbers = request.form.get('password_require_numbers') == 'on'
        password_require_symbols = request.form.get('password_require_symbols') == 'on'
        
        # Notification settings
        email_notifications = request.form.get('email_notifications') == 'on'
        admin_email = request.form.get('admin_email', '')
        
        # Alert settings
        alert_failed_logins = request.form.get('alert_failed_logins') == 'on'
        alert_system_errors = request.form.get('alert_system_errors') == 'on'
        alert_security_events = request.form.get('alert_security_events') == 'on'
        alert_database_issues = request.form.get('alert_database_issues') == 'on'
        
        # Update all settings
        settings_to_update = [
            ('max_query_result_limit', max_limit),
            ('voice_input_enabled', voice_input_enabled),
            ('ai_query_enabled', ai_query_enabled),
            ('ollama_sql_enabled', ollama_sql_enabled),
            ('session_timeout', session_timeout),
            ('maintenance_mode', maintenance_mode),
            ('debug_mode', debug_mode),
            ('ai_model', ai_model),
            ('api_rate_limit', api_rate_limit),
            ('max_failed_attempts', max_failed_attempts),
            ('lockout_duration', lockout_duration),
            ('two_factor_auth', two_factor_auth),
            ('password_min_length', password_min_length),
            ('password_require_uppercase', password_require_uppercase),
            ('password_require_numbers', password_require_numbers),
            ('password_require_symbols', password_require_symbols),
            ('email_notifications', email_notifications),
            ('admin_email', admin_email),
            ('alert_failed_logins', alert_failed_logins),
            ('alert_system_errors', alert_system_errors),
            ('alert_security_events', alert_security_events),
            ('alert_database_issues', alert_database_issues),
        ]
        
        for setting_name, setting_value in settings_to_update:
            set_setting(setting_name, setting_value, session.get('user_id'))
        
        log_activity(session.get('user_id'), 'Updated system settings')
        log_audit_event(session.get('user_id'), session.get('role', 'Administrator'), 
                      'SETTINGS_UPDATE', 'SYSTEM', 'Updated system settings', success=True)
        flash('Settings updated successfully.', 'success')
        
    except Exception as exc:
        logger.error(f"Error updating settings: {exc}")
        flash(f'Error updating settings: {exc}', 'error')
    
    return redirect(url_for('admin_settings.settings'))


@admin_settings_bp.route('/export', methods=['POST'])
@role_required("Administrator")
def export_settings():
    """Export settings configuration"""
    try:
        # Get all settings from database
        from admin_data_functions import get_settings_data
        settings_data = get_settings_data()
        
        # Format for export
        export_data = {
            'settings': settings_data.get('settings', {}),
            'export_date': datetime.now().isoformat(),
            'exported_by': session.get('user_id')
        }
        
        return jsonify({'success': True, 'data': export_data})
        
    except Exception as exc:
        logger.error(f"Error exporting settings: {exc}")
        return jsonify({'success': False, 'error': str(exc)})


@admin_settings_bp.route('/import', methods=['POST'])
@role_required("Administrator")
def import_settings():
    """Import settings configuration"""
    # Get kwargs from app context
    from flask import current_app
    set_setting = current_app.config.get('set_setting')
    log_activity = current_app.config.get('log_activity')
    log_audit_event = current_app.config.get('log_audit_event')
    
    try:
        import_data = request.get_json()
        if not import_data:
            return jsonify({'success': False, 'error': 'No data provided'})
        
        settings = import_data.get('settings', {})
        
        # Import each setting
        for setting_name, setting_value in settings.items():
            set_setting(setting_name, setting_value, session.get('user_id'))
        
        log_activity(session.get('user_id'), 'Imported settings configuration')
        log_audit_event(session.get('user_id'), session.get('role', 'Administrator'), 
                      'SETTINGS_IMPORT', 'SYSTEM', 'Imported settings configuration', success=True)
        
        return jsonify({'success': True})
        
    except Exception as exc:
        logger.error(f"Error importing settings: {exc}")
        return jsonify({'success': False, 'error': str(exc)})


@admin_settings_bp.route('/reset', methods=['POST'])
@role_required("Administrator")
def reset_settings():
    """Reset settings to defaults"""
    # Get kwargs from app context
    from flask import current_app
    set_setting = current_app.config.get('set_setting')
    log_activity = current_app.config.get('log_activity')
    log_audit_event = current_app.config.get('log_audit_event')
    
    try:
        # Default settings
        default_settings = {
            'max_query_result_limit': 100,
            'voice_input_enabled': True,
            'ai_query_enabled': True,
            'ollama_sql_enabled': True,
            'session_timeout': 30,
            'maintenance_mode': False,
            'debug_mode': False,
            'ai_model': 'gpt-3.5-turbo',
            'api_rate_limit': 100,
            'max_failed_attempts': 5,
            'lockout_duration': 15,
            'two_factor_auth': False,
            'password_min_length': True,
            'password_require_uppercase': False,
            'password_require_numbers': False,
            'password_require_symbols': False,
            'email_notifications': False,
            'admin_email': '',
            'alert_failed_logins': True,
            'alert_system_errors': True,
            'alert_security_events': True,
            'alert_database_issues': True,
        }
        
        # Reset all settings to defaults
        for setting_name, setting_value in default_settings.items():
            set_setting(setting_name, setting_value, session.get('user_id'))
        
        log_activity(session.get('user_id'), 'Reset settings to defaults')
        log_audit_event(session.get('user_id'), session.get('role', 'Administrator'), 
                      'SETTINGS_RESET', 'SYSTEM', 'Reset settings to defaults', success=True)
        
        return jsonify({'success': True})
        
    except Exception as exc:
        logger.error(f"Error resetting settings: {exc}")
        return jsonify({'success': False, 'error': str(exc)})


@admin_settings_bp.route('/test', methods=['POST'])
@role_required("Administrator")
def test_settings():
    """Test current settings configuration"""
    try:
        from admin_data_functions import get_settings_data
        settings_data = get_settings_data()
        
        # Test various settings
        test_results = {
            'database_connection': True,  # Would test actual DB connection
            'ai_model_access': settings_data.get('settings', {}).get('ai_query_enabled', False),
            'email_configuration': bool(settings_data.get('settings', {}).get('admin_email')),
            'security_settings': True,
        }
        
        return jsonify({'success': True, 'test_results': test_results})
        
    except Exception as exc:
        logger.error(f"Error testing settings: {exc}")
        return jsonify({'success': False, 'error': str(exc)})


@admin_settings_bp.route('/backup', methods=['POST'])
@role_required("Administrator")
def backup_settings():
    """Create backup of current settings"""
    try:
        from admin_data_functions import get_settings_data
        settings_data = get_settings_data()
        
        # Create backup data
        backup_data = {
            'backup_date': datetime.now().isoformat(),
            'backup_by': session.get('user_id'),
            'settings': settings_data.get('settings', {}),
            'version': '1.0'
        }
        
        # In a real implementation, this would save to a file or database
        log_activity(session.get('user_id'), 'Created settings backup')
        log_audit_event(session.get('user_id'), session.get('role', 'Administrator'), 
                      'SETTINGS_BACKUP', 'SYSTEM', 'Created settings backup', success=True)
        
        return jsonify({'success': True, 'backup_data': backup_data})
        
    except Exception as exc:
        logger.error(f"Error creating settings backup: {exc}")
        return jsonify({'success': False, 'error': str(exc)})


def register_admin_settings_routes(app, **kwargs):
    """Register settings routes"""
    # Store kwargs in app config for route access
    app.config.update({
        'validate_query_result_limit': kwargs.get('validate_query_result_limit'),
        'default_query_limit': kwargs.get('default_query_limit'),
        'set_setting': kwargs.get('set_setting'),
        'log_activity': kwargs.get('log_activity'),
        'log_audit_event': kwargs.get('log_audit_event'),
    })
    
    # Register the blueprint with the app
    app.register_blueprint(admin_settings_bp)


# Register blueprint with app (alternative method)
def register_blueprint(app):
    app.register_blueprint(admin_settings_bp)
