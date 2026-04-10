"""Librarian Routes for SPEAK2DB"""
import logging
import sqlite3
from datetime import datetime, timedelta
from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from utils.rbac import role_required
from db.connection import get_db_connection, MAIN_DB

logger = logging.getLogger(__name__)

librarian_bp = Blueprint('librarian', __name__, url_prefix='/librarian')


@librarian_bp.route('/query', methods=['GET', 'POST'])
@role_required('Librarian')
def query_console():
    """Librarian query console - natural language to SQL"""
    from admin_data_functions import add_log
    from ollama_sql import generate_sql
    
    # Log access to librarian query console
    add_log(session.get('user_id'), 'Accessed librarian query console')
    
    if request.method == 'POST':
        # Handle natural language query
        user_query = request.form.get('query', '').strip()
        
        if not user_query:
            flash('Please enter a query to execute.', 'error')
            return render_template('librarian/query.html', role=session.get('role'))
        
        # Generate SQL from natural language using existing function
        try:
            sql_query = generate_sql(user_query)
            
            if not sql_query or not sql_query.strip():
                flash('Unable to generate SQL from your query. Please try rephrasing.', 'error')
                return render_template('librarian/query.html', role=session.get('role'))
            
            # Execute the generated SQL safely
            conn = get_db_connection(MAIN_DB)
            try:
                results = conn.execute(sql_query).fetchall()
                results_list = [dict(row) for row in results]
                add_log(session.get('user_id'), f'Executed query: {user_query[:100]}...')
                flash(f'Query executed successfully. {len(results_list)} rows returned.', 'success')
                return render_template('librarian/query.html', 
                                 role=session.get('role'), 
                                 query=user_query, 
                                 sql=sql_query,
                                 results=results_list)
            except Exception as e:
                error_msg = f'Database error: {str(e)}'
                flash(error_msg, 'error')
                add_log(session.get('user_id'), f'Query error: {str(e)[:100]}')
                return render_template('librarian/query.html', 
                                 role=session.get('role'), 
                                 query=user_query, 
                                 sql=sql_query)
            finally:
                conn.close()
                
        except Exception as e:
            error_msg = f'Error generating SQL: {str(e)}'
            flash(error_msg, 'error')
            add_log(session.get('user_id'), f'SQL generation error: {str(e)[:100]}')
            return render_template('librarian/query.html', role=session.get('role'))
    
    # GET request - just show the console
    return render_template('librarian/query.html', role=session.get('role'))


@librarian_bp.route('/')
@role_required('Librarian')
def librarian_dashboard():
    """Librarian dashboard"""
    from admin_data_functions import add_log
    
    # Log access to librarian dashboard
    add_log(session.get('user_id'), 'Accessed librarian dashboard')
    
    # Get dashboard statistics
    conn = get_db_connection(MAIN_DB)
    try:
        # Books statistics
        total_books = conn.execute('SELECT COUNT(*) FROM Books').fetchone()[0]
        total_students = conn.execute('SELECT COUNT(*) FROM Students').fetchone()[0]
        issued_books = conn.execute('SELECT COUNT(*) FROM Issued WHERE return_date IS NULL').fetchone()[0]
        overdue_books = conn.execute(
            'SELECT COUNT(*) FROM Issued WHERE return_date IS NULL AND date("now") > due_date'
        ).fetchone()[0]
        
        # Available books calculation (sum of available copies)
        available_books = conn.execute('SELECT SUM(available_copies) FROM Books').fetchone()[0] or 0
        
        # Fines statistics
        total_fines = conn.execute('SELECT COUNT(*) FROM Fines').fetchone()[0]
        unpaid_fines = conn.execute('SELECT COUNT(*) FROM Fines WHERE status = "Unpaid"').fetchone()[0]
        total_unpaid_amount = conn.execute('SELECT SUM(fine_amount) FROM Fines WHERE status = "Unpaid"').fetchone()[0] or 0
        
        # Recent activity
        recent_issues = conn.execute('''
            SELECT COUNT(*) FROM Issued 
            WHERE date(issue_date) = date('now')
        ''').fetchone()[0]
        
        recent_returns = conn.execute('''
            SELECT COUNT(*) FROM Issued 
            WHERE date(return_date) = date('now')
        ''').fetchone()[0]
        
        recent_payments = conn.execute('''
            SELECT COUNT(*) FROM Fines 
            WHERE status = 'Paid'
        ''').fetchone()[0]
        
        dashboard_stats = {
            'total_books': total_books,
            'total_students': total_students,
            'issued_books': issued_books,
            'overdue_books': overdue_books,
            'available_books': available_books,
            'total_fines': total_fines,
            'unpaid_fines': unpaid_fines,
            'total_unpaid_amount': total_unpaid_amount,
            'recent_issues': recent_issues,
            'recent_returns': recent_returns,
            'recent_payments': recent_payments
        }
        
        return render_template('librarian/dashboard.html', 
                             role=session.get('role'), 
                             stats=dashboard_stats)
    except Exception as e:
        logger.error(f"Error getting librarian stats: {e}")
        return render_template('librarian/dashboard.html', 
                          role=session.get('role'), 
                          stats={})
    finally:
        conn.close()


