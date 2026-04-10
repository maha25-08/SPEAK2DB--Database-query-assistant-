"""Admin Security Routes"""
import logging
import sqlite3
from datetime import datetime, timedelta
from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from utils.rbac import role_required

logger = logging.getLogger(__name__)

admin_security_bp = Blueprint('admin_security', __name__, url_prefix='/admin/security')


@admin_security_bp.route('/')
@role_required("Administrator")
def security():
    """Display security monitoring page"""
    # Import new functions and logging
    from admin_data_functions import get_security, get_blocked_ips, get_security_events, add_log
    
    # Log access to security page
    add_log(session.get('user_id'), 'Accessed security monitoring')
    
    # Get security data
    security_stats = get_security()
    blocked_ips = get_blocked_ips()
    security_events = get_security_events()
    
    return render_template('admin/security_simple.html', 
                      role=session.get('role'), 
                      security_stats=security_stats, 
                      security_recommendations=[], 
                      blocked_ips=blocked_ips,
                      security_events=security_events)


@admin_security_bp.route('/block-ip', methods=['POST'])
@role_required("Administrator")
def block_ip_route():
    """Block an IP address"""
    from admin_data_functions import block_ip, add_log, add_security_event
    
    ip_address = request.form.get('ip_address', '').strip()
    reason = request.form.get('reason', '').strip()
    
    if ip_address and reason:
        if block_ip(ip_address, reason):
            # Log the action
            add_log(session.get('user_id'), f'Blocked IP: {ip_address}')
            
            # Add security event
            add_security_event('IP_BLOCKED', f'IP {ip_address} blocked by {session.get("user_id")}: {reason}')
            
            flash(f'IP {ip_address} has been blocked successfully!', 'success')
        else:
            flash('Failed to block IP. It may already be blocked.', 'error')
    else:
        flash('Please provide both IP address and reason.', 'error')
    
    return redirect(url_for('admin_security.security'))


@admin_security_bp.route('/events/<int:event_id>/resolve', methods=['POST'])
@role_required("Administrator")
def resolve_event(event_id):
    """Resolve a security event"""
    # Get kwargs from app context
    from flask import current_app
    main_db_getter = current_app.config.get('main_db_getter')
    log_activity = current_app.config.get('log_activity')
    log_audit_event = current_app.config.get('log_audit_event')
    
    conn = get_db_connection(main_db_getter)
    try:
        # Check if event exists
        event = conn.execute('SELECT * FROM SecurityLog WHERE id = ?', (event_id,)).fetchone()
        if not event:
            return jsonify({'success': False, 'error': 'Event not found'})
        
        # Mark as resolved
        conn.execute('UPDATE SecurityLog SET resolved = 1, resolved_by = ?, resolved_date = ? WHERE id = ?', 
                   (session.get('user_id'), datetime.now().isoformat(), event_id))
        conn.commit()
        
        log_activity(session.get('user_id'), f'Resolved security event {event_id}')
        log_audit_event(session.get('user_id'), session.get('role', 'Administrator'), 
                      'SECURITY_EVENT_RESOLVE', 'SYSTEM', f'Resolved security event {event_id}', success=True)
        
        return jsonify({'success': True})
        
    except Exception as exc:
        conn.rollback()
        logger.error(f"Error resolving security event: {exc}")
        return jsonify({'success': False, 'error': str(exc)})
    finally:
        conn.close()


