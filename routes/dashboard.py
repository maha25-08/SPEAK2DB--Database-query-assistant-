"""
Dashboard routes for SPEAK2DB.

Canonical URL scheme (snake_case):
  /student_dashboard      – student personal dashboard
  /faculty_dashboard      – faculty view
  /librarian_dashboard    – librarian view
  /admin_dashboard        – administrator view

Kebab-case aliases redirect to the canonical form for backward compatibility.
"""
import logging
import jinja2
from flask import Blueprint, current_app, render_template, session, redirect, url_for

from db.connection import get_db_connection, MAIN_DB
from utils.decorators import require_roles
from utils.helpers import get_library_stats
from utils.rbac import role_required

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint("dashboard", __name__)


# ---------------------------------------------------------------------------
# Student dashboard (canonical)
# ---------------------------------------------------------------------------

@dashboard_bp.route("/student_dashboard")
@role_required("Student")
def student_dashboard():
    """Student dashboard (canonical snake_case route)."""
    user_role = session.get("role", "Student")
    user_id = session["user_id"]
    student_id = session.get("student_id")

    try:
        conn = get_db_connection(MAIN_DB)
        student_info = conn.execute(
            "SELECT * FROM Students WHERE id = ?", (student_id,)
        ).fetchone()
        current_books = conn.execute(
            """SELECT i.*, b.title, b.author FROM Issued i
               JOIN Books b ON i.book_id = b.id
               WHERE i.student_id = ? AND i.return_date IS NULL
               ORDER BY i.due_date ASC""",
            (student_id,),
        ).fetchall()
        overdue_books = conn.execute(
            """SELECT i.*, b.title, b.author FROM Issued i
               JOIN Books b ON i.book_id = b.id
               WHERE i.student_id = ? AND i.return_date IS NULL
               AND i.due_date < date('now')
               ORDER BY i.due_date ASC""",
            (student_id,),
        ).fetchall()
        borrowing_history = conn.execute(
            """SELECT i.*, b.title, b.author FROM Issued i
               JOIN Books b ON i.book_id = b.id
               WHERE i.student_id = ? ORDER BY i.issue_date DESC""",
            (student_id,),
        ).fetchall()
        unpaid_fines = conn.execute(
            "SELECT f.id AS fine_id, f.student_id, f.fine_amount, f.fine_type, f.status, f.issue_date FROM Fines f WHERE f.student_id = ? AND f.status = 'Unpaid' ORDER BY f.issue_date DESC",
            (student_id,),
        ).fetchall()
        all_fines = conn.execute(
            "SELECT f.id AS fine_id, f.student_id, f.fine_amount, f.fine_type, f.status, f.issue_date FROM Fines f WHERE f.student_id = ? ORDER BY f.issue_date DESC",
            (student_id,),
        ).fetchall()
        reservations = conn.execute(
            """SELECT r.*, b.title, b.author FROM Reservations r
               JOIN Books b ON r.book_id = b.id
               WHERE r.student_id = ? ORDER BY r.reservation_date DESC""",
            (student_id,),
        ).fetchall()
        conn.close()
        stats = {
            "total_borrowed": len(borrowing_history),
            "current_borrowed": len(current_books),
            "total_fines": len(all_fines),
            "unpaid_fines": len(unpaid_fines),
            "pending_requests": len(reservations),
        }
    except Exception as exc:
        logger.error("student_dashboard DB error: %s", exc)
        student_info = None
        current_books = overdue_books = borrowing_history = []
        unpaid_fines = all_fines = reservations = []
        stats = {}

    return render_template(
        "student_dashboard.html",
        student_info=student_info,
        borrowing_history=borrowing_history,
        current_books=current_books,
        overdue_books=overdue_books,
        unpaid_fines=unpaid_fines,
        reservations=reservations,
        stats=stats,
        role=user_role,
        user=user_id,
    )


# ---------------------------------------------------------------------------
# Kebab-case aliases → redirect to canonical routes
# ---------------------------------------------------------------------------

@dashboard_bp.route("/student-dashboard")
def student_dashboard_kebab():
    """Redirect legacy kebab-case URL to canonical student dashboard."""
    return redirect(url_for("dashboard.student_dashboard"), code=301)