def register_librarian_routes(app):
    """Register librarian routes on the Flask app."""
    app.register_blueprint(librarian_bp)


# Placeholder routes for dashboard functionality
@librarian_bp.route('/issue-book', methods=['GET', 'POST'])
@role_required('Librarian')
def issue_book():
    """Issue book to student"""
    from admin_data_functions import add_log
    from datetime import datetime
    
    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip()
        book_id = request.form.get('book_id', '').strip()
        
        if not student_id or not book_id:
            flash('Both Student ID and Book ID are required.', 'error')
            return render_template('librarian/issue_book.html', role=session.get('role'))
        
        conn = get_db_connection(MAIN_DB)
        try:
            # Check if student exists
            student = conn.execute('SELECT id, name FROM Students WHERE id = ?', (student_id,)).fetchone()
            if not student:
                flash('Student not found.', 'error')
                return render_template('librarian/issue_book.html', role=session.get('role'))
            
            # Check if book exists and is available
            book = conn.execute('SELECT id, title, author FROM Books WHERE id = ?', (book_id,)).fetchone()
            if not book:
                flash('Book not found.', 'error')
                return render_template('librarian/issue_book.html', role=session.get('role'))
            
            # Check if book is already issued
            existing_issue = conn.execute(
                'SELECT id FROM Issued WHERE book_id = ? AND return_date IS NULL',
                (book_id,)
            ).fetchone()
            
            if existing_issue:
                flash('Book is already issued.', 'error')
                return render_template('librarian/issue_book.html', role=session.get('role'))
            
            # Issue the book
            issue_date = datetime.now().strftime('%Y-%m-%d')
            due_date = datetime.now().replace(day=datetime.now().day + 14).strftime('%Y-%m-%d')  # 14 days from now
            
            conn.execute(
                '''INSERT INTO Issued (student_id, book_id, issue_date, due_date)
                   VALUES (?, ?, ?, ?)''',
                (student_id, book_id, issue_date, due_date)
            )
            conn.commit()
            
            add_log(session.get('user_id'), f'Issued book {book_id} to student {student_id}')
            flash(f'Book "{book["title"]}" issued successfully to {student["name"]}. Due date: {due_date}', 'success')
            
            return redirect(url_for('librarian.issue_book'))
            
        except sqlite3.Error as e:
            flash(f'Database error: {str(e)}', 'error')
            add_log(session.get('user_id'), f'Issue book error: {str(e)}')
            return render_template('librarian/issue_book.html', role=session.get('role'))
        finally:
            conn.close()
    
    # GET request - show the form
    return render_template('librarian/issue_book.html', role=session.get('role'))


@librarian_bp.route('/return-book', methods=['GET', 'POST'])
@role_required('Librarian')
def return_book():
    """Return issued book"""
    from admin_data_functions import add_log
    from datetime import datetime
    
    if request.method == 'POST':
        book_id = request.form.get('book_id', '').strip()
        student_roll = request.form.get('student_roll', '').strip()
        student_department = request.form.get('student_department', '').strip()
        
        if not book_id:
            flash('Book ID is required.', 'error')
            return render_template('librarian/return_book.html', role=session.get('role'))
        
        conn = get_db_connection(MAIN_DB)
        try:
            # Check if book is currently issued
            issued_book = conn.execute(
                '''SELECT i.id, i.student_id, i.issue_date, i.due_date, b.title, s.name as student_name,
                       s.roll_number
                   FROM Issued i
                   JOIN Books b ON i.book_id = b.id
                   JOIN Students s ON i.student_id = s.id
                   WHERE i.book_id = ? AND i.return_date IS NULL''',
                (book_id,)
            ).fetchone()
            
            if not issued_book:
                flash('This book is not currently issued or does not exist.', 'error')
                return render_template('librarian/return_book.html', role=session.get('role'))
            
            # Return the book
            return_date = datetime.now().strftime('%Y-%m-%d')
            
            conn.execute(
                'UPDATE Issued SET return_date = ? WHERE id = ?',
                (return_date, issued_book['id'])
            )
            conn.commit()
            
            add_log(session.get('user_id'), f'Returned book {book_id} by student {issued_book["student_name"]} (Roll: {issued_book["roll_number"]})')
            flash(f'Book "{issued_book["title"]}" returned successfully by {issued_book["student_name"]} (Roll: {issued_book["roll_number"]}).', 'success')
            
            return redirect(url_for('librarian.return_book'))
            
        except sqlite3.Error as e:
            flash(f'Database error: {str(e)}', 'error')
            add_log(session.get('user_id'), f'Return book error: {str(e)}')
            return render_template('librarian/return_book.html', role=session.get('role'))
        finally:
            conn.close()
    
    # GET request - show form
    return render_template('librarian/return_book.html', role=session.get('role'), current_date=datetime.now().strftime('%Y-%m-%d'))


