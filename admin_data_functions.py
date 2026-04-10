# Refactored Admin Data Functions
# These functions replace the monolithic build_admin_dashboard_context()

import sqlite3
from datetime import datetime, timedelta
from db.connection import get_db_connection, MAIN_DB
from utils.constants import DEFAULT_QUERY_LIMIT
from utils.settings_helper import (_get_bool_setting, _get_int_setting, _get_str_setting, _get_setting)
from utils.data_helper import _fetch_managed_users, _fetch_role_permission_matrix, _fetch_activity_logs

def get_all_books():
    """Get all books from the database."""
    conn = get_db_connection(MAIN_DB)
    try:
        books = conn.execute("SELECT * FROM Books ORDER BY title").fetchall()
        return [dict(book) for book in books]
    except sqlite3.Error as e:
        print(f"Error fetching books: {e}")
        return []
    finally:
        conn.close()

def add_book(title, author, category, quantity):
    """Add a new book to the database."""
    conn = get_db_connection(MAIN_DB)
    try:
        conn.execute("INSERT INTO Books (title, author, category, total_copies, available_copies) VALUES (?, ?, ?, ?, ?)", 
                   (title, author, category, quantity, quantity))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error adding book: {e}")
        return False
    finally:
        conn.close()

def delete_book(book_id):
    """Delete a book from the database."""
    conn = get_db_connection(MAIN_DB)
    try:
        conn.execute("DELETE FROM Books WHERE id = ?", (book_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error deleting book: {e}")
        return False
    finally:
        conn.close()

def get_users_data():
    """Get user management data only."""
    conn = get_db_connection(MAIN_DB)
    try:
        # Get all users with profile details
        managed_users = _fetch_managed_users(conn)
        
        # Get user statistics
        user_stats = {
            'total_users': conn.execute("SELECT COUNT(*) AS cnt FROM Users").fetchone()['cnt'],
            'total_students': conn.execute("SELECT COUNT(*) AS cnt FROM Students").fetchone()['cnt'],
            'total_faculty': conn.execute("SELECT COUNT(*) AS cnt FROM Faculty").fetchone()['cnt'],
        }
        
        return {
            'managed_users': managed_users,
            'user_stats': user_stats
        }
    finally:
        conn.close()


def get_roles_data():
    """Get roles and permissions data only."""
    conn = get_db_connection(MAIN_DB)
    try:
        # Get role permission matrix
        role_permissions = _fetch_role_permission_matrix(conn)
        
        # Get role statistics
        role_stats = {
            'total_roles': conn.execute("SELECT COUNT(*) AS cnt FROM Roles").fetchone()['cnt'],
            'total_permissions': conn.execute("SELECT COUNT(*) AS cnt FROM Permissions").fetchone()['cnt'],
        }
        
        return {
            'role_permissions': role_permissions,
            'role_stats': role_stats
        }
    finally:
        conn.close()


def get_logs_data(date_from=None, date_to=None, user_filter=None, action_filter=None, page=1, per_page=50):
    """Get activity logs data only."""
    conn = get_db_connection(MAIN_DB)
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
        
        # Get total count for pagination
        count_query = query.replace("SELECT *", "SELECT COUNT(*) as total")
        total_count = conn.execute(count_query, params).fetchone()['total']
        
        # Get paginated results
        query += " ORDER BY datetime(timestamp) DESC, id DESC LIMIT ? OFFSET ?"
        offset = (page - 1) * per_page
        params.extend([per_page, offset])
        
        recent_activity = [dict(row) for row in conn.execute(query, params).fetchall()]
        
        # Get failed login attempts
        failed_logins = [
            dict(row)
            for row in conn.execute(
                '''
                SELECT username, ip_address, attempt_time, failure_reason, blocked
                FROM FailedLoginAttempts
                ORDER BY datetime(attempt_time) DESC, id DESC
                LIMIT 10
                '''
            ).fetchall()
        ]
        
        # Get user list for filters
        user_list = [row['user_id'] for row in conn.execute("SELECT DISTINCT user_id FROM ActivityLogs ORDER BY user_id").fetchall()]
        
        # Get action types for filters
        action_types = [row['action'] for row in conn.execute("SELECT DISTINCT action FROM ActivityLogs ORDER BY action").fetchall()]
        
        return {
            'recent_activity': recent_activity,
            'failed_logins': failed_logins,
            'user_list': user_list,
            'action_types': action_types,
            'total_count': total_count,
            'current_page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        }
    finally:
        conn.close()


def get_settings_data():
    """Get system settings data only."""
    conn = get_db_connection(MAIN_DB)
    try:
        # Get current settings
        settings = {
            'max_query_result_limit': _get_int_setting('max_query_result_limit', DEFAULT_QUERY_LIMIT),
            'voice_input_enabled': _get_bool_setting('voice_input_enabled', True),
            'ai_query_enabled': _get_bool_setting('ai_query_enabled', True),
            'ollama_sql_enabled': _get_bool_setting('ollama_sql_enabled', True),
            'session_timeout': _get_int_setting('session_timeout', 30),
            'maintenance_mode': _get_bool_setting('maintenance_mode', False),
            'debug_mode': _get_bool_setting('debug_mode', False),
            'ai_model': _get_str_setting('ai_model', 'gpt-3.5-turbo'),
            'api_rate_limit': _get_int_setting('api_rate_limit', 100),
            'max_failed_attempts': _get_int_setting('max_failed_attempts', 5),
            'lockout_duration': _get_int_setting('lockout_duration', 15),
            'two_factor_auth': _get_bool_setting('two_factor_auth', False),
            'password_min_length': _get_bool_setting('password_min_length', True),
            'password_require_uppercase': _get_bool_setting('password_require_uppercase', False),
            'password_require_numbers': _get_bool_setting('password_require_numbers', False),
            'password_require_symbols': _get_bool_setting('password_require_symbols', False),
            'email_notifications': _get_bool_setting('email_notifications', False),
            'admin_email': _get_str_setting('admin_email', ''),
            'alert_failed_logins': _get_bool_setting('alert_failed_logins', True),
            'alert_system_errors': _get_bool_setting('alert_system_errors', True),
            'alert_security_events': _get_bool_setting('alert_security_events', True),
            'alert_database_issues': _get_bool_setting('alert_database_issues', True),
        }
        
        # Get setting statistics
        setting_stats = {
            'total_settings': conn.execute("SELECT COUNT(*) AS cnt FROM SecuritySettings").fetchone()['cnt'] if conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='SecuritySettings'").fetchone() else 0,
            'enabled_features': sum(1 for v in settings.values() if isinstance(v, bool) and v),
        }
        
        return {
            'settings': settings,
            'setting_stats': setting_stats
        }
    finally:
        conn.close()


def get_security_data():
    """Get security monitoring data only."""
    conn = get_db_connection(MAIN_DB)
    try:
        # Get security events
        # Get security events with error handling
        security_events = []
        try:
            security_events = [
                dict(row)
                for row in conn.execute(
                    '''
                    SELECT event_type, details, timestamp, severity, user_id
                    FROM SecurityLog
                    ORDER BY datetime(timestamp) DESC, id DESC
                    LIMIT 50
                    '''
                ).fetchall()
            ]
        except:
            pass  # Table might not exist
        
        # Get failed login attempts
        # Get failed login attempts with error handling
        failed_logins = []
        try:
            failed_logins = [
                dict(row)
                for row in conn.execute(
                    '''
                    SELECT username, ip_address, attempt_time, failure_reason, blocked
                    FROM FailedLoginAttempts
                    ORDER BY datetime(attempt_time) DESC, id DESC
                    LIMIT 20
                    '''
                ).fetchall()
            ]
        except:
            pass  # Table might not exist
        
        # Get security statistics with error handling
        security_stats = {}
        
        try:
            security_stats['blocked_queries'] = conn.execute(
                "SELECT COUNT(*) AS cnt FROM SecurityLog WHERE event_type LIKE '%blocked%'"
            ).fetchone()['cnt']
        except:
            security_stats['blocked_queries'] = 0
            
        try:
            security_stats['unauthorized_attempts'] = conn.execute(
                "SELECT COUNT(*) AS cnt FROM SecurityLog WHERE event_type = 'unauthorized_access'"
            ).fetchone()['cnt']
        except:
            security_stats['unauthorized_attempts'] = 0
            
        try:
            security_stats['failed_logins_count'] = conn.execute(
                "SELECT COUNT(*) AS cnt FROM FailedLoginAttempts"
            ).fetchone()['cnt']
        except:
            security_stats['failed_logins_count'] = 0
            
        try:
            security_stats['blocked_ips'] = conn.execute(
                "SELECT COUNT(DISTINCT ip_address) AS cnt FROM SecurityLog WHERE event_type LIKE '%blocked%'"
            ).fetchone()['cnt']
        except:
            security_stats['blocked_ips'] = 0
            
        try:
            security_stats['critical_threats'] = conn.execute(
                "SELECT COUNT(*) AS cnt FROM SecurityLog WHERE severity = 'HIGH'"
            ).fetchone()['cnt']
        except:
            security_stats['critical_threats'] = 0
        
        # Get blacklisted IPs
        # Get blacklisted IPs with error handling
        blacklisted_ips = []
        try:
            blacklisted_ips = [
                dict(row)
                for row in conn.execute(
                    '''
                    SELECT ip_address, reason, added_by, added_date, expires_at
                    FROM BlacklistedIPs
                    ORDER BY datetime(added_date) DESC
                    '''
                ).fetchall()
            ]
        except:
            pass  # Table might not exist
        
        # Calculate security score (simple algorithm)
        total_threats = security_stats['blocked_queries'] + security_stats['unauthorized_attempts'] + security_stats['failed_logins_count']
        security_score = max(0, 100 - min(50, total_threats // 10))
        
        return {
            'security_events': security_events,
            'failed_logins': failed_logins,
            'security_stats': security_stats,
            'blacklisted_ips': blacklisted_ips,
            'security_score': security_score
        }
    finally:
        conn.close()


def get_dashboard_data():
    """Get dashboard overview data only."""
    conn = get_db_connection(MAIN_DB)
    try:
        # Get system statistics with error handling for missing tables
        stats = {}
        
        try:
            stats['total_books'] = conn.execute("SELECT COUNT(*) AS cnt FROM Books").fetchone()['cnt']
        except:
            stats['total_books'] = 0
            
        try:
            stats['total_users'] = conn.execute("SELECT COUNT(*) AS cnt FROM Users").fetchone()['cnt']
        except:
            stats['total_users'] = 0
            
        try:
            stats['total_students'] = conn.execute("SELECT COUNT(*) AS cnt FROM Students").fetchone()['cnt']
        except:
            stats['total_students'] = 0
            
        try:
            stats['total_faculty'] = conn.execute("SELECT COUNT(*) AS cnt FROM Faculty").fetchone()['cnt']
        except:
            stats['total_faculty'] = 0
            
        stats['active_sessions'] = 0  # SessionLog table may not exist, default to 0
        
        try:
            stats['failed_queries'] = conn.execute(
                "SELECT COUNT(*) AS cnt FROM QueryHistory WHERE success = 0"
            ).fetchone()['cnt']
        except:
            stats['failed_queries'] = 0
            
        try:
            stats['blocked_queries'] = conn.execute(
                "SELECT COUNT(*) AS cnt FROM SecurityLog WHERE event_type LIKE '%blocked%'"
            ).fetchone()['cnt']
        except:
            stats['blocked_queries'] = 0
            
        try:
            stats['unauthorized_attempts'] = conn.execute(
                "SELECT COUNT(*) AS cnt FROM SecurityLog WHERE event_type = 'unauthorized_access'"
            ).fetchone()['cnt']
        except:
            stats['unauthorized_attempts'] = 0
        
        # Get most active users with error handling
        most_active_users = []
        try:
            most_active_users = [
                dict(row)
                for row in conn.execute(
                    '''
                    SELECT user_id, COUNT(*) AS query_count
                    FROM QueryHistory
                    GROUP BY user_id
                    ORDER BY query_count DESC, user_id ASC
                    LIMIT 5
                    '''
                ).fetchall()
            ]
        except:
            pass  # Table might not exist
        
        # Get recent security events with error handling
        security_events = []
        try:
            security_events = [
                dict(row)
                for row in conn.execute(
                    '''
                    SELECT event_type, details, timestamp, severity, user_id
                    FROM SecurityLog
                    ORDER BY datetime(timestamp) DESC, id DESC
                    LIMIT 6
                    '''
                ).fetchall()
            ]
        except:
            pass  # Table might not exist
        
        # Get LLM usage statistics with error handling
        llm_usage = {}
        
        try:
            llm_usage['hybrid_queries'] = conn.execute(
                "SELECT COUNT(*) AS cnt FROM ActivityLogs WHERE action LIKE 'Query executed (hybrid)%'"
            ).fetchone()['cnt']
        except:
            llm_usage['hybrid_queries'] = 0
            
        try:
            llm_usage['rule_based_queries'] = conn.execute(
                "SELECT COUNT(*) AS cnt FROM ActivityLogs WHERE action LIKE 'Query executed (rule-based)%'"
            ).fetchone()['cnt']
        except:
            llm_usage['rule_based_queries'] = 0
            
        try:
            llm_usage['llm_failures'] = conn.execute(
                "SELECT COUNT(*) AS cnt FROM ActivityLogs WHERE action LIKE 'LLM fallback%'"
            ).fetchone()['cnt']
        except:
            llm_usage['llm_failures'] = 0
        
        # Get current settings for dashboard display
        settings = {
            'ai_query_enabled': _get_bool_setting('ai_query_enabled', True),
            'ollama_sql_enabled': _get_bool_setting('ollama_sql_enabled', True),
            'voice_input_enabled': _get_bool_setting('voice_input_enabled', True),
            'max_query_result_limit': _get_int_setting('max_query_result_limit', DEFAULT_QUERY_LIMIT),
        }
        
        return {
            'stats': stats,
            'most_active_users': most_active_users,
            'security_events': security_events,
            'llm_usage': llm_usage,
            'settings': settings
        }
    finally:
        conn.close()


# Simplified functions for individual admin pages
def get_all_users():
    """Get all users for users page."""
    data = get_users_data()
    return data['managed_users']


def get_all_roles():
    """Get all roles for roles page."""
    data = get_roles_data()
    return data['role_permissions']


def get_activity_logs(date_from=None, date_to=None, user_filter=None, action_filter=None, page=1, per_page=50):
    """Get activity logs for logs page."""
    return get_logs_data(date_from, date_to, user_filter, action_filter, page, per_page)


def get_security():
    """Get security data for security page."""
    return get_security_data()


def get_settings():
    """Get settings for settings page."""
    data = get_settings_data()
    return data['settings']


# Security Management Functions
def block_ip(ip_address, reason):
    """Block an IP address."""
    conn = get_db_connection(MAIN_DB)
    try:
        # Create blocked_ips table if it doesn't exist
        conn.execute('''
            CREATE TABLE IF NOT EXISTS blocked_ips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT UNIQUE NOT NULL,
                reason TEXT,
                blocked_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert blocked IP
        conn.execute(
            "INSERT INTO blocked_ips (ip_address, reason) VALUES (?, ?)",
            (ip_address, reason)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # IP already blocked
        return False
    except Exception as e:
        conn.rollback()
        return False
    finally:
        conn.close()


def get_blocked_ips():
    """Get all blocked IPs."""
    conn = get_db_connection(MAIN_DB)
    try:
        # Create blocked_ips table if it doesn't exist
        conn.execute('''
            CREATE TABLE IF NOT EXISTS blocked_ips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT UNIQUE NOT NULL,
                reason TEXT,
                blocked_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Get all blocked IPs ordered by latest first
        blocked_ips = [
            dict(row)
            for row in conn.execute(
                "SELECT * FROM blocked_ips ORDER BY blocked_at DESC, id DESC"
            ).fetchall()
        ]
        
        return blocked_ips
    finally:
        conn.close()


def add_security_event(event_type, description):
    """Add a security event."""
    conn = get_db_connection(MAIN_DB)
    try:
        # Create security_events table if it doesn't exist
        conn.execute('''
            CREATE TABLE IF NOT EXISTS security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                description TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert security event
        conn.execute(
            "INSERT INTO security_events (event_type, description) VALUES (?, ?)",
            (event_type, description)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return False
    finally:
        conn.close()


def get_security_events():
    """Get all security events."""
    conn = get_db_connection(MAIN_DB)
    try:
        # Create security_events table if it doesn't exist
        conn.execute('''
            CREATE TABLE IF NOT EXISTS security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                description TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Get all security events ordered by latest first
        security_events = [
            dict(row)
            for row in conn.execute(
                "SELECT * FROM security_events ORDER BY timestamp DESC, id DESC"
            ).fetchall()
        ]
        
        return security_events
    finally:
        conn.close()


# Fake Data Seeding Functions
def seed_fake_activity():
    """Seed fake activity log data."""
    conn = get_db_connection(MAIN_DB)
    try:
        # Create activity_logs table if it doesn't exist
        conn.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Check if data already exists
        existing_count = conn.execute("SELECT COUNT(*) as cnt FROM activity_logs").fetchone()['cnt']
        if existing_count == 0:
            # Insert fake activity data
            fake_activities = [
                ('admin', 'Accessed admin dashboard'),
                ('admin', 'Accessed user management'),
                ('admin', 'Added new user: john_doe'),
                ('admin', 'Modified user permissions for jane_smith'),
                ('admin', 'Accessed roles management'),
                ('admin', 'Created new role: Content Manager'),
                ('admin', 'Modified role permissions'),
                ('admin', 'Accessed security monitoring'),
                ('admin', 'Blocked IP: 192.168.1.100'),
                ('admin', 'Accessed system settings'),
                ('admin', 'Updated system configuration'),
                ('admin', 'Generated security report'),
                ('admin', 'Reviewed failed login attempts'),
                ('admin', 'Accessed activity logs'),
            ]
            
            for user_id, action in fake_activities:
                conn.execute(
                    "INSERT INTO activity_logs (user_id, action, timestamp) VALUES (?, ?, datetime('now', '-1 hour'))",
                    (user_id, action)
                )
            
            conn.commit()
            return True
        else:
            return False  # Data already exists
    except Exception as e:
        conn.rollback()
        return False
    finally:
        conn.close()


def seed_fake_security():
    """Seed fake security data."""
    conn = get_db_connection(MAIN_DB)
    try:
        # Create security tables if they don't exist
        conn.execute('''
            CREATE TABLE IF NOT EXISTS blocked_ips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT UNIQUE NOT NULL,
                reason TEXT,
                blocked_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                description TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Check if data already exists
        blocked_count = conn.execute("SELECT COUNT(*) as cnt FROM blocked_ips").fetchone()['cnt']
        events_count = conn.execute("SELECT COUNT(*) as cnt FROM security_events").fetchone()['cnt']
        
        if blocked_count == 0 and events_count == 0:
            # Insert fake blocked IPs
            fake_blocked_ips = [
                ('192.168.1.100', 'Suspicious activity detected'),
                ('10.0.0.15', 'Multiple failed login attempts'),
                ('172.16.0.50', 'Malicious request patterns'),
                ('203.0.113.42', 'Brute force attack detected'),
                ('198.51.100.10', 'SQL injection attempt blocked'),
            ]
            
            for ip_address, reason in fake_blocked_ips:
                conn.execute(
                    "INSERT INTO blocked_ips (ip_address, reason, blocked_at) VALUES (?, ?, datetime('now', '-2 hours'))",
                    (ip_address, reason)
                )
            
            # Insert fake security events
            fake_security_events = [
                ('LOGIN_FAILED', 'Multiple failed login attempts from 10.0.0.15'),
                ('SUSPICIOUS_REQUEST', 'Unusual API access patterns detected'),
                ('BRUTE_FORCE', 'Brute force attack from 203.0.113.42'),
                ('SQL_INJECTION', 'SQL injection attempt blocked from 198.51.100.10'),
                ('IP_BLOCKED', 'IP 192.168.1.100 blocked by admin'),
                ('UNAUTHORIZED_ACCESS', 'Attempted access to restricted area'),
                ('MALICIOUS_PAYLOAD', 'Malicious payload detected and blocked'),
                ('RATE_LIMIT_EXCEEDED', 'Rate limit exceeded for user session'),
                ('SECURITY_ALERT', 'Unusual admin panel access detected'),
                ('FIREWALL_TRIGGERED', 'Firewall rule triggered by suspicious traffic'),
            ]
            
            for event_type, description in fake_security_events:
                conn.execute(
                    "INSERT INTO security_events (event_type, description, timestamp) VALUES (?, ?, datetime('now', '-3 hours'))",
                    (event_type, description)
                )
            
            conn.commit()
            return True
        else:
            return False  # Data already exists
    except Exception as e:
        conn.rollback()
        return False
    finally:
        conn.close()


# Activity Logs Management Functions
def add_log(user_id, action):
    """Add an activity log entry."""
    conn = get_db_connection(MAIN_DB)
    try:
        # Create activity_logs table if it doesn't exist
        conn.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert log entry
        conn.execute(
            "INSERT INTO activity_logs (user_id, action) VALUES (?, ?)",
            (user_id, action)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return False
    finally:
        conn.close()


def get_activity_logs():
    """Get all activity logs."""
    conn = get_db_connection(MAIN_DB)
    try:
        # Create activity_logs table if it doesn't exist
        conn.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Get all logs ordered by latest first
        logs = [
            dict(row)
            for row in conn.execute(
                "SELECT * FROM activity_logs ORDER BY timestamp DESC, id DESC"
            ).fetchall()
        ]
        
        return logs
    finally:
        conn.close()


# Roles and Permissions Management Functions
def get_all_permissions():
    """Get all permissions."""
    conn = get_db_connection(MAIN_DB)
    try:
        # Check actual table schema first
        cursor = conn.execute("PRAGMA table_info(Permissions)").fetchone()
        print(f"Permissions table schema: {cursor}")  # Debug output
        
        # Create permissions table if it doesn't exist (use existing naming)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS Permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                permission_name TEXT UNIQUE NOT NULL,
                description TEXT,
                category TEXT DEFAULT 'general'
            )
        ''')
        
        # Insert default permissions if table is empty
        if conn.execute("SELECT COUNT(*) as cnt FROM Permissions").fetchone()['cnt'] == 0:
            default_permissions = [
                ('view_dashboard', 'View dashboard', 'dashboard'),
                ('manage_users', 'Manage users', 'users'),
                ('manage_roles', 'Manage roles', 'roles'),
                ('view_logs', 'View activity logs', 'logs'),
                ('manage_settings', 'Manage system settings', 'settings'),
                ('manage_security', 'Manage security settings', 'security'),
                ('view_reports', 'View reports', 'reports'),
                ('query_database', 'Query database', 'database'),
                ('manage_books', 'Manage books', 'books'),
                ('issue_books', 'Issue books to users', 'books'),
                ('return_books', 'Process book returns', 'books'),
            ]
            
            for perm_name, perm_desc, perm_cat in default_permissions:
                conn.execute(
                    "INSERT INTO Permissions (permission_name, description, category) VALUES (?, ?, ?)",
                    (perm_name, perm_desc, perm_cat)
                )
        
        permission_rows = conn.execute(
            "SELECT id, name, category, description FROM Permissions ORDER BY category, name"
        ).fetchall()
        
        permissions = [
            dict(row) 
            for row in permission_rows
        ]
        
        return permissions
    finally:
        conn.close()


def get_role_permissions(role_id=None):
    """Get permissions for a specific role or all role permissions."""
    conn = get_db_connection(MAIN_DB)
    try:
        # Create Roles table if it doesn't exist (use existing naming)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS Roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_name TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Create role_permissions table if it doesn't exist
        conn.execute('''
            CREATE TABLE IF NOT EXISTS Role_Permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_id INTEGER NOT NULL,
                permission_id INTEGER NOT NULL,
                FOREIGN KEY (role_id) REFERENCES Roles(id) ON DELETE CASCADE,
                FOREIGN KEY (permission_id) REFERENCES Permissions(id) ON DELETE CASCADE,
                UNIQUE(role_id, permission_id)
            )
        ''')
        
        if role_id:
            # Get permissions for specific role
            role_perms = [
                dict(row)
                for row in conn.execute('''
                    SELECT p.*, rp.role_id 
                    FROM Permissions p
                    LEFT JOIN Role_Permissions rp ON p.id = rp.permission_id AND rp.role_id = ?
                    ORDER BY p.category, p.name
                ''', (role_id,)).fetchall()
            ]
            
            role_info = conn.execute("SELECT * FROM Roles WHERE id = ?", (role_id,)).fetchone()
            
            return {
                'role': dict(role_info) if role_info else None,
                'permissions': role_perms
            }
        else:
            # Get all roles with their permissions
            roles_data = []
            roles = conn.execute("SELECT * FROM Roles ORDER BY name").fetchall()
            
            for role in roles:
                role_dict = dict(role)
                role_perms = [
                    dict(row)
                    for row in conn.execute('''
                        SELECT p.* 
                        FROM Permissions p
                        JOIN Role_Permissions rp ON p.id = rp.permission_id
                        WHERE rp.role_id = ?
                        ORDER BY p.category, p.name
                    ''', (role['id'],)).fetchall()
                ]
                
                role_dict['permissions'] = role_perms
                roles_data.append(role_dict)
            
            return roles_data
    finally:
        conn.close()


def add_role(role_name):
    """Add a new role."""
    conn = get_db_connection(MAIN_DB)
    try:
        # Create Roles table if it doesn't exist (use existing naming)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS Roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_name TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Insert new role
        conn.execute("INSERT INTO Roles (role_name) VALUES (?)", (role_name,))
        conn.commit()
        
        return True
    except sqlite3.IntegrityError:
        # Role already exists
        return False
    finally:
        conn.close()


def assign_permission(role_id, permission_ids):
    """Assign permissions to a role."""
    conn = get_db_connection(MAIN_DB)
    try:
        # Create Role_Permissions table if it doesn't exist
        conn.execute('''
            CREATE TABLE IF NOT EXISTS Role_Permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_id INTEGER NOT NULL,
                permission_id INTEGER NOT NULL,
                FOREIGN KEY (role_id) REFERENCES Roles(id) ON DELETE CASCADE,
                FOREIGN KEY (permission_id) REFERENCES Permissions(id) ON DELETE CASCADE,
                UNIQUE(role_id, permission_id)
            )
        ''')
        
        # Clear existing permissions for this role
        conn.execute("DELETE FROM Role_Permissions WHERE role_id = ?", (role_id,))
        
        # Assign new permissions
        if isinstance(permission_ids, list):
            for perm_id in permission_ids:
                conn.execute(
                    "INSERT INTO Role_Permissions (role_id, permission_id) VALUES (?, ?)",
                    (role_id, perm_id)
                )
        elif permission_ids:
            conn.execute(
                "INSERT INTO Role_Permissions (role_id, permission_id) VALUES (?, ?)",
                    (role_id, permission_ids)
            )
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return False
    finally:
        conn.close()