@dashboard_bp.route("/student/dashboard")
def student_dashboard_alt():
    """Redirect legacy alternative URL to canonical student dashboard."""
    return redirect(url_for("dashboard.student_dashboard"), code=301)


@dashboard_bp.route("/student-dashboard-individual")
@require_roles("Student")
def student_dashboard_individual():
    """Individual per-student template (roll-number-specific HTML file)."""
    roll_number = session.get("user_id")
    if not roll_number:
        return redirect(url_for("login"))

    template_name = f"student_dashboard_{roll_number.lower()}.html"
    try:
        return render_template(template_name)
    except jinja2.TemplateNotFound:
        logger.warning("Individual template not found: %s", template_name)
        return redirect(url_for("dashboard.student_dashboard"))


# ---------------------------------------------------------------------------
# Faculty dashboard
# ---------------------------------------------------------------------------

@dashboard_bp.route("/faculty_dashboard")
@require_roles("Faculty", "Librarian", "Administrator")
def faculty_dashboard():
    """Faculty dashboard – Faculty, Librarian, and Administrator roles."""
    role = session.get("role")
    logger.debug("faculty_dashboard accessed by role: %s", role)

    user_id = session["user_id"]
    faculty_info = None
    recent_issues = []

    try:
        conn = get_db_connection(MAIN_DB)
        faculty_info = conn.execute(
            "SELECT * FROM Faculty WHERE email = ? OR name = ? LIMIT 1",
            (user_id, user_id),
        ).fetchone()
        if faculty_info is None:
            faculty_info = conn.execute("SELECT * FROM Faculty LIMIT 1").fetchone()
        recent_issues = conn.execute(
            """SELECT i.*, b.title, b.author, s.name as student_name
               FROM Issued i
               JOIN Books b ON i.book_id = b.id
               JOIN Students s ON i.student_id = s.id
               ORDER BY i.issue_date DESC LIMIT 10"""
        ).fetchall()
        conn.close()
    except Exception as exc:
        logger.error("faculty_dashboard DB error: %s", exc)

    stats = get_library_stats()

    return render_template(
        "faculty_dashboard.html",
        role=role,
        user=user_id,
        faculty_info=faculty_info,
        stats=stats,
        recent_issues=recent_issues,
    )


# ---------------------------------------------------------------------------
# Librarian dashboard
# ---------------------------------------------------------------------------

_LIBRARIAN_TEMPLATES = {
    "librarian1": "librarian1_dashboard.html",
    "librarian2": "librarian2_dashboard.html",
    "librarian3": "librarian3_dashboard.html",
}


@dashboard_bp.route("/librarian_dashboard")
@require_roles("Librarian", "Administrator")
def librarian_dashboard():
    """Librarian dashboard."""
    role = session.get("role")
    logger.debug("librarian_dashboard accessed by role: %s", role)

    user_id = session["user_id"]
    recent_issues = []

    try:
        conn = get_db_connection(MAIN_DB)
        recent_issues = conn.execute(
            """SELECT i.*, b.title, b.author, s.name as student_name
               FROM Issued i
               JOIN Books b ON i.book_id = b.id
               JOIN Students s ON i.student_id = s.id
               ORDER BY i.issue_date DESC LIMIT 5"""
        ).fetchall()
        conn.close()
    except Exception as exc:
        logger.error("librarian_dashboard DB error: %s", exc)

    stats = get_library_stats()

    return render_template(
        "librarian/dashboard.html",
        active_page='dashboard',
        role=role,
        user=user_id,
        stats=stats,
        recent_issues=recent_issues,
    )


# ---------------------------------------------------------------------------
# Admin dashboard
# ---------------------------------------------------------------------------

@dashboard_bp.route("/admin_dashboard")
@role_required("Administrator")
def admin_dashboard():
    """Administrator dashboard."""
    # Import the new function and logging
    from admin_data_functions import get_dashboard_data, add_log
    
    # Log access to dashboard
    add_log(session.get('user_id'), 'Accessed admin dashboard')
    
    # Get only dashboard data
    dashboard_data = get_dashboard_data()
    
    return render_template("admin/dashboard.html", role=session.get('role'), dashboard=dashboard_data)