@librarian_bp.route('/manage-books')
@role_required('Librarian')
def manage_books():
    """Manage books - full CRUD functionality"""
    from admin_data_functions import add_log, get_all_books
    
    # Log access to manage books page
    add_log(session.get('user_id'), 'Accessed manage books page')
    
    # Get all books
    books = get_all_books()
    
    return render_template('librarian/manage_books.html', 
                      role=session.get('role'), 
                      books=books)

@librarian_bp.route('/add-book', methods=['POST'])
@role_required('Librarian')
def add_book_route():
    """Add a new book"""
    from admin_data_functions import add_book, add_log
    
    title = request.form.get('title', '').strip()
    author = request.form.get('author', '').strip()
    category = request.form.get('category', '').strip()
    quantity = request.form.get('quantity', '').strip()
    
    if not title or not author or not category or not quantity:
        flash('All fields are required.', 'error')
    else:
        try:
            quantity = int(quantity)
            if quantity <= 0:
                flash('Quantity must be a positive number.', 'error')
            else:
                if add_book(title, author, category, quantity):
                    add_log(session.get('user_id'), f'Added book: {title} by {author} ({category})')
                    flash(f'Book "{title}" added successfully!', 'success')
                else:
                    flash('Failed to add book. Please try again.', 'error')
        except ValueError:
            flash('Quantity must be a valid number.', 'error')
    
    return redirect(url_for('librarian.manage_books'))

@librarian_bp.route('/delete-book/<int:book_id>')
@role_required('Librarian')
def delete_book_route(book_id):
    """Delete a book"""
    from admin_data_functions import delete_book, add_log
    
    # Get book details for logging
    conn = get_db_connection(MAIN_DB)
    try:
        book = conn.execute("SELECT title, author FROM Books WHERE id = ?", (book_id,)).fetchone()
        if book:
            if delete_book(book_id):
                add_log(session.get('user_id'), f'Deleted book: {book["title"]} by {book["author"]}')
                flash(f'Book "{book["title"]}" deleted successfully!', 'success')
            else:
                flash('Failed to delete book. Please try again.', 'error')
        else:
            flash('Book not found.', 'error')
    except sqlite3.Error as e:
        flash('Database error occurred.', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('librarian.manage_books'))


@librarian_bp.route('/manage-fines')
@role_required('Librarian')
def manage_fines():
    """Manage fines - view and process payments"""
    from admin_data_functions import add_log
    
    # Log access to manage fines page
    add_log(session.get('user_id'), 'Accessed manage fines page')
    
    conn = get_db_connection(MAIN_DB)
    try:
        # Get unpaid fines with student and book information
        unpaid_fines = conn.execute('''
            SELECT f.id, f.fine_amount, f.issue_date, f.status,
                   s.id as student_id, s.name as student_name, s.roll_number,
                   b.id as book_id, b.title as book_title
            FROM Fines f
            JOIN Students s ON f.student_id = s.id
            LEFT JOIN Issued i ON f.student_id = i.student_id AND i.return_date IS NOT NULL
            LEFT JOIN Books b ON i.book_id = b.id
            WHERE f.status = 'Unpaid'
            ORDER BY f.issue_date DESC
        ''').fetchall()
        
        # Get payment statistics
        total_unpaid = conn.execute('''
            SELECT COUNT(*) as count, SUM(fine_amount) as total
            FROM Fines WHERE status = 'Unpaid'
        ''').fetchone()
        
        return render_template('librarian/manage_fines.html', 
                             role=session.get('role'), 
                             unpaid_fines=unpaid_fines,
                             stats=total_unpaid)
    except Exception as e:
        logger.error(f"Error getting fines data: {e}")
        return render_template('librarian/manage_fines.html', 
                          role=session.get('role'), 
                          unpaid_fines=[],
                          stats={'count': 0, 'total': 0})
    finally:
        conn.close()


