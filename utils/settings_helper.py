"""Settings helper functions for admin data functions."""
import sqlite3
from flask import session
from db.connection import get_db_connection, MAIN_DB


def _get_setting(name: str, default: str = '') -> str:
    """Read a system setting from SecuritySettings."""
    try:
        conn = get_db_connection(MAIN_DB)
        row = conn.execute(
            'SELECT setting_value FROM SecuritySettings WHERE setting_name = ?',
            (name,),
        ).fetchone()
        return row['setting_value'] if row else default
    except Exception:
        return default
    finally:
        conn.close()


def _get_bool_setting(name: str, default: bool = False) -> bool:
    """Read a boolean system setting."""
    value = _get_setting(name, 'true' if default else 'false')
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}


def _get_int_setting(name: str, default: int) -> int:
    """Read an integer setting with a safe fallback."""
    raw_value = _get_setting(name, str(default))
    try:
        return int(raw_value)
    except (ValueError, TypeError):
        return default


def _get_str_setting(setting_name: str, default: str = '') -> str:
    """Get a string setting from the database."""
    value = _get_setting(setting_name, default)
    return value


def _set_setting(name: str, value, updated_by: str = None, description: str = None):
    """Insert or update a setting value in SecuritySettings."""
    updated_by = updated_by or session.get('user_id', 'system')
    conn = get_db_connection(MAIN_DB)
    try:
        cursor = conn.cursor()
        existing = cursor.execute(
            'SELECT id FROM SecuritySettings WHERE setting_name = ?',
            (name,),
        ).fetchone()
        if existing:
            cursor.execute(
                '''
                UPDATE SecuritySettings
                SET setting_value = ?, description = COALESCE(?, description), updated_by = ?, updated_date = CURRENT_TIMESTAMP
                WHERE id = ?
                ''',
                (str(value), description, updated_by, existing[0]),
            )
        else:
            cursor.execute(
                '''
                INSERT INTO SecuritySettings (setting_name, setting_value, description, updated_by, updated_date)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''',
                (name, str(value), description, updated_by),
            )
        conn.commit()
    finally:
        conn.close()
