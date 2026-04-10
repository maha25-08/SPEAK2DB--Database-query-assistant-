"""Admin Logs & Activity Routes"""
import logging
import sqlite3
from datetime import datetime, timedelta
from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from utils.rbac import role_required

logger = logging.getLogger(__name__)

admin_logs_bp = Blueprint('admin_logs', __name__, url_prefix='/admin/logs')


@admin_logs_bp.route('/')
@role_required("Administrator")
def logs():
    """Display activity logs page"""
    # Import new function
    from admin_data_functions import get_activity_logs, add_log
    
    # Log access to logs page
    add_log(session.get('user_id'), 'Accessed activity logs')
    
    # Get all logs
    logs = get_activity_logs()
    
    return render_template('admin/logs_simple.html', role=session.get('role'), logs=logs)


@admin_logs_bp.route('/api', methods=['GET'])
@role_required("Administrator")
def logs_api():
    """API endpoint for logs data"""
    # Get kwargs from app context
    from flask import current_app
    fetch_activity_logs = current_app.config.get('fetch_activity_logs')
    main_db_getter = current_app.config.get('main_db_getter')
    
    conn = get_db_connection(main_db_getter())
    try:
        limit = int(request.args.get('limit', 50))
        logs = fetch_activity_logs(conn, limit=limit)
        return jsonify({'success': True, 'logs': logs, 'total_events': len(logs)})
    except Exception as exc:
        logger.error(f"Error fetching logs API: {exc}")
        return jsonify({'success': False, 'error': str(exc)})
    finally:
        conn.close()


@admin_logs_bp.route('/<int:log_id>/delete', methods=['POST'])
@role_required("Administrator")
def delete_log(log_id):
    """Delete a specific log entry"""
    # Get kwargs from app context
    from flask import current_app
    main_db_getter = current_app.config.get('main_db_getter')
    log_activity = current_app.config.get('log_activity')
    log_audit_event = current_app.config.get('log_audit_event')
    
    conn = sqlite3.connect(main_db_getter())
    try:
        # Check if log exists and can be deleted
        log_row = conn.execute('SELECT * FROM ActivityLogs WHERE id = ?', (log_id,)).fetchone()
        if not log_row:
            return jsonify({'success': False, 'error': 'Log entry not found'})
        
        # Delete the log
        conn.execute('DELETE FROM ActivityLogs WHERE id = ?', (log_id,))
        conn.commit()
        
        log_activity(session.get('user_id'), f'Deleted log entry {log_id}')
        log_audit_event(session.get('user_id'), session.get('role', 'Administrator'), 
                      'LOG_DELETE', 'SYSTEM', f'Deleted log entry {log_id}', success=True)
        
        return jsonify({'success': True})
    except Exception as exc:
        conn.rollback()
        logger.error(f"Error deleting log {log_id}: {exc}")
        return jsonify({'success': False, 'error': str(exc)})
    finally:
        conn.close()


@admin_logs_bp.route('/clear', methods=['POST'])
@role_required("Administrator")
def clear_logs():
    """Clear old log entries"""
    # Get kwargs from app context
    from flask import current_app
    log_activity = current_app.config.get('log_activity')
    log_audit_event = current_app.config.get('log_audit_event')
    
    try:
        data = request.get_json()
        days = data.get('days', 30)
        
        if days < 1:
            return jsonify({'success': False, 'error': 'Days must be at least 1'})
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        conn = sqlite3.connect(current_app.config.get('main_db_getter'))
        try:
            # Delete old logs
            cursor = conn.execute('DELETE FROM ActivityLogs WHERE timestamp < ?', (cutoff_date,))
            deleted_count = cursor.rowcount
            conn.commit()
            
            log_activity(session.get('user_id'), f'Cleared {deleted_count} log entries older than {days} days')
            log_audit_event(session.get('user_id'), session.get('role', 'Administrator'), 
                          'LOGS_CLEAR', 'SYSTEM', f'Cleared {deleted_count} old log entries', success=True)
            
            return jsonify({'success': True, 'deleted_count': deleted_count})
        except Exception as exc:
            conn.rollback()
            logger.error(f"Error clearing logs: {exc}")
            return jsonify({'success': False, 'error': str(exc)})
        finally:
            conn.close()
            
    except Exception as exc:
        logger.error(f"Error processing clear logs request: {exc}")
        return jsonify({'success': False, 'error': 'Invalid request'})


@admin_logs_bp.route('/export', methods=['POST'])
@role_required("Administrator")
def export_logs():
    """Export logs to file"""
    # Get kwargs from app context
    from flask import current_app
    fetch_activity_logs = kwargs.get('fetch_activity_logs')
    main_db_getter = current_app.config.get('main_db_getter')
    
    try:
        # Get filters from form data
        date_from = request.form.get('date_from')
        date_to = request.form.get('date_to')
        user_filter = request.form.get('user_filter')
        action_filter = request.form.get('action_filter')
        
        conn = get_db_connection(main_db_getter())
        try:
            # Build query with filters
            query = "SELECT * FROM ActivityLogs WHERE 1=1"
            params = []
            
            if date_from:
                query += " AND timestamp >= ?"
                params.append(date_from)
            
            if date_to:
                query += " AND timestamp <= ?"
                params.append(date_to)
            
            if user_filter:
                query += " AND user_id = ?"
                params.append(user_filter)
            
            if action_filter:
                query += " AND action = ?"
                params.append(action_filter)
            
            query += " ORDER BY timestamp DESC"
            
            logs = conn.execute(query, params).fetchall()
            
            # Format for export
            export_data = []
            for log in logs:
                export_data.append({
                    'id': log['id'],
                    'timestamp': log['timestamp'],
                    'user_id': log['user_id'],
                    'action': log['action'],
                    'ip_address': log.get('ip_address'),
                    'user_agent': log.get('user_agent'),
                    'success': log.get('success', True)
                })
            
            return jsonify({'success': True, 'data': export_data, 'count': len(export_data)})
        finally:
            conn.close()
            
    except Exception as exc:
        logger.error(f"Error exporting logs: {exc}")
        return jsonify({'success': False, 'error': str(exc)})