@librarian_bp.route('/pay-fine/<int:fine_id>', methods=['POST'])
@role_required('Librarian')
def pay_fine(fine_id):
    """Mark a fine as paid"""
    from admin_data_functions import add_log
    from datetime import datetime
    
    payment_method = request.form.get('payment_method', 'Cash')
    
    conn = get_db_connection(MAIN_DB)
    try:
        # Check if fine exists and is unpaid
        fine = conn.execute('''
            SELECT f.id, f.fine_amount, f.status,
                   s.id as student_id, s.name as student_name, s.roll_number,
                   b.id as book_id, b.title as book_title
            FROM Fines f
            JOIN Students s ON f.student_id = s.id
            LEFT JOIN Issued i ON f.student_id = i.student_id AND i.return_date IS NOT NULL
            LEFT JOIN Books b ON i.book_id = b.id
            WHERE f.id = ? AND f.status = 'Unpaid'
        ''', (fine_id,)).fetchone()
        
        if not fine:
            flash('Fine not found or already paid.', 'error')
            return redirect(url_for('librarian.manage_fines'))
        
        # Update fine status
        payment_date = datetime.now().strftime('%Y-%m-%d')
        conn.execute('''
            UPDATE Fines 
            SET status = 'Paid', payment_date = ?, payment_method = ?
            WHERE id = ?
        ''', (payment_date, payment_method, fine_id))
        conn.commit()
        
        add_log(session.get('user_id'), 
                f'Paid fine {fine_id} for student {fine["student_name"]} (Roll: {fine["roll_number"]}) - Amount: ${fine["fine_amount"]}')
        flash(f'Fine of ${fine["fine_amount"]} paid successfully for {fine["student_name"]} via {payment_method}.', 'success')
        
    except sqlite3.Error as e:
        flash(f'Database error: {str(e)}', 'error')
        add_log(session.get('user_id'), f'Pay fine error: {str(e)}')
    finally:
        conn.close()
    
    return redirect(url_for('librarian.manage_fines'))


@librarian_bp.route('/pay-all-fines', methods=['POST'])
@role_required('Librarian')
def pay_all_fines():
    """Mark all unpaid fines as paid"""
    from admin_data_functions import add_log
    from datetime import datetime
    
    payment_method = request.form.get('payment_method', 'Cash')
    
    conn = get_db_connection(MAIN_DB)
    try:
        # Get count of unpaid fines
        unpaid_count = conn.execute('SELECT COUNT(*) FROM Fines WHERE status = "Unpaid"').fetchone()[0]
        
        if unpaid_count == 0:
            flash('No unpaid fines to process.', 'info')
            return redirect(url_for('librarian.manage_fines'))
        
        # Update all unpaid fines
        payment_date = datetime.now().strftime('%Y-%m-%d')
        conn.execute('''
            UPDATE Fines 
            SET status = 'Paid', payment_date = ?, payment_method = ?
            WHERE status = 'Unpaid'
        ''', (payment_date, payment_method))
        conn.commit()
        
        add_log(session.get('user_id'), 
                f'Paid all {unpaid_count} unpaid fines via {payment_method}')
        flash(f'Successfully marked {unpaid_count} fines as paid via {payment_method}.', 'success')
        
    except sqlite3.Error as e:
        flash(f'Database error: {str(e)}', 'error')
        add_log(session.get('user_id'), f'Pay all fines error: {str(e)}')
    finally:
        conn.close()
    
    return redirect(url_for('librarian.manage_fines'))


@librarian_bp.route('/student-fines/<int:student_id>')
@role_required('Librarian')
def student_fines(student_id):
    """View fines for a specific student"""
    from admin_data_functions import add_log
    
    conn = get_db_connection(MAIN_DB)
    try:
        # Get student information
        student = conn.execute('''
            SELECT id, name, roll_number, email, branch
            FROM Students WHERE id = ?
        ''', (student_id,)).fetchone()
        
        if not student:
            flash('Student not found.', 'error')
            return redirect(url_for('librarian.manage_fines'))
        
        # Get all fines for this student
        fines = conn.execute('''
            SELECT f.id, f.fine_amount, f.issue_date, f.status, 
                   f.payment_date, f.payment_method,
                   b.title as book_title
            FROM Fines f
            LEFT JOIN Issued i ON f.issued_id = i.id
            LEFT JOIN Books b ON i.book_id = b.id
            WHERE f.student_id = ?
            ORDER BY f.issue_date DESC
        ''', (student_id,)).fetchall()
        
        # Calculate totals
        total_unpaid = sum(f['fine_amount'] for f in fines if f['status'] == 'Unpaid')
        total_paid = sum(f['fine_amount'] for f in fines if f['status'] == 'Paid')
        
        add_log(session.get('user_id'), f'Viewed fines for student {student["name"]} (Roll: {student["roll_number"]})')
        
        return render_template('librarian/student_fines.html', 
                             role=session.get('role'),
                             student=student,
                             fines=fines,
                             total_unpaid=total_unpaid,
                             total_paid=total_paid)
        
    except Exception as e:
        logger.error(f"Error getting student fines: {e}")
        flash('Error retrieving student fines.', 'error')
        return redirect(url_for('librarian.manage_fines'))
    finally:
        conn.close()