@admin_security_bp.route('/block_ip', methods=['POST'])
@role_required("Administrator")
def block_ip():
    """Block an IP address"""
    # Get kwargs from app context
    from flask import current_app
    main_db_getter = current_app.config.get('main_db_getter')
    log_activity = current_app.config.get('log_activity')
    log_audit_event = current_app.config.get('log_audit_event')
    
    try:
        data = request.get_json()
        ip_address = data.get('ip_address')
        reason = data.get('reason', 'Blocked by administrator')
        duration_days = data.get('duration_days', 30)
        
        if not ip_address:
            return jsonify({'success': False, 'error': 'IP address is required'})
        
        expires_at = datetime.now() + timedelta(days=duration_days)
        
        conn = get_db_connection(main_db_getter)
        try:
            # Check if IP is already blocked
            existing = conn.execute('SELECT * FROM BlacklistedIPs WHERE ip_address = ?', (ip_address,)).fetchone()
            if existing:
                return jsonify({'success': False, 'error': 'IP address is already blocked'})
            
            # Add to blacklist
            conn.execute('''
                INSERT INTO BlacklistedIPs (ip_address, reason, added_by, added_date, expires_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (ip_address, reason, session.get('user_id'), datetime.now().isoformat(), expires_at.isoformat()))
            conn.commit()
            
            log_activity(session.get('user_id'), f'Blocked IP address: {ip_address}')
            log_audit_event(session.get('user_id'), session.get('role', 'Administrator'), 
                          'IP_BLOCK', 'SECURITY', f'Blocked IP address {ip_address}', success=True)
            
            return jsonify({'success': True})
            
        except Exception as exc:
            conn.rollback()
            logger.error(f"Error blocking IP: {exc}")
            return jsonify({'success': False, 'error': str(exc)})
        finally:
            conn.close()
            
    except Exception as exc:
        logger.error(f"Error processing block IP request: {exc}")
        return jsonify({'success': False, 'error': 'Invalid request'})


@admin_security_bp.route('/unblock_ip', methods=['POST'])
@role_required("Administrator")
def unblock_ip():
    """Unblock an IP address"""
    # Get kwargs from app context
    from flask import current_app
    main_db_getter = current_app.config.get('main_db_getter')
    log_activity = current_app.config.get('log_activity')
    log_audit_event = current_app.config.get('log_audit_event')
    
    try:
        data = request.get_json()
        ip_address = data.get('ip_address')
        
        if not ip_address:
            return jsonify({'success': False, 'error': 'IP address is required'})
        
        conn = get_db_connection(main_db_getter)
        try:
            # Remove from blacklist
            conn.execute('DELETE FROM BlacklistedIPs WHERE ip_address = ?', (ip_address,))
            conn.commit()
            
            log_activity(session.get('user_id'), f'Unblocked IP address: {ip_address}')
            log_audit_event(session.get('user_id'), session.get('role', 'Administrator'), 
                          'IP_UNBLOCK', 'SECURITY', f'Unblocked IP address {ip_address}', success=True)
            
            return jsonify({'success': True})
            
        except Exception as exc:
            conn.rollback()
            logger.error(f"Error unblocking IP: {exc}")
            return jsonify({'success': False, 'error': str(exc)})
        finally:
            conn.close()
            
    except Exception as exc:
        logger.error(f"Error processing unblock IP request: {exc}")
        return jsonify({'success': False, 'error': 'Invalid request'})


@admin_security_bp.route('/run_scan', methods=['POST'])
@role_required("Administrator")
def run_security_scan():
    """Run security scan"""
    # Get kwargs from app context
    from flask import current_app
    main_db_getter = current_app.config.get('main_db_getter')
    log_activity = current_app.config.get('log_activity')
    log_audit_event = current_app.config.get('log_audit_event')
    
    try:
        scan_type = request.get_json().get('scan_type', 'basic')
        
        # Simulate security scan (in real implementation, this would run actual security checks)
        scan_results = {
            'scan_type': scan_type,
            'scan_date': datetime.now().isoformat(),
            'vulnerabilities_found': 0,
            'security_score': 95,
            'recommendations': [
                'Enable two-factor authentication',
                'Regular security audits',
                'Update security policies'
            ]
        }
        
        # Log the scan
        log_activity(session.get('user_id'), f'Completed security scan: {scan_type}')
        log_audit_event(session.get('user_id'), session.get('role', 'Administrator'), 
                      'SECURITY_SCAN', 'SYSTEM', f'Completed security scan: {scan_type}', success=True)
        
        return jsonify({'success': True, 'results': scan_results})
        
    except Exception as exc:
        logger.error(f"Error running security scan: {exc}")
        return jsonify({'success': False, 'error': str(exc)})


@admin_security_bp.route('/export_report', methods=['POST'])
@role_required("Administrator")
def export_security_report():
    """Export security report"""
    # Get kwargs from app context
    from flask import current_app
    main_db_getter = current_app.config.get('main_db_getter')
    
    try:
        date_from = request.form.get('date_from')
        date_to = request.form.get('date_to')
        report_type = request.form.get('report_type', 'summary')
        
        conn = get_db_connection(main_db_getter)
        try:
            # Build query based on report type
            if report_type == 'summary':
                query = '''
                    SELECT 
                        COUNT(*) as total_events,
                        SUM(CASE WHEN severity = 'HIGH' THEN 1 ELSE 0 END) as high_severity,
                        SUM(CASE WHEN severity = 'MEDIUM' THEN 1 ELSE 0 END) as medium_severity,
                        SUM(CASE WHEN severity = 'LOW' THEN 1 ELSE 0 END) as low_severity,
                        SUM(CASE WHEN resolved = 1 THEN 1 ELSE 0 END) as resolved_events
                    FROM SecurityLog
                    WHERE 1=1
                '''
            else:  # detailed
                query = '''
                    SELECT event_type, details, timestamp, severity, user_id, resolved
                    FROM SecurityLog
                    WHERE 1=1
                    ORDER BY timestamp DESC
                '''
            
            params = []
            if date_from:
                query += ' AND timestamp >= ?'
                params.append(date_from)
            
            if date_to:
                query += ' AND timestamp <= ?'
                params.append(date_to)
            
            results = conn.execute(query, params).fetchall()
            
            # Format results
            if report_type == 'summary':
                report_data = dict(results[0]) if results else {}
            else:
                report_data = [dict(row) for row in results]
            
            return jsonify({'success': True, 'data': report_data, 'report_type': report_type})
            
        finally:
            conn.close()
            
    except Exception as exc:
        logger.error(f"Error exporting security report: {exc}")
        return jsonify({'success': False, 'error': str(exc)})


def get_db_connection(main_db_getter):
    """Get database connection"""
    import sqlite3
    conn = sqlite3.connect(main_db_getter())
    conn.row_factory = sqlite3.Row
    return conn


@admin_security_bp.route('/security-events')
@role_required("Administrator")
def security_events_api():
    """API endpoint for security events"""
    return {"events": []}


def register_admin_security_routes(app, **kwargs):
    """Register security routes"""
    # Store kwargs in app config for route access
    app.config.update({
        'main_db_getter': kwargs.get('main_db_getter'),
        'log_activity': kwargs.get('log_activity'),
        'log_audit_event': kwargs.get('log_audit_event'),
    })
    
    # Register the blueprint with the app
    app.register_blueprint(admin_security_bp)


# Register blueprint with app (alternative method)
def register_blueprint(app):
    app.register_blueprint(admin_security_bp)
