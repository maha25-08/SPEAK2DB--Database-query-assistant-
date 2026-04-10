"""
Centralized Role-Based Access Control (RBAC) utility for SPEAK2DB.

Provides reusable helpers that can be imported and applied across all routes:

    from utils.rbac import check_role, login_required, role_required
"""
from functools import wraps

from flask import redirect, request, session, url_for


def check_role(required_roles) -> bool:
    """Return True if the current session role is in *required_roles*.

    The session role is stored under the ``"role"`` key (e.g. ``"Administrator"``,
    ``"Librarian"``, ``"Faculty"``, ``"Student"``).
    """
    # Handle tuple/list flattening and normalize to lowercase
    flattened_roles = []
    if isinstance(required_roles, tuple):
        # If it's a tuple like (['Librarian'],), flatten it
        for item in required_roles:
            if isinstance(item, (list, tuple)):
                flattened_roles.extend(item)
            else:
                flattened_roles.append(item)
    else:
        flattened_roles = list(required_roles) if isinstance(required_roles, (list, tuple)) else [required_roles]
    
    # Normalize all roles to lowercase for comparison
    normalized_roles = [role.lower() for role in flattened_roles if role]
    current_role = session.get("role", "").lower()
    
    return current_role in normalized_roles


def login_required(f=None):
    """Redirect to /login when no user session is active.

    Can be used as a plain decorator::

        @login_required
        def my_view(): ...

    or called directly to check and return a redirect when needed::

        redir = login_required()
        if redir:
            return redir
    """
    # Called without arguments – acts as a decorator factory or plain check.
    if f is None:
        if "user_id" not in session:
            return redirect(url_for("login"))
        return None

    @wraps(f)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return wrapped


def role_required(*required_roles):
    """Decorator that combines login check with role authorisation.

    Redirects unauthenticated users to /login.
    Returns ``("Unauthorized", 403)`` when the authenticated user does not
    hold one of the *required_roles*.

    Usage::

        @role_required("Administrator")
        def admin_only_view(): ...

        @role_required("Administrator", "Librarian")
        def staff_view(): ...
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            
            if not check_role(required_roles):
                return "Unauthorized", 403
            return f(*args, **kwargs)

        return wrapped

    return decorator
