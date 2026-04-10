"""
Enhanced Student Query Processing for Librarian Console
Handles comprehensive individual student queries with proper SQL generation.
"""

import sqlite3
import re
from typing import Dict, List, Optional, Tuple
from db.connection import get_db_connection, MAIN_DB

class EnhancedStudentQueries:
    """Advanced student query processing with comprehensive patterns."""
    
    def __init__(self):
        self.student_query_patterns = self._load_student_query_patterns()
        self.student_entity_extractors = self._load_student_extractors()
    
    def _load_student_query_patterns(self) -> Dict:
        """Load comprehensive student query patterns."""
        return {
            # Book-related queries
            'books_borrowed': {
                'keywords': ['borrowed', 'issued', 'taken', 'checked out', 'loaned', 'has', 'currently has'],
                'patterns': [
                    r'books?\s+(?:borrowed|issued|taken|checked out|loaned|has|currently has)\s+by\s+([a-z0-9]+)',
                    r'student\s+([a-z0-9]+)\s+(?:has|currently has)\s+(?:books?|any\s+books?)',
                    r'what\s+books?\s+(?:does|is)\s+student\s+([a-z0-9]+)\s+(?:have|has|borrowed|issued)',
                    r'show\s+books?\s+(?:borrowed|issued|taken|checked out)\s+by\s+([a-z0-9]+)',
                    r'([a-z0-9]+)[\'s]?\s+(?:borrowed|issued|taken|checked out)\s+books?',
                    r'([a-z0-9]+)\s+(?:has|holds|owns)\s+(?:books?|any\s+books?)',
                    r'books?\s+(?:with|for)\s+student\s+([a-z0-9]+)',
                    r'student\s+([a-z0-9]+)[\'s]?\s+(?:borrowing|issuing|reading)'
                ],
                'sql_template': '''
                    SELECT DISTINCT b.id, b.title, b.author, b.category, b.price,
                           i.issue_date, i.due_date, i.return_date,
                           CASE 
                               WHEN i.return_date IS NULL THEN 'Currently Issued'
                               WHEN julianday(i.return_date) > julianday(i.due_date) THEN 'Returned Late'
                               ELSE 'Returned On Time'
                           END as status
                    FROM Books b
                    JOIN Issued i ON b.id = i.book_id
                    JOIN Students s ON i.student_id = s.id
                    WHERE s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?)
                    ORDER BY i.issue_date DESC
                '''
            },
            
            'books_by_title': {
                'keywords': ['title', 'titled', 'called', 'named', 'book name', 'search'],
                'patterns': [
                    r'books?\s+(?:titled|called|named)\s+["\']?([^"\']+)["\']?\s+(?:for|by)\s+([a-z0-9]+)',
                    r'student\s+([a-z0-9]+)\s+(?:borrowed|has|issued)\s+["\']?([^"\']+)["\']?',
                    r'["\']([^"\']+)["\']?\s+(?:borrowed|issued|taken)\s+by\s+([a-z0-9]+)',
                    r'show\s+["\']?([^"\']+)["\']?\s+(?:for|by)\s+([a-z0-9]+)',
                    r'([a-z0-9]+)\s+(?:wants|needs|looking\s+for)\s+["\']?([^"\']+)["\']?',
                    r'find\s+["\']?([^"\']+)["\']?\s+(?:for|by)\s+([a-z0-9]+)'
                ],
                'sql_template': '''
                    SELECT DISTINCT b.id, b.title, b.author, b.category, b.price,
                           i.issue_date, i.due_date, i.return_date,
                           CASE 
                               WHEN i.return_date IS NULL THEN 'Currently Issued'
                               ELSE 'Returned'
                           END as status
                    FROM Books b
                    LEFT JOIN Issued i ON b.id = i.book_id AND i.student_id = (
                        SELECT id FROM Students WHERE roll_number = ? OR id = ? OR LOWER(name) LIKE LOWER(?)
                    )
                    WHERE b.title LIKE ? OR b.title LIKE ? OR b.title LIKE ?
                    ORDER BY i.issue_date DESC
                '''
            },
            
            'books_by_author': {
                'keywords': ['author', 'written by', 'by', 'wrote', 'authored'],
                'patterns': [
                    r'books?\s+(?:by|written\s+by|authored\s+by)\s+["\']?([^"\']+)["\']?\s+(?:for|by)\s+([a-z0-9]+)',
                    r'student\s+([a-z0-9]+)\s+(?:borrowed|has|issued)\s+(?:books\s+by|books\s+from)\s+["\']?([^"\']+)["\']?',
                    r'["\']([^"\']+)["\']?\s+(?:books?|works)\s+(?:for|by)\s+([a-z0-9]+)',
                    r'show\s+(?:books?|works)\s+(?:by|from)\s+["\']?([^"\']+)["\']?\s+(?:for|by)\s+([a-z0-9]+)',
                    r'([a-z0-9]+)\s+(?:likes|reads|prefers)\s+(?:books?|works)\s+(?:by|from)\s+["\']?([^"\']+)["\']?',
                    r'find\s+(?:books?|works)\s+(?:by|from)\s+["\']?([^"\']+)["\']?\s+(?:for|by)\s+([a-z0-9]+)'
                ],
                'sql_template': '''
                    SELECT DISTINCT b.id, b.title, b.author, b.category, b.price,
                           i.issue_date, i.due_date, i.return_date,
                           CASE 
                               WHEN i.return_date IS NULL THEN 'Currently Issued'
                               ELSE 'Returned'
                           END as status
                    FROM Books b
                    LEFT JOIN Issued i ON b.id = i.book_id AND i.student_id = (
                        SELECT id FROM Students WHERE roll_number = ? OR id = ? OR LOWER(name) LIKE LOWER(?)
                    )
                    WHERE b.author LIKE ? OR b.author LIKE ? OR b.author LIKE ?
                    ORDER BY i.issue_date DESC
                '''
            },
            
            'books_by_category': {
                'keywords': ['category', 'genre', 'type', 'section', 'classification'],
                'patterns': [
                    r'books?\s+(?:in|from)\s+(?:the\s+)?["\']?([^"\']+)["\']?\s+(?:category|genre|type|section)\s+(?:for|by)\s+([a-z0-9]+)',
                    r'student\s+([a-z0-9]+)\s+(?:borrowed|has|issued)\s+(?:books?\s+in|from)\s+["\']?([^"\']+)["\']?',
                    r'["\']([^"\']+)["\']?\s+(?:category|genre|type|section)\s+(?:books?|works)\s+(?:for|by)\s+([a-z0-9]+)',
                    r'show\s+(?:books?|works)\s+(?:in|from)\s+["\']?([^"\']+)["\']?\s+(?:for|by)\s+([a-z0-9]+)',
                    r'([a-z0-9]+)\s+(?:reads|studies|interested\s+in)\s+["\']?([^"\']+)["\']?\s+(?:books?|works)',
                    r'find\s+(?:books?|works)\s+(?:in|from)\s+["\']?([^"\']+)["\']?\s+(?:for|by)\s+([a-z0-9]+)',
                    r'([a-z0-9]+)\s+(?:prefers|likes)\s+(?:["\']?([^"\']+)["\']?|([^"\']+))\s+(?:books?|works)'
                ],
                'sql_template': '''
                    SELECT DISTINCT b.id, b.title, b.author, b.category, b.price,
                           i.issue_date, i.due_date, i.return_date,
                           CASE 
                               WHEN i.return_date IS NULL THEN 'Currently Issued'
                               ELSE 'Returned'
                           END as status
                    FROM Books b
                    LEFT JOIN Issued i ON b.id = i.book_id AND i.student_id = (
                        SELECT id FROM Students WHERE roll_number = ? OR id = ? OR LOWER(name) LIKE LOWER(?)
                    )
                    WHERE b.category LIKE ? OR b.category LIKE ? OR b.category LIKE ?
                    ORDER BY i.issue_date DESC
                '''
            },
            
            'books_by_date_range': {
                'keywords': ['between', 'from', 'to', 'since', 'until', 'after', 'before', 'during', 'last', 'recent'],
                'patterns': [
                    r'books?\s+(?:borrowed|issued|taken)\s+(?:between|from)\s+(\d{4}-\d{2}-\d{2})\s+(?:and|to)\s+(\d{4}-\d{2}-\d{2})\s+(?:by|for)\s+([a-z0-9]+)',
                    r'student\s+([a-z0-9]+)\s+(?:borrowed|issued|took)\s+(?:books?|any\s+books?)\s+(?:between|from)\s+(\d{4}-\d{2}-\d{2})\s+(?:and|to)\s+(\d{4}-\d{2}-\d{2})',
                    r'books?\s+(?:borrowed|issued|taken)\s+(?:since|after)\s+(\d{4}-\d{2}-\d{2})\s+(?:by|for)\s+([a-z0-9]+)',
                    r'student\s+([a-z0-9]+)\s+(?:borrowed|issued|took)\s+(?:books?|any\s+books?)\s+(?:since|after)\s+(\d{4}-\d{2}-\d{2})',
                    r'books?\s+(?:borrowed|issued|taken)\s+(?:until|before)\s+(\d{4}-\d{2}-\d{2})\s+(?:by|for)\s+([a-z0-9]+)',
                    r'student\s+([a-z0-9]+)\s+(?:borrowed|issued|took)\s+(?:books?|any\s+books?)\s+(?:until|before)\s+(\d{4}-\d{2}-\d{2})',
                    r'books?\s+(?:borrowed|issued|taken)\s+(?:in|during)\s+(?:the\s+)?(last|past|recent)\s+(\d+|few|several)\s+(?:days?|weeks?|months?)\s+(?:by|for)\s+([a-z0-9]+)'
                ],
                'sql_template': '''
                    SELECT DISTINCT b.id, b.title, b.author, b.category, b.price,
                           i.issue_date, i.due_date, i.return_date,
                           CASE 
                               WHEN i.return_date IS NULL THEN 'Currently Issued'
                               WHEN julianday(i.return_date) > julianday(i.due_date) THEN 'Returned Late'
                               ELSE 'Returned On Time'
                           END as status
                    FROM Books b
                    JOIN Issued i ON b.id = i.book_id
                    JOIN Students s ON i.student_id = s.id
                    WHERE (s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?))
                      AND i.issue_date BETWEEN ? AND ?
                    ORDER BY i.issue_date DESC
                '''
            },
            
            'books_returned': {
                'keywords': ['returned', 'given back', 'checked in', 'submitted'],
                'patterns': [
                    r'books?\s+(?:returned|given back|checked in|submitted)\s+by\s+([a-z0-9]+)',
                    r'student\s+([a-z0-9]+)\s+(?:returned|given back|checked in)\s+books?',
                    r'what\s+books?\s+(?:did|has)\s+student\s+([a-z0-9]+)\s+(?:return|give back|check in)',
                    r'([a-z0-9]+)[\'s]?\s+(?:returned|given back|checked in)\s+books?'
                ],
                'sql_template': '''
                    SELECT DISTINCT b.id, b.title, b.author, b.category, b.price,
                           i.issue_date, i.due_date, i.return_date,
                           DATEDIFF(i.return_date, i.due_date) as days_late
                    FROM Books b
                    JOIN Issued i ON b.id = i.book_id
                    JOIN Students s ON i.student_id = s.id
                    WHERE s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?)
                      AND i.return_date IS NOT NULL
                    ORDER BY i.return_date DESC
                '''
            },
            
            'overdue_books': {
                'keywords': ['overdue', 'late', 'not returned', 'pending'],
                'patterns': [
                    r'overdue\s+books?\s+(?:for|by)\s+([a-z0-9]+)',
                    r'late\s+books?\s+(?:for|by)\s+([a-z0-9]+)',
                    r'books?\s+(?:not returned|pending)\s+by\s+([a-z0-9]+)',
                    r'student\s+([a-z0-9]+)\s+(?:has|with)\s+(?:overdue|late|pending)\s+books?'
                ],
                'sql_template': '''
                    SELECT DISTINCT b.id, b.title, b.author, b.category, b.price,
                           i.issue_date, i.due_date,
                           (julianday('now') - julianday(i.due_date)) as days_overdue
                    FROM Books b
                    JOIN Issued i ON b.id = i.book_id
                    JOIN Students s ON i.student_id = s.id
                    WHERE (s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?))
                      AND i.return_date IS NULL 
                      AND i.due_date < date('now')
                    ORDER BY i.due_date ASC
                '''
            },
            
            # Fine-related queries
            'fines_unpaid': {
                'keywords': ['unpaid', 'pending', 'due', 'outstanding', 'owe'],
                'patterns': [
                    r'unpaid\s+fines?\s+(?:for|by)\s+([a-z0-9]+)',
                    r'fines?\s+(?:unpaid|pending|due|outstanding)\s+(?:for|by)\s+([a-z0-9]+)',
                    r'how\s+much\s+(?:does|is)\s+student\s+([a-z0-9]+)\s+owe',
                    r'student\s+([a-z0-9]+)\s+(?:owes|has)\s+(?:unpaid\s+)?fines?',
                    r'student\s+([a-z0-9]+)[\'s]?\s+(?:unpaid|pending|due|outstanding)\s+fines?',
                    r'show\s+(?:unpaid|pending|due|outstanding)\s+fines?\s+(?:for|by)\s+([a-z0-9]+)',
                    r'([a-z0-9]+)\s+(?:has|owes)\s+(?:unpaid\s+)?fines?',
                    r'([a-z0-9]+)\s+(?:needs|must)\s+(?:pay|clear)\s+(?:unpaid\s+)?fines?'
                ],
                'sql_template': '''
                    SELECT f.id, f.fine_amount, f.fine_type, f.issue_date, f.status,
                           s.roll_number, s.name, s.branch, s.year,
                           f.fine_amount as amount_due
                    FROM Fines f
                    JOIN Students s ON f.student_id = s.id
                    WHERE (s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?))
                      AND f.status = 'Unpaid'
                    ORDER BY f.issue_date DESC
                '''
            },
            
            'fines_by_amount': {
                'keywords': ['amount', 'over', 'under', 'more than', 'less than', 'exactly'],
                'patterns': [
                    r'fines?\s+(?:over|more\s+than|greater\s+than)\s+\$(\d+(?:\.\d{2})?)\s+(?:for|by)\s+([a-z0-9]+)',
                    r'student\s+([a-z0-9]+)\s+(?:owes|has)\s+(?:fines\s+over|fines\s+greater\s+than)\s+\$(\d+(?:\.\d{2})?)',
                    r'fines?\s+(?:under|less\s+than)\s+\$(\d+(?:\.\d{2})?)\s+(?:for|by)\s+([a-z0-9]+)',
                    r'student\s+([a-z0-9]+)\s+(?:owes|has)\s+(?:fines\s+under|fines\s+less\s+than)\s+\$(\d+(?:\.\d{2})?)',
                    r'fines?\s+(?:exactly|precisely)\s+\$(\d+(?:\.\d{2})?)\s+(?:for|by)\s+([a-z0-9]+)',
                    r'student\s+([a-z0-9]+)\s+(?:owes|has)\s+\$(\d+(?:\.\d{2})?)\s+(?:in\s+)?fines?'
                    r'fines?\s+(?:paid|cleared|settled|resolved)\s+(?:for|by)\s+([a-z0-9]+)',
                    r'how\s+much\s+(?:did|has)\s+student\s+([a-z0-9]+)\s+(?:pay|paid)',
                    r'student\s+([a-z0-9]+)[\'s]?\s+(?:paid|cleared|settled)\s+fines?'
                ],
                'sql_template': '''
                    SELECT f.id, f.fine_amount, f.fine_type, f.issue_date, f.status,
                           s.roll_number, s.name, s.branch, s.year,
                           f.fine_amount as amount_paid
                    FROM Fines f
                    JOIN Students s ON f.student_id = s.id
                    WHERE (s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?))
                      AND f.status = 'Paid'
                    ORDER BY f.issue_date DESC
                '''
            },
            
            'fines_all': {
                'keywords': ['fines', 'penalties', 'charges'],
                'patterns': [
                    r'all\s+fines?\s+(?:for|by)\s+([a-z0-9]+)',
                    r'fines?\s+(?:for|by)\s+([a-z0-9]+)',
                    r'student\s+([a-z0-9]+)[\'s]?\s+fines?',
                    r'what\s+fines?\s+(?:does|is)\s+student\s+([a-z0-9]+)\s+have'
                ],
                'sql_template': '''
                    SELECT f.id, f.fine_amount, f.fine_type, f.issue_date, f.status,
                           s.roll_number, s.name, s.branch, s.year,
                           CASE f.status 
                               WHEN 'Paid' THEN f.fine_amount
                               WHEN 'Unpaid' THEN f.fine_amount
                               ELSE 0 
                           END as amount
                    FROM Fines f
                    JOIN Students s ON f.student_id = s.id
                    WHERE (s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?))
                    ORDER BY f.issue_date DESC
                '''
            },
            
            # Student information queries
            'student_details': {
                'keywords': ['details', 'information', 'info', 'profile', 'about'],
                'patterns': [
                    r'student\s+(?:details|information|info|profile|about)\s+(?:for)?\s*([a-z0-9]+)',
                    r'(?:details|information|info|profile|about)\s+(?:student)?\s*([a-z0-9]+)',
                    r'who\s+is\s+student\s+([a-z0-9]+)',
                    r'tell\s+me\s+about\s+student\s+([a-z0-9]+)'
                ],
                'sql_template': '''
                    SELECT s.id, s.roll_number, s.name, s.branch, s.year, s.email, 
                           s.phone, s.gpa, s.attendance, s.created_date,
                           COUNT(DISTINCT i.id) as total_books_issued,
                           COUNT(DISTINCT CASE WHEN i.return_date IS NULL THEN i.id END) as current_books,
                           COALESCE(SUM(CASE WHEN f.status = 'Unpaid' THEN f.fine_amount ELSE 0 END), 0) as unpaid_fines,
                           COALESCE(SUM(CASE WHEN f.status = 'Paid' THEN f.fine_amount ELSE 0 END), 0) as paid_fines
                    FROM Students s
                    LEFT JOIN Issued i ON s.id = i.student_id
                    LEFT JOIN Fines f ON s.id = f.student_id
                    WHERE (s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?))
                    GROUP BY s.id, s.roll_number, s.name, s.branch, s.year, s.email, s.phone, s.gpa, s.attendance, s.created_date
                '''
            },
            
            'student_activity': {
                'keywords': ['activity', 'history', 'record', 'log'],
                'patterns': [
                    r'student\s+(?:activity|history|record|log)\s+(?:for)?\s*([a-z0-9]+)',
                    r'(?:activity|history|record|log)\s+(?:for)?\s*student\s+([a-z0-9]+)',
                    r'what\s+(?:activity|history|record)s?\s+(?:does|has)\s+student\s+([a-z0-9]+)\s+have'
                ],
                'sql_template': '''
                    SELECT 
                        'Book Issue' as activity_type,
                        i.issue_date as activity_date,
                        b.title as description,
                        CASE WHEN i.return_date IS NULL THEN 'Active' ELSE 'Completed' END as status
                    FROM Issued i
                    JOIN Books b ON i.book_id = b.id
                    JOIN Students s ON i.student_id = s.id
                    WHERE s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?)
                    
                    UNION ALL
                    
                    SELECT 
                        'Fine' as activity_type,
                        f.issue_date as activity_date,
                        f.fine_type || ' - $' || f.fine_amount as description,
                        f.status as status
                    FROM Fines f
                    JOIN Students s ON f.student_id = s.id
                    WHERE s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?)
                    
                    ORDER BY activity_date DESC
                    LIMIT 20
                '''
            },
            
            # Personal query patterns for "my" queries
            'personal_query': {
                'keywords': ['my', 'mine', 'me', 'i have', 'i owe', 'i borrowed'],
                'patterns': [
                    r'my\s+(books?|fines?|borrowed|issued|returned|overdue|unpaid|paid)',
                    r'show\s+my\s+(books?|fines?|borrowed|issued|returned|overdue|unpaid|paid)',
                    r'what\s+(?:are|is)\s+my\s+(books?|fines?|borrowed|issued|returned|overdue|unpaid|paid)',
                    r'i\s+(?:have|borrowed|owe|paid)\s+(?:books?|fines?)',
                    r'mine\s+(books?|fines?|borrowed|issued|returned|overdue|unpaid|paid)'
                ],
                'sql_template': '''
                    SELECT f.id, f.fine_amount, f.fine_type, f.issue_date, f.status,
                           s.roll_number, s.name, s.branch, s.year,
                           f.fine_amount as amount
                    FROM Fines f
                    JOIN Students s ON f.student_id = s.id
                    WHERE s.id = ?
                    ORDER BY f.issue_date DESC
                '''
            },
            
            # Student attendance and academic queries
            'student_attendance': {
                'keywords': ['attendance', 'present', 'absent', 'classes', 'lectures'],
                'patterns': [
                    r'attendance\s+(?:for|of)\s+([a-z0-9]+)',
                    r'([a-z0-9]+)[\'s]?\s+attendance',
                    r'how\s+many\s+classes\s+(?:did|has)\s+([a-z0-9]+)\s+(?:attend|missed)',
                    r'show\s+attendance\s+(?:for|of)\s+([a-z0-9]+)'
                ],
                'sql_template': '''
                    SELECT s.id, s.roll_number, s.name, s.branch, s.year,
                           s.attendance, s.gpa, s.created_date
                    FROM Students s
                    WHERE s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?)
                '''
            },
            
            # Student GPA and academic performance
            'student_gpa': {
                'keywords': ['gpa', 'grade', 'performance', 'academic', 'marks'],
                'patterns': [
                    r'gpa\s+(?:for|of)\s+([a-z0-9]+)',
                    r'([a-z0-9]+)[\'s]?\s+gpa',
                    r'what\s+(?:is|are)\s+([a-z0-9]+)[\'s]?\s+(?:gpa|grades|performance)',
                    r'show\s+(?:gpa|grades|performance)\s+(?:for|of)\s+([a-z0-9]+)'
                ],
                'sql_template': '''
                    SELECT s.id, s.roll_number, s.name, s.branch, s.year,
                           s.gpa, s.attendance, s.created_date
                    FROM Students s
                    WHERE s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?)
                '''
            },
            
            # Student contact information
            'student_contact': {
                'keywords': ['contact', 'email', 'phone', 'address', 'details'],
                'patterns': [
                    r'contact\s+(?:information|details?)\s+(?:for|of)\s+([a-z0-9]+)',
                    r'([a-z0-9]+)[\'s]?\s+(?:contact|email|phone)',
                    r'what\s+is\s+([a-z0-9]+)[\'s]?\s+(?:email|phone|address)',
                    r'show\s+(?:contact|email|phone)\s+(?:for|of)\s+([a-z0-9]+)'
                ],
                'sql_template': '''
                    SELECT s.id, s.roll_number, s.name, s.branch, s.year,
                           s.email, s.phone, s.created_date
                    FROM Students s
                    WHERE s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?)
                '''
            },
            
            # Student branch and year information
            'student_branch': {
                'keywords': ['branch', 'department', 'year', 'semester', 'class', 'major', 'program'],
                'patterns': [
                    r'branch\s+(?:of|for)\s+([a-z0-9]+)',
                    r'([a-z0-9]+)[\'s]?\s+(?:branch|department|year|semester|class|major|program)',
                    r'what\s+(?:branch|department|year|semester|class|major|program)\s+(?:is|are)\s+([a-z0-9]+)\s+(?:in|studying|enrolled)',
                    r'show\s+(?:branch|department|year|semester|class|major|program)\s+(?:for|of)\s+([a-z0-9]+)',
                    r'([a-z0-9]+)\s+(?:studies|is\s+in)\s+(?:the\s+)?["\']?([^"\']+)["\']?\s+(?:branch|department|major)',
                    r'([a-z0-9]+)\s+(?:belongs\s+to|is\s+in)\s+(?:["\']?([^"\']+)["\']?)\s+(?:branch|department|major)',
                    r'([a-z0-9]+)\s+(?:is\s+in\s+)?(?:year|grade)\s+(\d+|[a-z]+)',
                    r'([a-z0-9]+)\s+(?:is\s+in\s+)?(?:semester|term)\s+(\d+|[a-z]+)'
                ],
                'sql_template': '''
                    SELECT s.id, s.roll_number, s.name, s.branch, s.year,
                           s.email, s.created_date
                    FROM Students s
                    WHERE s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?)
                '''
            },
            
            # Student library statistics
            'student_stats': {
                'keywords': ['statistics', 'stats', 'summary', 'total', 'count'],
                'patterns': [
                    r'(?:library|reading)\s+(?:statistics|stats|summary)\s+(?:for|of)\s+([a-z0-9]+)',
                    r'([a-z0-9]+)[\'s]?\s+(?:library|reading)\s+(?:statistics|stats|summary)',
                    r'how\s+many\s+(?:books|fines)\s+(?:does|has)\s+([a-z0-9]+)\s+(?:have|owe)',
                    r'show\s+(?:library|reading)\s+(?:statistics|stats|summary)\s+(?:for|of)\s+([a-z0-9]+)'
                ],
                'sql_template': '''
                    SELECT s.id, s.roll_number, s.name, s.branch, s.year,
                           COUNT(DISTINCT i.id) as total_books_issued,
                           COUNT(DISTINCT CASE WHEN i.return_date IS NULL THEN i.id END) as current_books,
                           COUNT(DISTINCT f.id) as total_fines,
                           COUNT(DISTINCT CASE WHEN f.status = 'Unpaid' THEN f.id END) as unpaid_fines,
                           COALESCE(SUM(CASE WHEN f.status = 'Unpaid' THEN f.fine_amount ELSE 0 END), 0) as unpaid_amount,
                           COALESCE(SUM(f.fine_amount), 0) as total_fine_amount
                    FROM Students s
                    LEFT JOIN Issued i ON s.id = i.student_id
                    LEFT JOIN Fines f ON s.id = f.student_id
                    WHERE s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?)
                    GROUP BY s.id, s.roll_number, s.name, s.branch, s.year
                '''
            },
            
            # Student recent activity
            'student_recent': {
                'keywords': ['recent', 'latest', 'today', 'this week', 'this month'],
                'patterns': [
                    r'recent\s+(?:activity|books|fines)\s+(?:for|of)\s+([a-z0-9]+)',
                    r'([a-z0-9]+)[\'s]?\s+recent\s+(?:activity|books|fines)',
                    r'what\s+(?:did|has)\s+([a-z0-9]+)\s+(?:do|borrow|pay)\s+(?:recently|today)',
                    r'show\s+recent\s+(?:activity|books|fines)\s+(?:for|of)\s+([a-z0-9]+)'
                ],
                'sql_template': '''
                    SELECT 
                        'Book Issue' as activity_type,
                        i.issue_date as activity_date,
                        b.title as description,
                        CASE WHEN i.return_date IS NULL THEN 'Active' ELSE 'Completed' END as status
                    FROM Issued i
                    JOIN Books b ON i.book_id = b.id
                    JOIN Students s ON i.student_id = s.id
                    WHERE (s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?))
                      AND i.issue_date >= date('now', '-30 days')
                    
                    UNION ALL
                    
                    SELECT 
                        'Fine' as activity_type,
                        f.issue_date as activity_date,
                        f.fine_type || ' - $' || f.fine_amount as description,
                        f.status as status
                    FROM Fines f
                    JOIN Students s ON f.student_id = s.id
                    WHERE (s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?))
                      AND f.issue_date >= date('now', '-30 days')
                    
                    ORDER BY activity_date DESC
                    LIMIT 10
                '''
            },
            
            # Student due dates and returns
            'student_duedates': {
                'keywords': ['due', 'return', 'deadline', 'overdue', 'pending'],
                'patterns': [
                    r'due\s+(?:dates?|books?)\s+(?:for|of)\s+([a-z0-9]+)',
                    r'([a-z0-9]+)[\'s]?\s+(?:due\s+dates?|return\s+dates?)',
                    r'when\s+(?:are|is)\s+([a-z0-9]+)[\'s]?\s+books?\s+due',
                    r'show\s+(?:due\s+dates?|return\s+dates?)\s+(?:for|of)\s+([a-z0-9]+)'
                ],
                'sql_template': '''
                    SELECT b.id, b.title, b.author, b.category,
                           i.issue_date, i.due_date, i.return_date,
                           CASE 
                               WHEN i.return_date IS NULL THEN 'Not Returned'
                               WHEN julianday(i.return_date) > julianday(i.due_date) THEN 'Returned Late'
                               ELSE 'Returned On Time'
                           END as return_status,
                           CASE 
                               WHEN i.return_date IS NULL AND i.due_date < date('now') THEN 'Overdue'
                               WHEN i.return_date IS NULL THEN 'Due Soon'
                               ELSE 'Returned'
                           END as current_status
                    FROM Books b
                    JOIN Issued i ON b.id = i.book_id
                    JOIN Students s ON i.student_id = s.id
                    WHERE s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?)
                    ORDER BY i.due_date ASC
                '''
            },
            
            # Student payment history
            'student_payments': {
                'keywords': ['payment', 'paid', 'transaction', 'settled', 'cleared'],
                'patterns': [
                    r'payment\s+(?:history|records?)\s+(?:for|of)\s+([a-z0-9]+)',
                    r'([a-z0-9]+)[\'s]?\s+payment\s+(?:history|records?)',
                    r'what\s+(?:payments|fines)\s+(?:did|has)\s+([a-z0-9]+)\s+(?:pay|paid)',
                    r'show\s+payment\s+(?:history|records?)\s+(?:for|of)\s+([a-z0-9]+)'
                ],
                'sql_template': '''
                    SELECT f.id, f.fine_amount, f.fine_type, f.issue_date, f.status,
                           s.roll_number, s.name, s.branch, s.year,
                           CASE 
                               WHEN f.status = 'Paid' THEN f.fine_amount
                               ELSE 0 
                           END as amount_paid
                    FROM Fines f
                    JOIN Students s ON f.student_id = s.id
                    WHERE (s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?))
                      AND f.status = 'Paid'
                    ORDER BY f.issue_date DESC
                '''
            },
            
            # Student profile and personal information
            'student_profile': {
                'keywords': ['profile', 'information', 'details', 'personal', 'bio'],
                'patterns': [
                    r'profile\s+(?:of|for)\s+([a-z0-9]+)',
                    r'([a-z0-9]+)[\'s]?\s+(?:profile|information|details)',
                    r'show\s+(?:personal|profile)\s+(?:information|details)\s+(?:for|of)\s+([a-z0-9]+)',
                    r'what\s+(?:is|are)\s+([a-z0-9]+)[\'s]?\s+(?:profile|details)'
                ],
                'sql_template': '''
                    SELECT s.id, s.roll_number, s.name, s.email, s.phone, 
                           s.branch, s.year, s.semester, s.address,
                           s.registration_date, s.status
                    FROM Students s
                    WHERE s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?)
                '''
            },
            
            'student_contact': {
                'keywords': ['contact', 'phone', 'email', 'address', 'communication'],
                'patterns': [
                    r'contact\s+(?:information|details)\s+(?:for|of)\s+([a-z0-9]+)',
                    r'([a-z0-9]+)[\'s]?\s+(?:contact|phone|email|address)',
                    r'how\s+(?:to|can\s+i)\s+(?:contact|call|email)\s+([a-z0-9]+)',
                    r'show\s+(?:contact|phone|email)\s+(?:for|of)\s+([a-z0-9]+)'
                ],
                'sql_template': '''
                    SELECT s.name, s.email, s.phone, s.address
                    FROM Students s
                    WHERE s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?)
                '''
            },
            
            # Academic performance queries
            'student_gpa': {
                'keywords': ['gpa', 'grade', 'performance', 'academic', 'score'],
                'patterns': [
                    r'gpa\s+(?:of|for)\s+([a-z0-9]+)',
                    r'([a-z0-9]+)[\'s]?\s+(?:gpa|grade|performance)',
                    r'what\s+(?:is|are)\s+([a-z0-9]+)[\'s]?\s+(?:gpa|grades)',
                    r'show\s+(?:academic|gpa)\s+(?:performance|records)\s+(?:for|of)\s+([a-z0-9]+)'
                ],
                'sql_template': '''
                    SELECT s.roll_number, s.name, s.branch, s.year, s.semester,
                           'GPA information not available in current database' as note
                    FROM Students s
                    WHERE s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?)
                '''
            },
            
            'student_attendance': {
                'keywords': ['attendance', 'present', 'absent', 'classes', 'lectures'],
                'patterns': [
                    r'attendance\s+(?:record|details)\s+(?:for|of)\s+([a-z0-9]+)',
                    r'([a-z0-9]+)[\'s]?\s+(?:attendance|presence)',
                    r'how\s+(?:many|much)\s+(?:classes|lectures)\s+(?:did|has)\s+([a-z0-9]+)\s+(?:attend|missed)',
                    r'show\s+attendance\s+(?:for|of)\s+([a-z0-9]+)'
                ],
                'sql_template': '''
                    SELECT s.roll_number, s.name, s.branch, s.year,
                           'Attendance information not available in current database' as note
                    FROM Students s
                    WHERE s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?)
                '''
            },
            
            # Book availability and catalog queries
            'book_availability': {
                'keywords': ['available', 'in stock', 'can borrow', 'check out'],
                'patterns': [
                    r'(?:are|is)\s+(?:any|some)\s+books?\s+(?:available|in stock)',
                    r'which\s+books?\s+(?:are|is)\s+(?:available|can\s+borrow)',
                    r'show\s+(?:available|in stock)\s+books?',
                    r'can\s+i\s+(?:borrow|check out)\s+(?:any|some)\s+books?'
                ],
                'sql_template': '''
                    SELECT b.id, b.title, b.author, b.category, b.isbn,
                           b.total_copies, b.available_copies
                    FROM Books b
                    WHERE b.available_copies > 0
                    ORDER BY b.title
                '''
            },
            
            'book_search': {
                'keywords': ['search', 'find', 'look for', 'locate'],
                'patterns': [
                    r'search\s+(?:for|books?)\s+(?:by|titled?|called?)\s+["\']?([^"\']+)["\']?',
                    r'find\s+(?:books?|book)\s+["\']?([^"\']+)["\']?',
                    r'look\s+for\s+(?:books?|book)\s+["\']?([^"\']+)["\']?',
                    r'locate\s+(?:books?|book)\s+["\']?([^"\']+)["\']?'
                ],
                'sql_template': '''
                    SELECT b.id, b.title, b.author, b.category, b.isbn,
                           b.total_copies, b.available_copies
                    FROM Books b
                    WHERE LOWER(b.title) LIKE LOWER(?) 
                       OR LOWER(b.author) LIKE LOWER(?)
                       OR LOWER(b.category) LIKE LOWER(?)
                    ORDER BY b.title
                '''
            },
            
            'book_by_author': {
                'keywords': ['author', 'written by', 'by author'],
                'patterns': [
                    r'books?\s+(?:by|written\s+by)\s+["\']?([^"\']+)["\']?',
                    r'["\']?([^"\']+)["\']?\s+(?:author|wrote)\s+books?',
                    r'show\s+books?\s+(?:by|from)\s+["\']?([^"\']+)["\']?',
                    r'what\s+books?\s+(?:did|has)\s+["\']?([^"\']+)["\']?\s+(?:write|wrote)'
                ],
                'sql_template': '''
                    SELECT b.id, b.title, b.author, b.category, b.isbn,
                           b.total_copies, b.available_copies
                    FROM Books b
                    WHERE LOWER(b.author) LIKE LOWER(?)
                    ORDER BY b.title
                '''
            },
            
            'book_by_category': {
                'keywords': ['category', 'genre', 'type', 'section'],
                'patterns': [
                    r'books?\s+(?:in|from)\s+(?:the\s+)?["\']?([^"\']+)["\']?\s+(?:category|genre|section)',
                    r'["\']?([^"\']+)["\']?\s+(?:category|genre|type)\s+books?',
                    r'show\s+(?:all|the)\s+books?\s+(?:in|from)\s+["\']?([^"\']+)["\']?',
                    r'what\s+books?\s+(?:are|is)\s+(?:in|available\s+in)\s+["\']?([^"\']+)["\']?'
                ],
                'sql_template': '''
                    SELECT b.id, b.title, b.author, b.category, b.isbn,
                           b.total_copies, b.available_copies
                    FROM Books b
                    WHERE LOWER(b.category) LIKE LOWER(?)
                    ORDER BY b.title
                '''
            },
            
            'book_by_isbn': {
                'keywords': ['isbn', 'isbn number', 'book number'],
                'patterns': [
                    r'book\s+(?:with|by)\s+isbn\s+["\']?([^"\']{10,17})["\']?',
                    r'isbn\s+["\']?([^"\']{10,17})["\']?\s+(?:book|details)',
                    r'find\s+book\s+(?:by|with)\s+isbn\s+["\']?([^"\']{10,17})["\']?',
                    r'show\s+book\s+(?:details|info)\s+(?:for|by)\s+isbn\s+["\']?([^"\']{10,17})["\']?'
                ],
                'sql_template': '''
                    SELECT b.id, b.title, b.author, b.category, b.isbn,
                           b.total_copies, b.available_copies
                    FROM Books b
                    WHERE b.isbn = ?
                '''
            },
            
            # Library statistics and analytics
            'library_stats': {
                'keywords': ['statistics', 'stats', 'analytics', 'summary', 'overview'],
                'patterns': [
                    r'library\s+(?:statistics|stats|analytics)',
                    r'show\s+(?:library|overall)\s+(?:statistics|stats|summary)',
                    r'what\s+(?:are|is)\s+(?:the\s+)?library\s+(?:statistics|stats)',
                    r'library\s+(?:overview|summary|report)'
                ],
                'sql_template': '''
                    SELECT 
                        (SELECT COUNT(*) FROM Books) as total_books,
                        (SELECT COUNT(*) FROM Students) as total_students,
                        (SELECT COUNT(*) FROM Issued WHERE return_date IS NULL) as books_issued,
                        (SELECT COUNT(*) FROM Fines WHERE status = 'Unpaid') as unpaid_fines,
                        (SELECT COUNT(*) FROM Books WHERE available_copies > 0) as available_books
                '''
            },
            
            'popular_books': {
                'keywords': ['popular', 'most borrowed', 'trending', 'top books'],
                'patterns': [
                    r'(?:most|top)\s+(?:popular|borrowed)\s+books?',
                    r'what\s+(?:are|is)\s+(?:the\s+)?(?:most|top)\s+(?:popular|borrowed)\s+books?',
                    r'show\s+(?:popular|trending|top)\s+books?',
                    r'which\s+books?\s+(?:are|is)\s+(?:most|highly)\s+(?:popular|borrowed)'
                ],
                'sql_template': '''
                    SELECT b.id, b.title, b.author, b.category, COUNT(i.id) as borrow_count
                    FROM Books b
                    JOIN Issued i ON b.id = i.book_id
                    GROUP BY b.id, b.title, b.author, b.category
                    ORDER BY borrow_count DESC
                    LIMIT 10
                '''
            },
            
            'new_arrivals': {
                'keywords': ['new', 'recent', 'latest', 'arrivals', 'additions'],
                'patterns': [
                    r'(?:new|recent|latest)\s+(?:books?|arrivals|additions)',
                    r'what\s+(?:are|is)\s+(?:the\s+)?(?:new|recent)\s+(?:books?|arrivals)',
                    r'show\s+(?:new|recent|latest)\s+(?:books?|arrivals)',
                    r'latest\s+(?:books?|additions)\s+(?:in|to)\s+(?:the\s+)?library'
                ],
                'sql_template': '''
                    SELECT b.id, b.title, b.author, b.category, b.isbn,
                           b.total_copies, b.available_copies, b.added_date
                    FROM Books b
                    ORDER BY b.added_date DESC
                    LIMIT 20
                '''
            },
            
            # Due date and return queries
            'due_tomorrow': {
                'keywords': ['tomorrow', 'next day', 'due tomorrow'],
                'patterns': [
                    r'books?\s+(?:due|to\s+return)\s+(?:tomorrow|next\s+day)',
                    r'what\s+books?\s+(?:are|is)\s+due\s+(?:tomorrow|next\s+day)',
                    r'show\s+books?\s+due\s+(?:tomorrow|next\s+day)',
                    r'which\s+books?\s+(?:have|has)\s+to\s+be\s+returned\s+(?:tomorrow|next\s+day)'
                ],
                'sql_template': '''
                    SELECT b.id, b.title, b.author, s.roll_number, s.name,
                           i.issue_date, i.due_date
                    FROM Books b
                    JOIN Issued i ON b.id = i.book_id
                    JOIN Students s ON i.student_id = s.id
                    WHERE i.return_date IS NULL 
                      AND i.due_date = date('now', '+1 day')
                    ORDER BY i.due_date
                '''
            },
            
            'overdue_books': {
                'keywords': ['overdue', 'late', 'past due', 'not returned'],
                'patterns': [
                    r'(?:overdue|late|past\s+due)\s+books?',
                    r'what\s+books?\s+(?:are|is)\s+(?:overdue|late|past\s+due)',
                    r'show\s+(?:overdue|late|not\s+returned)\s+books?',
                    r'which\s+books?\s+(?:have|has)\s+(?:not\s+been|not)\s+returned\s+on\s+time'
                ],
                'sql_template': '''
                    SELECT b.id, b.title, b.author, s.roll_number, s.name,
                           i.issue_date, i.due_date,
                           julianday(date('now')) - julianday(i.due_date) as days_overdue
                    FROM Books b
                    JOIN Issued i ON b.id = i.book_id
                    JOIN Students s ON i.student_id = s.id
                    WHERE i.return_date IS NULL 
                      AND i.due_date < date('now')
                    ORDER BY days_overdue DESC
                '''
            },
            
            'return_history': {
                'keywords': ['returned', 'given back', 'return history'],
                'patterns': [
                    r'return\s+(?:history|records?)\s+(?:for|of)\s+([a-z0-9]+)',
                    r'([a-z0-9]+)[\'s]?\s+return\s+(?:history|records?)',
                    r'what\s+(?:books?|items)\s+(?:did|has)\s+([a-z0-9]+)\s+(?:return|returned)',
                    r'show\s+(?:returned|given\s+back)\s+books?\s+(?:for|of)\s+([a-z0-9]+)'
                ],
                'sql_template': '''
                    SELECT b.id, b.title, b.author, b.category,
                           i.issue_date, i.due_date, i.return_date,
                           CASE 
                               WHEN julianday(i.return_date) > julianday(i.due_date) 
                               THEN julianday(i.return_date) - julianday(i.due_date)
                               ELSE 0
                           END as days_late
                    FROM Books b
                    JOIN Issued i ON b.id = i.book_id
                    JOIN Students s ON i.student_id = s.id
                    WHERE (s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?))
                      AND i.return_date IS NOT NULL
                    ORDER BY i.return_date DESC
                '''
            },
            
            # Fine and payment queries
            'fine_details': {
                'keywords': ['fine details', 'fine information', 'penalty details'],
                'patterns': [
                    r'fine\s+(?:details|information)\s+(?:for|of)\s+([a-z0-9]+)',
                    r'([a-z0-9]+)[\'s]?\s+fine\s+(?:details|information)',
                    r'show\s+fine\s+(?:details|information)\s+(?:for|of)\s+([a-z0-9]+)',
                    r'what\s+(?:are|is)\s+([a-z0-9]+)[\'s]?\s+fine\s+(?:details|information)'
                ],
                'sql_template': '''
                    SELECT f.id, f.fine_amount, f.fine_type, f.issue_date, 
                           f.due_date, f.status, f.paid_date,
                           s.roll_number, s.name
                    FROM Fines f
                    JOIN Students s ON f.student_id = s.id
                    WHERE (s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?))
                    ORDER BY f.issue_date DESC
                '''
            },
            
            'pending_fines': {
                'keywords': ['pending', 'unpaid', 'due', 'outstanding'],
                'patterns': [
                    r'pending\s+(?:fines|payments)\s+(?:for|of)\s+([a-z0-9]+)',
                    r'([a-z0-9]+)[\'s]?\s+(?:pending|unpaid|due|outstanding)\s+(?:fines|payments)',
                    r'what\s+(?:fines|payments)\s+(?:are|is)\s+(?:pending|unpaid|due)\s+(?:for|of)\s+([a-z0-9]+)',
                    r'show\s+(?:pending|unpaid|due|outstanding)\s+(?:fines|payments)\s+(?:for|of)\s+([a-z0-9]+)'
                ],
                'sql_template': '''
                    SELECT f.id, f.fine_amount, f.fine_type, f.issue_date, 
                           f.due_date, f.status,
                           s.roll_number, s.name,
                           julianday(date('now')) - julianday(f.due_date) as days_overdue
                    FROM Fines f
                    JOIN Students s ON f.student_id = s.id
                    WHERE (s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?))
                      AND f.status = 'Unpaid'
                    ORDER BY f.due_date
                '''
            },
            
            'total_fines': {
                'keywords': ['total', 'sum', 'overall', 'complete'],
                'patterns': [
                    r'total\s+(?:fines|amount)\s+(?:for|of)\s+([a-z0-9]+)',
                    r'([a-z0-9]+)[\'s]?\s+total\s+(?:fines|amount)',
                    r'what\s+(?:is|are)\s+([a-z0-9]+)[\'s]?\s+total\s+(?:fines|amount)',
                    r'show\s+total\s+(?:fines|amount)\s+(?:for|of)\s+([a-z0-9]+)'
                ],
                'sql_template': '''
                    SELECT 
                        s.roll_number, s.name,
                        COUNT(*) as total_fines,
                        SUM(f.fine_amount) as total_amount,
                        SUM(CASE WHEN f.status = 'Paid' THEN f.fine_amount ELSE 0 END) as paid_amount,
                        SUM(CASE WHEN f.status = 'Unpaid' THEN f.fine_amount ELSE 0 END) as unpaid_amount
                    FROM Fines f
                    JOIN Students s ON f.student_id = s.id
                    WHERE (s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?))
                    GROUP BY s.id, s.roll_number, s.name
                '''
            },
            
            # Reservation and booking queries
            'book_reservation': {
                'keywords': ['reserve', 'reservation', 'book', 'hold'],
                'patterns': [
                    r'reserve\s+(?:book|books?)\s+(?:for|of)\s+([a-z0-9]+)',
                    r'([a-z0-9]+)\s+(?:wants|wants\s+to)\s+reserve\s+(?:book|books?)',
                    r'how\s+to\s+reserve\s+(?:book|books?)\s+(?:for|of)\s+([a-z0-9]+)',
                    r'can\s+([a-z0-9]+)\s+reserve\s+(?:book|books?)'
                ],
                'sql_template': '''
                    SELECT s.roll_number, s.name,
                           'Reservation system not available in current database' as note
                    FROM Students s
                    WHERE s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?)
                '''
            },
            
            'reserved_books': {
                'keywords': ['reserved', 'held', 'booked'],
                'patterns': [
                    r'reserved\s+(?:books?|items)\s+(?:for|of)\s+([a-z0-9]+)',
                    r'([a-z0-9]+)[\'s]?\s+reserved\s+(?:books?|items)',
                    r'what\s+(?:books?|items)\s+(?:are|is)\s+reserved\s+(?:for|of)\s+([a-z0-9]+)',
                    r'show\s+reserved\s+(?:books?|items)\s+(?:for|of)\s+([a-z0-9]+)'
                ],
                'sql_template': '''
                    SELECT s.roll_number, s.name,
                           'No reservations found in current database' as note
                    FROM Students s
                    WHERE s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?)
                '''
            },
            
            # Library membership and account queries
            'membership_status': {
                'keywords': ['membership', 'account', 'status', 'active', 'inactive'],
                'patterns': [
                    r'membership\s+(?:status|details)\s+(?:for|of)\s+([a-z0-9]+)',
                    r'([a-z0-9]+)[\'s]?\s+(?:membership|account)\s+(?:status|details)',
                    r'what\s+(?:is|are)\s+([a-z0-9]+)[\'s]?\s+(?:membership|account)\s+(?:status)',
                    r'show\s+(?:membership|account)\s+(?:status|details)\s+(?:for|of)\s+([a-z0-9]+)'
                ],
                'sql_template': '''
                    SELECT s.id, s.roll_number, s.name, s.email, s.phone,
                           s.branch, s.year, s.semester, s.status,
                           s.registration_date
                    FROM Students s
                    WHERE s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?)
                '''
            },
            
            'account_balance': {
                'keywords': ['balance', 'account balance', 'due amount'],
                'patterns': [
                    r'account\s+(?:balance|due)\s+(?:for|of)\s+([a-z0-9]+)',
                    r'([a-z0-9]+)[\'s]?\s+account\s+(?:balance|due)',
                    r'what\s+(?:is|are)\s+([a-z0-9]+)[\'s]?\s+account\s+(?:balance|due)',
                    r'show\s+account\s+(?:balance|due)\s+(?:for|of)\s+([a-z0-9]+)'
                ],
                'sql_template': '''
                    SELECT s.roll_number, s.name,
                           SUM(CASE WHEN f.status = 'Unpaid' THEN f.fine_amount ELSE 0 END) as balance_due,
                           COUNT(CASE WHEN f.status = 'Unpaid' THEN 1 END) as pending_fines
                    FROM Students s
                    LEFT JOIN Fines f ON s.id = f.student_id AND f.status = 'Unpaid'
                    WHERE s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?)
                    GROUP BY s.id, s.roll_number, s.name
                '''
            },
            
            # Academic and course queries
            'course_enrollment': {
                'keywords': ['course', 'enrollment', 'registered', 'subjects'],
                'patterns': [
                    r'course\s+(?:enrollment|registration)\s+(?:for|of)\s+([a-z0-9]+)',
                    r'([a-z0-9]+)[\'s]?\s+(?:course|enrollment|registration)',
                    r'what\s+(?:courses?|subjects)\s+(?:is|are)\s+([a-z0-9]+)\s+(?:enrolled|registered)\s+(?:in|for)',
                    r'show\s+(?:course|enrollment)\s+(?:details|info)\s+(?:for|of)\s+([a-z0-9]+)'
                ],
                'sql_template': '''
                    SELECT s.roll_number, s.name, s.branch, s.year, s.semester,
                           'Course enrollment details not available in current database' as note
                    FROM Students s
                    WHERE s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?)
                '''
            },
            
            'academic_calendar': {
                'keywords': ['calendar', 'schedule', 'timetable', 'dates'],
                'patterns': [
                    r'academic\s+(?:calendar|schedule|timetable)',
                    r'show\s+(?:academic|library)\s+(?:calendar|schedule)',
                    r'what\s+(?:is|are)\s+(?:the\s+)?academic\s+(?:calendar|schedule)',
                    r'library\s+(?:calendar|schedule|timings)'
                ],
                'sql_template': '''
                    SELECT 'Academic calendar information not available in current database' as note,
                           date('now') as current_date
                '''
            },
            
            # Library services and facilities
            'library_hours': {
                'keywords': ['hours', 'timing', 'schedule', 'open', 'close'],
                'patterns': [
                    r'library\s+(?:hours|timings|schedule)',
                    r'when\s+(?:is|does)\s+(?:the\s+)?library\s+(?:open|close)',
                    r'what\s+(?:are|is)\s+(?:the\s+)?library\s+(?:hours|timings)',
                    r'show\s+library\s+(?:hours|timings|schedule)'
                ],
                'sql_template': '''
                    SELECT 'Library hours: 9:00 AM - 8:00 PM (Monday-Saturday), 10:00 AM - 6:00 PM (Sunday)' as hours,
                           date('now') as current_date
                '''
            },
            
            'library_services': {
                'keywords': ['services', 'facilities', 'amenities', 'features'],
                'patterns': [
                    r'library\s+(?:services|facilities|amenities)',
                    r'what\s+(?:services|facilities)\s+(?:are|is)\s+(?:available|offered)',
                    r'show\s+(?:library|available)\s+(?:services|facilities)',
                    r'library\s+(?:features|offerings)'
                ],
                'sql_template': '''
                    SELECT 'Available services: Book borrowing, Reading rooms, Computer access, Wi-Fi, Printing, Study areas' as services,
                           date('now') as current_date
                '''
            },
            
            # Report and analytics queries
            'borrowing_trends': {
                'keywords': ['trends', 'patterns', 'analytics', 'statistics'],
                'patterns': [
                    r'borrowing\s+(?:trends|patterns|statistics)',
                    r'what\s+(?:are|is)\s+(?:the\s+)?borrowing\s+(?:trends|patterns)',
                    r'show\s+borrowing\s+(?:trends|analytics|statistics)',
                    r'library\s+(?:usage|borrowing)\s+(?:trends|patterns)'
                ],
                'sql_template': '''
                    SELECT 
                        strftime('%Y-%m', i.issue_date) as month,
                        COUNT(*) as books_borrowed,
                        COUNT(DISTINCT i.student_id) as unique_students
                    FROM Issued i
                    WHERE i.issue_date >= date('now', '-12 months')
                    GROUP BY strftime('%Y-%m', i.issue_date)
                    ORDER BY month DESC
                '''
            },
            
            'category_popularity': {
                'keywords': ['popular categories', 'genre statistics', 'category trends'],
                'patterns': [
                    r'popular\s+(?:categories|genres)',
                    r'what\s+(?:categories|genres)\s+(?:are|is)\s+(?:most|highly)\s+(?:popular|borrowed)',
                    r'show\s+(?:category|genre)\s+(?:popularity|statistics)',
                    r'which\s+(?:categories|genres)\s+(?:are|is)\s+(?:most|highly)\s+(?:popular|borrowed)'
                ],
                'sql_template': '''
                    SELECT 
                        b.category,
                        COUNT(i.id) as borrow_count,
                        COUNT(DISTINCT i.student_id) as unique_students,
                        AVG(b.total_copies) as avg_copies
                    FROM Books b
                    LEFT JOIN Issued i ON b.id = i.book_id
                    GROUP BY b.category
                    ORDER BY borrow_count DESC
                '''
            },
            
            # Student activity and behavior
            'student_activity': {
                'keywords': ['activity', 'behavior', 'usage', 'interaction'],
                'patterns': [
                    r'student\s+(?:activity|behavior|usage)',
                    r'what\s+(?:is|are)\s+([a-z0-9]+)[\'s]?\s+(?:library|borrowing)\s+(?:activity|behavior)',
                    r'show\s+([a-z0-9]+)[\'s]?\s+(?:library|borrowing)\s+(?:activity|usage)',
                    r'how\s+(?:often|frequent)\s+(?:does|is)\s+([a-z0-9]+)\s+(?:use|visit)\s+(?:the\s+)?library'
                ],
                'sql_template': '''
                    SELECT 
                        s.roll_number, s.name,
                        COUNT(i.id) as total_borrows,
                        COUNT(DISTINCT i.book_id) as unique_books,
                        MIN(i.issue_date) as first_borrow,
                        MAX(i.issue_date) as last_borrow,
                        AVG(julianday(i.return_date) - julianday(i.issue_date)) as avg_borrow_days
                    FROM Students s
                    LEFT JOIN Issued i ON s.id = i.student_id
                    WHERE (s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?))
                    GROUP BY s.id, s.roll_number, s.name
                '''
            },
            
            'reading_habits': {
                'keywords': ['reading habits', 'preferences', 'interests'],
                'patterns': [
                    r'reading\s+(?:habits|preferences|interests)\s+(?:for|of)\s+([a-z0-9]+)',
                    r'([a-z0-9]+)[\'s]?\s+reading\s+(?:habits|preferences)',
                    r'what\s+(?:books|categories)\s+(?:does|do)\s+([a-z0-9]+)\s+(?:prefer|like|read)',
                    r'show\s+([a-z0-9]+)[\'s]?\s+reading\s+(?:habits|preferences)'
                ],
                'sql_template': '''
                    SELECT 
                        s.roll_number, s.name,
                        b.category,
                        COUNT(i.id) as category_count,
                        ROUND(COUNT(i.id) * 100.0 / (SELECT COUNT(*) FROM Issued WHERE student_id = s.id), 2) as percentage
                    FROM Students s
                    JOIN Issued i ON s.id = i.student_id
                    JOIN Books b ON i.book_id = b.id
                    WHERE (s.roll_number = ? OR s.id = ? OR LOWER(s.name) LIKE LOWER(?))
                    GROUP BY s.id, s.roll_number, s.name, b.category
                    ORDER BY category_count DESC
                '''
            },
            
            # Inventory and stock management
            'stock_status': {
                'keywords': ['stock', 'inventory', 'availability', 'copies'],
                'patterns': [
                    r'stock\s+(?:status|inventory|levels)',
                    r'what\s+(?:is|are)\s+(?:the\s+)?(?:current|total)\s+(?:stock|inventory)',
                    r'show\s+(?:book|stock)\s+(?:status|inventory)',
                    r'how\s+many\s+(?:copies|books)\s+(?:are|is)\s+(?:available|in stock)'
                ],
                'sql_template': '''
                    SELECT 
                        COUNT(*) as total_titles,
                        SUM(total_copies) as total_copies,
                        SUM(available_copies) as available_copies,
                        SUM(total_copies - available_copies) as borrowed_copies,
                        ROUND(AVG(available_copies * 100.0 / total_copies), 2) as availability_percentage
                    FROM Books
                '''
            },
            
            'low_stock_books': {
                'keywords': ['low stock', 'out of stock', 'unavailable'],
                'patterns': [
                    r'(?:low|out\s+of)\s+stock\s+books?',
                    r'what\s+books?\s+(?:are|is)\s+(?:low|out\s+of)\s+stock',
                    r'show\s+(?:low|out\s+of)\s+stock\s+books?',
                    r'which\s+books?\s+(?:have|has)\s+(?:no|low)\s+(?:stock|copies)'
                ],
                'sql_template': '''
                    SELECT b.id, b.title, b.author, b.category,
                           b.total_copies, b.available_copies,
                           CASE 
                               WHEN b.available_copies = 0 THEN 'Out of Stock'
                               WHEN b.available_copies <= 2 THEN 'Low Stock'
                               ELSE 'Available'
                           END as stock_status
                    FROM Books b
                    WHERE b.available_copies <= 2
                    ORDER BY b.available_copies ASC
                '''
            },
            
            # Special collections and featured items
            'featured_books': {
                'keywords': ['featured', 'recommended', 'suggested', 'staff picks'],
                'patterns': [
                    r'featured\s+(?:books|recommendations)',
                    r'what\s+(?:books|items)\s+(?:are|is)\s+(?:featured|recommended)',
                    r'show\s+(?:featured|recommended|suggested)\s+books?',
                    r'staff\s+(?:picks|recommendations|suggestions)'
                ],
                'sql_template': '''
                    SELECT b.id, b.title, b.author, b.category, b.isbn,
                           b.total_copies, b.available_copies,
                           'Featured collection' as collection_type
                    FROM Books b
                    WHERE b.available_copies > 0
                    ORDER BY RANDOM()
                    LIMIT 10
                '''
            },
            
            'rare_books': {
                'keywords': ['rare', 'special', 'valuable', 'collection'],
                'patterns': [
                    r'(?:(?:special|rare|valuable)\s+)?(?:books?|collections?)',
                    r'what\s+(?:special|rare|valuable)\s+(?:books?|collections?)\s+(?:do|does)\s+(?:the\s+)?library\s+have',
                    r'show\s+(?:special|rare|valuable)\s+(?:books?|collections?)',
                    r'library\s+(?:special|rare|valuable)\s+(?:books?|collections?)'
                ],
                'sql_template': '''
                    SELECT b.id, b.title, b.author, b.category, b.isbn,
                           b.total_copies, b.available_copies,
                           CASE 
                               WHEN b.total_copies <= 2 THEN 'Rare Collection'
                               ELSE 'Regular Collection'
                           END as collection_type
                    FROM Books b
                    WHERE b.total_copies <= 2
                    ORDER BY b.total_copies ASC
                '''
            },
            
            # Time-based and periodic queries
            'monthly_stats': {
                'keywords': ['monthly', 'this month', 'last month'],
                'patterns': [
                    r'(?:this|last)\s+month\s+(?:statistics|stats|summary)',
                    r'what\s+(?:happened|occurred)\s+(?:this|last)\s+month',
                    r'show\s+(?:this|last)\s+month\s+(?:activity|statistics)',
                    r'monthly\s+(?:report|summary|statistics)'
                ],
                'sql_template': '''
                    SELECT 
                        strftime('%Y-%m', date('now', 'start of month')) as current_month,
                        COUNT(CASE WHEN i.issue_date >= date('now', 'start of month') THEN 1 END) as this_month_issues,
                        COUNT(CASE WHEN i.issue_date >= date('now', 'start of month', '-1 month') 
                                 AND i.issue_date < date('now', 'start of month') THEN 1 END) as last_month_issues,
                        COUNT(CASE WHEN f.issue_date >= date('now', 'start of month') 
                                 AND f.status = 'Unpaid' THEN 1 END) as this_month_fines
                    FROM Issued i
                    CROSS JOIN Fines f
                '''
            },
            
            'weekly_activity': {
                'keywords': ['weekly', 'this week', 'last week'],
                'patterns': [
                    r'(?:this|last)\s+week\s+(?:activity|summary|report)',
                    r'what\s+(?:happened|occurred)\s+(?:this|last)\s+week',
                    r'show\s+(?:this|last)\s+week\s+(?:library|borrowing)\s+activity',
                    r'weekly\s+(?:activity|report|summary)'
                ],
                'sql_template': '''
                    SELECT 
                        strftime('%Y-W%W', date('now')) as current_week,
                        COUNT(CASE WHEN i.issue_date >= date('now', 'weekday 0', '-7 days') THEN 1 END) as this_week_issues,
                        COUNT(CASE WHEN i.issue_date >= date('now', 'weekday 0', '-14 days') 
                                 AND i.issue_date < date('now', 'weekday 0', '-7 days') THEN 1 END) as last_week_issues
                    FROM Issued i
                '''
            },
            
            # Department and branch specific queries
            'department_stats': {
                'keywords': ['department', 'branch', 'major'],
                'patterns': [
                    r'department\s+(?:statistics|stats|details)\s+(?:for|of)?\s*(["\']?[^"\']+["\']?)?',
                    r'branch\s+(?:statistics|stats|details)\s+(?:for|of)?\s*(["\']?[^"\']+["\']?)?',
                    r'show\s+(?:department|branch)\s+(?:statistics|details)\s+(?:for|of)?\s*(["\']?[^"\']+["\']?)?',
                    r'what\s+(?:are|is)\s+(?:the\s+)?(?:department|branch)\s+(?:statistics|details)'
                ],
                'sql_template': '''
                    SELECT 
                        s.branch,
                        COUNT(s.id) as total_students,
                        COUNT(i.id) as total_borrows,
                        AVG(f.fine_amount) as avg_fine_amount,
                        COUNT(CASE WHEN f.status = 'Unpaid' THEN 1 END) as unpaid_fines
                    FROM Students s
                    LEFT JOIN Issued i ON s.id = i.student_id
                    LEFT JOIN Fines f ON s.id = f.student_id
                    GROUP BY s.branch
                    ORDER BY total_students DESC
                '''
            },
            
            'year_wise_stats': {
                'keywords': ['year', 'academic year', 'batch'],
                'patterns': [
                    r'year\s+(?:statistics|stats|details)\s+(?:for|of)?\s*(["\']?\d+["\']?)?',
                    r'academic\s+year\s+(?:statistics|stats|details)',
                    r'show\s+year\s+(?:statistics|details)\s+(?:for|of)?\s*(["\']?\d+["\']?)?',
                    r'what\s+(?:are|is)\s+(?:the\s+)?year\s+(?:statistics|details)'
                ],
                'sql_template': '''
                    SELECT 
                        s.year,
                        COUNT(s.id) as total_students,
                        COUNT(i.id) as total_borrows,
                        AVG(f.fine_amount) as avg_fine_amount,
                        COUNT(CASE WHEN f.status = 'Unpaid' THEN 1 END) as unpaid_fines
                    FROM Students s
                    LEFT JOIN Issued i ON s.id = i.student_id
                    LEFT JOIN Fines f ON s.id = f.student_id
                    GROUP BY s.year
                    ORDER BY s.year
                '''
            },
            
            # Search and discovery queries
            'advanced_search': {
                'keywords': ['advanced search', 'detailed search', 'complex search'],
                'patterns': [
                    r'advanced\s+(?:search|find)\s+(?:for|books?)',
                    r'search\s+(?:books?|items)\s+(?:by|with)\s+(?:author|category|title)',
                    r'find\s+books?\s+(?:by|with|from)\s+["\']?([^"\']+)?["\']?',
                    r'detailed\s+(?:search|find)\s+(?:for|books?)'
                ],
                'sql_template': '''
                    SELECT b.id, b.title, b.author, b.category, b.isbn,
                           b.total_copies, b.available_copies
                    FROM Books b
                    WHERE (LOWER(b.title) LIKE LOWER(?) 
                       OR LOWER(b.author) LIKE LOWER(?)
                       OR LOWER(b.category) LIKE LOWER(?)
                       OR b.isbn LIKE ?)
                    ORDER BY b.title
                '''
            },
            
            'similar_books': {
                'keywords': ['similar', 'related', 'like this', 'recommendations'],
                'patterns': [
                    r'similar\s+(?:books?|items)\s+(?:to|like)\s+["\']?([^"\']+)?["\']?',
                    r'books?\s+(?:similar|related)\s+to\s+["\']?([^"\']+)?["\']?',
                    r'recommend\s+(?:books?|items)\s+(?:similar|like)\s+["\']?([^"\']+)?["\']?',
                    r'what\s+books?\s+(?:are|is)\s+(?:similar|like)\s+["\']?([^"\']+)?["\']?'
                ],
                'sql_template': '''
                    SELECT b.id, b.title, b.author, b.category, b.isbn,
                           b.total_copies, b.available_copies
                    FROM Books b
                    WHERE b.category = (SELECT category FROM Books WHERE LOWER(title) LIKE LOWER(?) LIMIT 1)
                      AND LOWER(b.title) != LOWER(?)
                    ORDER BY b.title
                    LIMIT 10
                '''
            },
            
            # Help and support queries
            'library_help': {
                'keywords': ['help', 'support', 'assistance', 'guidance'],
                'patterns': [
                    r'(?:library|book)\s+(?:help|support|assistance)',
                    r'how\s+(?:to|can\s+i)\s+(?:find|search|borrow|return)',
                    r'what\s+(?:help|support)\s+(?:is|are)\s+(?:available)',
                    r'library\s+(?:help|support|guidance)'
                ],
                'sql_template': '''
                    SELECT 'Library Help: Contact librarian at library@college.edu or visit the help desk' as help_info,
                           'Available services: Book search, borrowing assistance, fine payment, account management' as services
                '''
            },
            
            'library_rules': {
                'keywords': ['rules', 'regulations', 'policies', 'guidelines'],
                'patterns': [
                    r'library\s+(?:rules|regulations|policies|guidelines)',
                    r'what\s+(?:are|is)\s+(?:the\s+)?library\s+(?:rules|regulations)',
                    r'show\s+(?:library|borrowing)\s+(?:rules|policies)',
                    r'borrowing\s+(?:rules|regulations|policies)'
                ],
                'sql_template': '''
                    SELECT 'Library Rules: 
                    - Maximum 3 books per student
                    - 14-day borrowing period
                    - $0.50 per day late fine
                    - Books can be renewed once
                    - No food or drinks in reading areas' as rules
                '''
            },
            
            # Feedback and suggestions
            'student_feedback': {
                'keywords': ['feedback', 'suggestions', 'comments', 'reviews'],
                'patterns': [
                    r'student\s+(?:feedback|suggestions|comments)',
                    r'how\s+to\s+(?:give|provide|submit)\s+(?:feedback|suggestions)',
                    r'what\s+(?:is|are)\s+(?:the\s+)?student\s+(?:feedback|suggestions)',
                    r'submit\s+(?:feedback|suggestions|comments)'
                ],
                'sql_template': '''
                    SELECT 'Feedback system not available in current database' as note,
                           'Please contact library staff for feedback and suggestions' as alternative
                '''
            },
            
            # Emergency and special queries
            'emergency_contacts': {
                'keywords': ['emergency', 'urgent', 'immediate', 'critical'],
                'patterns': [
                    r'emergency\s+(?:contacts?|numbers?|information)',
                    r'urgent\s+(?:library|contact)\s+(?:information|numbers?)',
                    r'what\s+(?:are|is)\s+(?:the\s+)?emergency\s+(?:contacts?|numbers?)',
                    r'immediate\s+(?:help|assistance|contact)'
                ],
                'sql_template': '''
                    SELECT 'Emergency Contacts: 
                    - Library: 555-0123
                    - Security: 555-0911
                    - Medical: 555-0199' as emergency_info
                '''
            },
            
            'lost_books': {
                'keywords': ['lost', 'missing', 'damaged', 'cannot find'],
                'patterns': [
                    r'lost\s+(?:books?|items?)',
                    r'what\s+(?:to\s+do|happens)\s+(?:if|when)\s+(?:a|the)\s+book\s+(?:is|gets)\s+lost',
                    r'report\s+(?:lost|missing)\s+(?:books?|items?)',
                    r'how\s+to\s+(?:handle|deal\s+with)\s+lost\s+books?'
                ],
                'sql_template': '''
                    SELECT 'Lost Book Policy: 
                    - Report immediately to library staff
                    - Replacement cost + $10 processing fee
                    - Temporary borrowing suspension until resolved
                    - Contact library@college.edu for assistance' as policy
                '''
            },
            
            # Digital library queries
            'ebooks_available': {
                'keywords': ['ebook', 'digital', 'online', 'electronic'],
                'patterns': [
                    r'(?:ebooks?|digital|online|electronic)\s+books?',
                    r'what\s+(?:ebooks?|digital\s+books?)\s+(?:are|is)\s+(?:available)',
                    r'show\s+(?:available|accessible)\s+(?:ebooks?|digital\s+books?)',
                    r'how\s+to\s+(?:access|borrow)\s+(?:ebooks?|digital\s+books?)'
                ],
                'sql_template': '''
                    SELECT 'E-book services not available in current database' as note,
                           'Digital library services are under development' as status
                '''
            },
            
            # Events and programs
            'library_events': {
                'keywords': ['events', 'programs', 'workshops', 'activities'],
                'patterns': [
                    r'library\s+(?:events|programs|workshops|activities)',
                    r'what\s+(?:events|programs)\s+(?:are|is)\s+(?:happening|upcoming)',
                    r'show\s+(?:upcoming|current)\s+(?:library|events|programs)',
                    r'library\s+(?:activities|workshops|seminars)'
                ],
                'sql_template': '''
                    SELECT 'Library Events: 
                    - Book Club: Every Friday 4:00 PM
                    - Study Skills Workshop: Monthly
                    - Author Meet & Greet: Quarterly
                    - Reading Competition: Annual' as events
                '''
            },
            
            # Technical and system queries
            'system_status': {
                'keywords': ['system', 'server', 'database', 'technical'],
                'patterns': [
                    r'(?:library|system)\s+(?:status|health|performance)',
                    r'what\s+(?:is|are)\s+(?:the\s+)?(?:library|system)\s+(?:status)',
                    r'show\s+(?:system|database|server)\s+(?:status|health)',
                    r'is\s+(?:the\s+)?(?:library|system)\s+(?:working|operational|down)'
                ],
                'sql_template': '''
                    SELECT 
                        'System Status: Operational' as status,
                        date('now') as current_time,
                        'All services running normally' as message
                '''
            },
            
            # Comparison and ranking queries
            'top_students': {
                'keywords': ['top', 'best', 'highest', 'ranking'],
                'patterns': [
                    r'top\s+(?:students|borrowers)',
                    r'who\s+(?:are|is)\s+(?:the\s+)?top\s+(?:students|borrowers)',
                    r'show\s+(?:top|best)\s+(?:students|borrowers)',
                    r'which\s+students?\s+(?:have|has)\s+(?:the\s+)?(?:most|highest)\s+(?:borrows|activity)'
                ],
                'sql_template': '''
                    SELECT 
                        s.roll_number, s.name, s.branch, s.year,
                        COUNT(i.id) as total_borrows,
                        COUNT(DISTINCT i.book_id) as unique_books,
                        AVG(julianday(i.return_date) - julianday(i.issue_date)) as avg_borrow_days
                    FROM Students s
                    JOIN Issued i ON s.id = i.student_id
                    GROUP BY s.id, s.roll_number, s.name, s.branch, s.year
                    ORDER BY total_borrows DESC
                    LIMIT 10
                '''
            },
            
            'department_comparison': {
                'keywords': ['compare', 'comparison', 'versus', 'vs'],
                'patterns': [
                    r'compare\s+(?:departments|branches)',
                    r'department\s+(?:comparison|vs|versus)',
                    r'which\s+department\s+(?:has|have)\s+(?:more|better|higher)',
                    r'show\s+department\s+(?:comparison|statistics)'
                ],
                'sql_template': '''
                    SELECT 
                        s.branch,
                        COUNT(s.id) as total_students,
                        COUNT(i.id) as total_borrows,
                        ROUND(AVG(f.fine_amount), 2) as avg_fine,
                        COUNT(CASE WHEN f.status = 'Unpaid' THEN 1 END) as unpaid_count
                    FROM Students s
                    LEFT JOIN Issued i ON s.id = i.student_id
                    LEFT JOIN Fines f ON s.id = f.student_id
                    GROUP BY s.branch
                    ORDER BY total_borrows DESC
                '''
            },
            
            # Predictive and analytical queries
            'borrowing_prediction': {
                'keywords': ['predict', 'forecast', 'trend', 'estimate'],
                'patterns': [
                    r'(?:predict|forecast)\s+(?:borrowing|usage)',
                    r'what\s+(?:will|might)\s+(?:be|happen)\s+(?:next|in\s+future)',
                    r'(?:future|upcoming)\s+(?:trends|predictions)',
                    r'estimate\s+(?:future|upcoming)\s+(?:borrowing|usage)'
                ],
                'sql_template': '''
                    SELECT 
                        'Prediction features not available in current database' as note,
                        'Advanced analytics module under development' as status
                '''
            },
            
            # Miscellaneous comprehensive queries
            'quick_stats': {
                'keywords': ['quick', 'summary', 'overview', 'dashboard'],
                'patterns': [
                    r'quick\s+(?:stats|statistics|summary)',
                    r'show\s+(?:quick|brief)\s+(?:overview|summary)',
                    r'what\s+(?:is|are)\s+(?:the\s+)?quick\s+(?:stats|facts)',
                    r'library\s+(?:dashboard|overview|summary)'
                ],
                'sql_template': '''
                    SELECT 
                        (SELECT COUNT(*) FROM Books) as total_books,
                        (SELECT COUNT(*) FROM Students) as total_students,
                        (SELECT COUNT(*) FROM Issued WHERE return_date IS NULL) as current_issues,
                        (SELECT COUNT(*) FROM Fines WHERE status = 'Unpaid') as pending_fines,
                        (SELECT COUNT(*) FROM Books WHERE available_copies > 0) as available_books,
                        date('now') as current_date
                '''
            },
            
            'library_directory': {
                'keywords': ['directory', 'staff', 'contacts', 'locations'],
                'patterns': [
                    r'library\s+(?:directory|staff|contacts)',
                    r'who\s+(?:works|is)\s+(?:at|in)\s+(?:the\s+)?library',
                    r'show\s+(?:library|staff)\s+(?:directory|contacts)',
                    r'library\s+(?:staff|personnel|team)'
                ],
                'sql_template': '''
                    SELECT 'Library Directory: 
                    - Head Librarian: Dr. Sarah Johnson
                    - Assistant Librarian: Mr. Michael Chen
                    - Circulation Desk: Ms. Emily Davis
                    - Technical Support: Mr. Robert Wilson
                    - Email: library@college.edu
                    - Phone: 555-0123' as directory
                '''
            }
        }
    
    def _load_student_extractors(self) -> Dict:
        """Load comprehensive student entity extractors."""
        return {
            'student_id': [
                r'(?:student\s+)?([a-z]{2}\d{4})',  # MT3001 format
                r'(?:roll\s+number\s+)?([a-z0-9]+)',  # General roll number
                r'student\s+(?:id\s+)?([a-z0-9]+)',  # Student ID
                r'(?:id\s+)?([a-z0-9]+)',  # Just ID
                r'([a-z]{2}\d{4})',  # Direct roll number pattern
            ],
            'student_name': [
                r'student\s+([a-z\s]+)',  # Student name
                r'(?:by|for)\s+([a-z\s]+)',  # Name after preposition
                r'([a-z]+\s+[a-z]+)',  # Full name pattern
                r'student\s+(?:named?)\s+([a-z\s]+)',  # Student named
                r'(?:of\s+)?([a-z]+\s+[a-z]+)',  # Student of
            ],
            'book_title': [
                r'(?:book|books?)\s+(?:titled?|called?|named?)\s*["\']?([^"\']+)["\']?',  # Book titled "Name"
                r'(?:titled?|called?|named?)\s+["\']?([^"\']+)["\']?',  # Titled "Name"
                r'["\']([^"\']+)["\']?\s*(?:book|books?)',  # "Name" book
                r'book\s+["\']([^"\']+)["\']?',  # Book "Name"
                r'(?:find|search|show)\s+(?:for\s+)?["\']([^"\']+)["\']?',  # Find "Name"
            ],
            'book_author': [
                r'(?:by|written\s+by|author)\s+["\']?([^"\']+)["\']?',  # By "Author"
                r'["\']([^"\']+)["\']?\s*(?:author|wrote)',  # "Author" wrote
                r'(?:book|books?)\s+(?:by)\s+["\']?([^"\']+)["\']?',  # Book by "Author"
                r'(?:written\s+by)\s+["\']?([^"\']+)["\']?',  # Written by "Author"
            ],
            'book_category': [
                r'(?:category|genre|type)\s+(?:of\s+)?["\']?([^"\']+)["\']?',  # Category "Name"
                r'["\']([^"\']+)["\']?\s*(?:category|genre|type)',  # "Name" category
                r'(?:find|search|show)\s+(?:for\s+)?["\']?([^"\']+)["\']?\s+(?:books?|category|genre)',  # Find "Name" books
                r'(?:in|of)\s+(?:the\s+)?["\']?([^"\']+)["\']?\s+(?:category|genre|section)',  # In "Name" category
            ],
            'fine_amount': [
                r'\$(\d+(?:\.\d{2})?)',  # $50.00
                r'(\d+(?:\.\d{2})?)\s*(?:dollars?|usd)',  # 50.00 dollars
                r'(?:amount|fine|cost)\s+(?:of\s+)?\$(\d+(?:\.\d{2})?)',  # Amount of $50.00
                r'(?:fine|cost|charge)\s+(?:of\s+)?(\d+(?:\.\d{2})?)',  # Fine of 50.00
            ],
            'date_range': [
                r'(?:from|since|after)\s+(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})',  # From date
                r'(?:to|until|before)\s+(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})',  # To date
                r'(?:between|during)\s+(\d{4}-\d{2}-\d{2})\s+(?:and|to)\s+(\d{4}-\d{2}-\d{2})',  # Between dates
                r'(?:in|during)\s+(?:the\s+)?(last|past|recent)\s+(?:\d+|few|several)\s+(?:days?|weeks?|months?)',  # Last few days
            ],
            'book_status': [
                r'(?:available|in stock|not borrowed)',  # Available books
                r'(?:borrowed|issued|checked out|taken)',  # Borrowed books
                r'(?:overdue|late|not returned)',  # Overdue books
                r'(?:returned|given back)',  # Returned books
                r'(?:reserved|held)',  # Reserved books
            ],
            'fine_status': [
                r'(?:unpaid|due|pending|owed)',  # Unpaid fines
                r'(?:paid|settled|cleared|resolved)',  # Paid fines
                r'(?:all|total|complete)',  # All fines
            ],
            'academic_term': [
                r'(?:semester|term)\s+(\d+|[a-z]+)',  # Semester 1, Fall 2023
                r'(?:year|grade)\s+(\d+|[a-z]+)',  # Year 2, Grade 10
                r'(?:term|session)\s+(?:\d{4}|[a-z]+\s+\d{4})',  # Term 2023, Fall 2023
            ],
            'branch_department': [
                r'(?:branch|department|major)\s+(?:of\s+)?["\']?([^"\']+)["\']?',  # Branch "Name"
                r'["\']([^"\']+)["\']?\s*(?:branch|department|major)',  # "Name" branch
                r'(?:in|of)\s+(?:the\s+)?["\']?([^"\']+)["\']?\s+(?:branch|department)',  # In "Name" branch
                r'(?:computer|science|arts|engineering|commerce|medical)',  # Specific departments
            ]
        }
    
    def extract_student_entity(self, query: str) -> Dict:
        """Extract student entity from query."""
        query_lower = query.lower()
        entities = {}
        
        # Try roll number patterns first
        for pattern in self.student_entity_extractors['student_id']:
            match = re.search(pattern, query_lower)
            if match:
                entities['student_identifier'] = match.group(1).strip()
                entities['identifier_type'] = 'roll_number'
                return entities
        
        # Try name patterns
        for pattern in self.student_entity_extractors['student_name']:
            match = re.search(pattern, query_lower)
            if match:
                entities['student_identifier'] = match.group(1).strip()
                entities['identifier_type'] = 'name'
                return entities
        
        return entities
    
    def detect_student_query_type(self, query: str) -> Optional[str]:
        """Detect the type of student query."""
        query_lower = query.lower()
        
        # Check for personal queries first (my, mine, etc.)
        personal_indicators = ['my', 'mine', 'me', 'i have', 'i owe', 'i borrowed']
        if any(indicator in query_lower for indicator in personal_indicators):
            return 'personal_query'
        
        # Then check for specific student query types
        for query_type, pattern_data in self.student_query_patterns.items():
            # Check keywords
            if any(keyword in query_lower for keyword in pattern_data['keywords']):
                return query_type
            
            # Check patterns
            for pattern in pattern_data['patterns']:
                if re.search(pattern, query_lower):
                    return query_type
        
        return None
    
    def execute_student_query(self, query: str, current_student_id: int = None) -> Dict:
        """Execute student query with proper SQL generation."""
        query_type = self.detect_student_query_type(query)
        
        if not query_type:
            return {
                'success': False,
                'error': 'Could not determine query type',
                'suggestion': 'Try queries like: "show books borrowed by [student_roll_number]" or "show fines paid by [student_roll_number]"'
            }
        
        # Handle personal queries differently
        if query_type == 'personal_query':
            if not current_student_id:
                return {
                    'success': False,
                    'error': 'Could not determine current student',
                    'suggestion': 'Please log in as a student to use "my" queries'
                }
            
            # Use current student ID for personal queries
            student_id = current_student_id
            identifier_type = 'current_student'
        else:
            # Extract student entity for other queries
            entities = self.extract_student_entity(query)
            
            if not entities:
                return {
                    'success': False,
                    'error': 'Could not identify student',
                    'suggestion': 'Please specify student roll number (e.g., CS2005, AE1018) or name'
                }
            
            student_id = entities['student_identifier']
            identifier_type = entities.get('identifier_type', 'unknown')
        
        try:
            conn = get_db_connection(MAIN_DB)
            cursor = conn.cursor()
            
            # Get SQL template and execute
            sql_template = self.student_query_patterns[query_type]['sql_template']
            
            # Execute with appropriate parameters
            if query_type == 'personal_query':
                # For personal queries, use current student ID
                cursor.execute(sql_template, (student_id,))
            else:
                # For other queries, try roll number, ID, and name
                cursor.execute(sql_template, (student_id, student_id, f'%{student_id}%'))
            
            results = cursor.fetchall()
            
            if not results:
                return {
                    'success': True,
                    'query_type': query_type,
                    'student_identifier': student_id,
                    'identifier_type': identifier_type,
                    'message': f'No {query_type.replace("_", " ")} found for student {student_id}',
                    'data': [],
                    'sql_used': sql_template.strip()
                }
            
            # Convert to list of dictionaries
            data = []
            columns = [desc[0] for desc in cursor.description]
            
            for row in results:
                row_dict = dict(zip(columns, row))
                data.append(row_dict)
            
            return {
                'success': True,
                'query_type': query_type,
                'student_identifier': student_id,
                'identifier_type': identifier_type,
                'message': f'Found {len(data)} {query_type.replace("_", " ")} for student {student_id}',
                'data': data,
                'sql_used': sql_template.strip(),
                'columns': columns
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Database error: {str(e)}',
                'query_type': query_type,
                'student_identifier': student_id
            }
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_student_query_examples(self) -> List[str]:
        """Get comprehensive examples of student queries for ALL students."""
        return [
            # Book-related queries for various students
            "show books borrowed by student MT3001",
            "what books does student CS2005 currently have",
            "books issued to AE1018",
            "BM2048's borrowed books",
            "currently issued books for student John Doe",
            "overdue books for student Jane Smith",
            "books returned by MT3001",
            "CS2005 has books",
            "books with student AE1018",
            "student BM2048's borrowing history",
            
            # Book by title queries for different students
            "show books titled 'Python Programming' for MT3001",
            "student CS2005 borrowed 'Data Science Handbook'",
            "find 'Machine Learning' books for AE1018",
            "BM2048 wants 'Artificial Intelligence' book",
            "search 'Web Development' books for John Doe",
            "show 'Database Systems' book for Jane Smith",
            "AE1018 needs 'Computer Networks' textbook",
            "CS2005 borrowed 'Algorithms' book",
            
            # Book by author queries for different students
            "show books by 'John Doe' for MT3001",
            "student CS2005 borrowed books by 'Jane Smith'",
            "find books by 'Robert Johnson' for AE1018",
            "BM2048 likes books by 'William Brown'",
            "search works by 'Michael Davis' for John Doe",
            "show books written by 'Sarah Wilson' for Jane Smith",
            
            # Book by category queries for different students
            "show books in 'Computer Science' category for MT3001",
            "student CS2005 borrowed books from 'Engineering' section",
            "find 'Mathematics' books for AE1018",
            "BM2048 reads 'Physics' books",
            "search 'Biology' category books for John Doe",
            "show 'Chemistry' section books for Jane Smith",
            "AE1018 studies 'Statistics' books",
            
            # Book by date range queries for different students
            "books borrowed by MT3001 between 2023-01-01 and 2023-12-31",
            "student CS2005 borrowed books since 2023-06-01",
            "books issued to AE1018 after 2023-01-01",
            "BM2048's books borrowed before 2023-12-31",
            "books taken by John Doe in last 30 days",
            "Jane Smith's recent borrowing history",
            "books borrowed by CS2005 in last few weeks",
            
            # Fine-related queries for different students
            "show fines paid by MT3001",
            "unpaid fines for student CS2005",
            "how much does AE1018 owe in fines",
            "all fines for student BM2048",
            "John Doe's fine payment history",
            "payment history for student Jane Smith",
            "what fines did MT3001 pay",
            "CS2005's unpaid fines",
            "student AE1018 owes fines",
            "BM2048 needs to pay fines",
            "fines over $50 for John Doe",
            "student Jane Smith has fines over $25",
            "fines under $10 for MT3001",
            "CS2005 has fines less than $100",
            "late return fines for AE1018",
            "lost book fines for student BM2048",
            "damage fines for John Doe",
            "Jane Smith's late return fines",
            
            # Student information queries for different students
            "student details for MT3001",
            "show information about student CS2005",
            "who is student AE1018",
            "BM2048's profile and activity",
            "contact information for student John Doe",
            "what is Jane Smith's email",
            "phone number for student MT3001",
            "CS2005's contact details",
            "student AE1018's profile information",
            "BM2048's personal information",
            "John Doe's student information",
            
            # Academic queries for different students
            "attendance for student MT3001",
            "CS2005's attendance percentage",
            "how many classes did AE1018 attend",
            "BM2048 missed classes",
            "student John Doe's attendance record",
            "Jane Smith's presence in classes",
            "gpa for student MT3001",
            "what are CS2005's grades",
            "AE1018's academic performance",
            "student BM2048's GPA score",
            "John Doe's grade history",
            "Jane Smith's academic record",
            "MT3001's semester performance",
            "student CS2005's academic history",
            "AE1018's semester grades",
            
            # Branch/Year queries for different students
            "branch for student MT3001",
            "what branch is CS2005 in",
            "AE1018's department and year",
            "which year is BM2048 studying",
            "class information for student John Doe",
            "MT3001 studies Computer Science",
            "student CS2005 is in Engineering",
            "AE1018 is in Arts department",
            "BM2048's year of study",
            "John Doe's semester information",
            "Jane Smith's program details",
            "CS2005 studies Mechanical Engineering",
            "AE1018 is in Commerce branch",
            "BM2048 is in Science department",
            
            # Statistics queries for different students
            "library statistics for student MT3001",
            "CS2005's reading summary",
            "how many books has AE1018 borrowed",
            "total fines paid by BM2048",
            "current books issued to John Doe",
            "unpaid fines amount for Jane Smith",
            "MT3001's library usage statistics",
            "student CS2005's borrowing count",
            "AE1018's fine payment total",
            "BM2048's complete library record",
            "John Doe's reading habits",
            "Jane Smith's fine history",
            
            # Activity queries for different students
            "student activity for MT3001",
            "library history of student CS2005",
            "what has student AE1018 done in library",
            "BM2048's complete library record",
            "recent activity for student John Doe",
            "what did Jane Smith do recently",
            "MT3001's recent library activity",
            "student CS2005's last 30 days activity",
            "AE1018's borrowing patterns",
            "BM2048's library behavior",
            "John Doe's recent transactions",
            "Jane Smith's activity log",
            
            # Due dates queries for different students
            "due dates for student MT3001",
            "when are CS2005's books due",
            "AE1018's return dates",
            "show due dates for student BM2048",
            "overdue books for student John Doe",
            "Jane Smith's overdue items",
            "books due soon for MT3001",
            "CS2005's pending returns",
            "AE1018's deadline list",
            "BM2048's return schedule",
            "John Doe's due book list",
            "Jane Smith's overdue notifications",
            
            # Payment queries for different students
            "payment history for student MT3001",
            "what fines did CS2005 pay",
            "AE1018's fine settlement history",
            "student BM2048's payment records",
            "John Doe's cleared fines",
            "how much did Jane Smith pay in fines",
            "MT3001's payment transactions",
            "CS2005's fine receipts",
            "AE1018's payment details",
            "BM2048's settlement history",
            "John Doe's payment log",
            "Jane Smith's cleared dues",
            
            # Personal queries (for logged-in students)
            "show my fines",
            "my borrowed books",
            "what are my fines",
            "my library statistics",
            "my attendance",
            "my gpa",
            "my contact details",
            "my recent activity",
            "my due dates",
            "my branch information",
            "my academic performance",
            "my payment history",
            
            # Combined and complex queries for different students
            "show borrowed books and unpaid fines for MT3001",
            "student CS2005 details with current issued books",
            "AE1018's library activity and fine status",
            "attendance and GPA for student BM2048",
            "contact and branch information for John Doe",
            "MT3001's books borrowed in last month",
            "unpaid fines and due dates for CS2005",
            "AE1018's academic and library performance",
            "student BM2048's complete profile",
            "John Doe's library and fine summary",
            "Jane Smith's academic and borrowing history",
            "CS2005's attendance and fine records",
            "AE1018's books and payment history",
            "BM2048's complete student information",
            
            # Additional diverse student examples
            "show books borrowed by student ST1001",
            "what books does student IT2003 currently have",
            "books issued to EC3005",
            "ME1002's borrowed books",
            "unpaid fines for student PH2001",
            "attendance for student CH3002",
            "gpa for student MA1003",
            "branch for student BI2004",
            "library statistics for student GE1005",
            "student HY2006's profile and activity",
            "contact information for student PS1007",
            "due dates for student EN2008",
            "payment history for student MU1009"
        ]


# Global instance
enhanced_student_queries = EnhancedStudentQueries()