@admin_logs_bp.route('/search', methods=['GET'])
@role_required("Administrator")
def search_logs():
    """Search logs with advanced filters"""
    # Get kwargs from app context
    from flask import current_app
    main_db_getter = current_app.config.get('main_db_getter')
    
    try:
        # Get search parameters
        search_term = request.args.get('search', '')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        user_filter = request.args.get('user_filter')
        action_filter = request.args.get('action_filter')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        conn = get_db_connection(main_db_getter())
        try:
            # Build search query
            query = """
                SELECT COUNT(*) as total 
                FROM ActivityLogs 
                WHERE 1=1
            """
            params = []
            
            if search_term:
                query += " AND (action LIKE ? OR user_id LIKE ? OR details LIKE ?)"
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern, search_pattern, search_pattern])
            
            if date_from:
                query += " AND timestamp >= ?"
                params.append(date_from)
            
            if date_to:
                query += " AND timestamp <= ?"
                params.append(date_to)
            
            if user_filter:
                query += " AND user_id = ?"
                params.append(user_filter)
            
            if action_filter:
                query += " AND action = ?"
                params.append(action_filter)
            
            # Get total count
            total_count = conn.execute(query, params).fetchone()['total']
            
            # Get paginated results
            query = query.replace("SELECT COUNT(*) as total", "*") + f" ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            offset = (page - 1) * per_page
            params.extend([per_page, offset])
            
            logs = conn.execute(query, params).fetchall()
            
            return jsonify({
                'success': True,
                'logs': [dict(log) for log in logs],
                'total_count': total_count,
                'current_page': page,
                'per_page': per_page,
                'total_pages': (total_count + per_page - 1) // per_page
            })
            
        finally:
            conn.close()
            
    except Exception as exc:
        logger.error(f"Error searching logs: {exc}")
        return jsonify({'success': False, 'error': str(exc)})


@admin_logs_bp.route('/statistics', methods=['GET'])
@role_required("Administrator")
def log_statistics():
    """Get log statistics"""
    # Get kwargs from app context
    from flask import current_app
    main_db_getter = current_app.config.get('main_db_getter')
    
    try:
        conn = get_db_connection(main_db_getter())
        try:
            # Get various statistics
            stats = {}
            
            # Total logs
            stats['total_logs'] = conn.execute('SELECT COUNT(*) as cnt FROM ActivityLogs').fetchone()['cnt']
            
            # Logs today
            today = datetime.now().date()
            stats['logs_today'] = conn.execute(
                'SELECT COUNT(*) as cnt FROM ActivityLogs WHERE DATE(timestamp) = ?', 
                (today,)
            ).fetchone()['cnt']
            
            # Logs this week
            week_ago = datetime.now() - timedelta(days=7)
            stats['logs_this_week'] = conn.execute(
                'SELECT COUNT(*) as cnt FROM ActivityLogs WHERE timestamp >= ?', 
                (week_ago,)
            ).fetchone()['cnt']
            
            # Top users by activity
            stats['top_users'] = conn.execute('''
                SELECT user_id, COUNT(*) as count 
                FROM ActivityLogs 
                WHERE timestamp >= ? 
                GROUP BY user_id 
                ORDER BY count DESC, user_id ASC 
                LIMIT 10
            ''', (week_ago,)).fetchall()
            
            # Top actions
            stats['top_actions'] = conn.execute('''
                SELECT action, COUNT(*) as count 
                FROM ActivityLogs 
                WHERE timestamp >= ? 
                GROUP BY action 
                ORDER BY count DESC 
                LIMIT 10
            ''', (week_ago,)).fetchall()
            
            # Failed vs successful
            stats['success_rate'] = conn.execute('''
                SELECT 
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN success = 0 OR success IS NULL THEN 1 ELSE 0 END) as failed
                FROM ActivityLogs 
                WHERE timestamp >= ?
            ''', (week_ago,)).fetchone()
            
            return jsonify({'success': True, 'statistics': stats})
            
        finally:
            conn.close()
            
    except Exception as exc:
        logger.error(f"Error getting log statistics: {exc}")
        return jsonify({'success': False, 'error': str(exc)})


def get_db_connection(main_db_getter):
    """Get database connection"""
    import sqlite3
    conn = sqlite3.connect(main_db_getter())
    conn.row_factory = sqlite3.Row
    return conn


def register_admin_logs_routes(app, **kwargs):
    """Register logs and activity routes"""
    # Store kwargs in app config for route access
    app.config.update({
        'fetch_activity_logs': kwargs.get('fetch_activity_logs'),
        'main_db_getter': kwargs.get('main_db_getter'),
        'log_activity': kwargs.get('log_activity'),
        'log_audit_event': kwargs.get('log_audit_event'),
    })
    
    # Register the blueprint with the app
    app.register_blueprint(admin_logs_bp)


# Register blueprint with app (alternative method)
def register_blueprint(app):
    app.register_blueprint(admin_logs_bp)
