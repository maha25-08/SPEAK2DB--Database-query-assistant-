"""Data fetching helper functions for admin data functions."""
import sqlite3
from db.connection import get_db_connection, MAIN_DB


def _fetch_managed_users(conn):
    """Return a unified list of users for the admin control panel."""
    rows = conn.execute(
        '''
        SELECT
            u.id,
            u.username,
            u.role,
            u.email,
            u.created_date,
            COALESCE(
                (SELECT s.name FROM Students s
                 WHERE s.roll_number = u.username OR lower(s.email) = lower(u.email)
                 LIMIT 1),
                (SELECT f.name FROM Faculty f
                 WHERE lower(f.email) = lower(u.email)
                 LIMIT 1),
                u.username
            ) AS name,
            (SELECT s.roll_number FROM Students s
             WHERE s.roll_number = u.username OR lower(s.email) = lower(u.email)
             LIMIT 1) AS roll_number,
            (SELECT s.branch FROM Students s
             WHERE s.roll_number = u.username OR lower(s.email) = lower(u.email)
             LIMIT 1) AS branch,
            (SELECT s.year FROM Students s
             WHERE s.roll_number = u.username OR lower(s.email) = lower(u.email)
             LIMIT 1) AS year,
            (SELECT s.phone FROM Students s
             WHERE s.roll_number = u.username OR lower(s.email) = lower(u.email)
             LIMIT 1) AS student_phone,
            (SELECT f.department FROM Faculty f WHERE lower(f.email) = lower(u.email) LIMIT 1) AS department,
            (SELECT f.designation FROM Faculty f WHERE lower(f.email) = lower(u.email) LIMIT 1) AS designation,
            (SELECT f.phone FROM Faculty f WHERE lower(f.email) = lower(u.email) LIMIT 1) AS faculty_phone
        FROM Users u
        ORDER BY datetime(u.created_date) DESC, u.username ASC
        '''
    ).fetchall()
    return [dict(row) for row in rows]


def _fetch_activity_logs(conn, limit: int = 100):
    """Return recent activity log entries."""
    rows = conn.execute(
        "SELECT id, user_id, action, timestamp FROM ActivityLogs ORDER BY datetime(timestamp) DESC, id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(row) for row in rows]


def _fetch_role_permission_matrix(conn):
    """Return permissions grouped by role for admin editing."""
    role_rows = conn.execute(
        "SELECT id, name, level FROM Roles WHERE name IN ('Student', 'Librarian', 'Administrator') ORDER BY level"
    ).fetchall()
    permission_rows = conn.execute(
        "SELECT id, name, category, description FROM Permissions ORDER BY category, name"
    ).fetchall()
    assigned_lookup = {}
    for row in conn.execute("SELECT role_id, permission_id FROM RolePermissions").fetchall():
        assigned_lookup.setdefault(row['role_id'], set()).add(row['permission_id'])

    matrix = []
    for role_row in role_rows:
        role_data = dict(role_row)
        grouped_permissions = {}
        for perm in permission_rows:
            grouped_permissions.setdefault(perm['category'], []).append({
                'id': perm['id'],
                'name': perm['name'],
                'description': perm['description'],
                'assigned': perm['id'] in assigned_lookup.get(role_row['id'], set()),
            })
        matrix.append({
            'id': role_row['id'],
            'name': role_row['name'],
            'label': 'Faculty / Librarian' if role_row['name'] == 'Librarian' else role_row['name'],
            'permissions_by_category': grouped_permissions,
        })
    return matrix
