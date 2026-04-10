"""
Chatbot route for SPEAK2DB.

Handles natural language commands for Books CRUD via POST /chat.
Uses Flask session to track multi-turn clarification conversations.

Supported intents:
  add_book    – requires: title, author; optional: category, copies
  delete_book – requires: title
  update_book – requires: title + at least one update field
  view_books  – no required fields; executes immediately

Session keys used:
  chat_intent : str     – current pending intent
  chat_data   : dict    – data collected so far
"""
from __future__ import annotations

import logging
import re
from typing import Optional

from flask import Blueprint, jsonify, request, session

from db.connection import get_db_connection, MAIN_DB
from utils.decorators import require_roles

logger = logging.getLogger(__name__)

chat_bp = Blueprint("chat", __name__)

# ---------------------------------------------------------------------------
# Required fields per intent
# ---------------------------------------------------------------------------

_REQUIRED: dict[str, list[str]] = {
    "add_book": ["title", "author"],
    "delete_book": ["title"],
    "update_book": ["title"],
    "view_books": [],
    "show_books": [],
    "show_available": [],
    "count_query": [],
    "issue_book": ["title", "student_id"],
    "return_book": ["title", "student_id"],
}

_CLARIFICATION_QUESTIONS: dict[str, str] = {
    "title": "What is the title of the book?",
    "author": "Who is the author?",
    "category": "What category does the book belong to? (or type 'skip' to leave blank)",
    "copies": "How many copies are there? (or type 'skip' to use 1)",
    "student_id": "What is the student ID?",
    "confirm_delete": "Are you sure you want to delete \"{title}\"? (yes/no)",
}

_ADD_OPTIONAL = ["category", "copies"]


# ---------------------------------------------------------------------------
# Input normalization and multi-intent handling
# ---------------------------------------------------------------------------

def _normalize_input(text: str) -> str:
    """Normalize user input by removing filler words and converting to lowercase."""
    filler_words = {
        "please", "can you", "could you", "would you", "give me", "show me", 
        "tell me", "list me", "display me", "get me", "find me", "search me",
        "i want", "i need", "i'd like", "help me", "let me"
    }
    
    text = text.lower()
    for filler in filler_words:
        text = text.replace(filler, "")
    
    # Remove extra whitespace
    text = " ".join(text.split())
    return text.strip()


def _split_multi_intents(text: str) -> list[str]:
    """Split complex commands by 'and', 'then', 'also'."""
    separators = [" and ", " then ", " also ", " plus ", " next "]
    parts = [text]
    
    for sep in separators:
        new_parts = []
        for part in parts:
            new_parts.extend([p.strip() for p in part.split(sep) if p.strip()])
        parts = new_parts
    
    return [p for p in parts if p]


# ---------------------------------------------------------------------------
# Intent detection
# ---------------------------------------------------------------------------

def _detect_intent(text: str) -> Optional[str]:
    """Detect intent based on flexible question patterns, not strict commands."""
    t = text.lower()
    print("User input:", text)  # Debug log
    
    # Question-based intent detection
    if any(k in t for k in ("how many", "count", "number of", "total")):
        intent = "count_query"
        print("Detected intent:", intent)  # Debug log
        return intent
    
    if any(k in t for k in ("show", "list", "display", "which", "give me", "what", "find", "search", "get", "see")):
        # Check if it's about availability
        if any(k in t for k in ("available", "in stock", "not issued")):
            intent = "show_available"
        else:
            intent = "show_books"
        print("Detected intent:", intent)  # Debug log
        return intent
    
    if any(k in t for k in ("add", "create", "new", "insert", "put")):
        intent = "add_book"
        print("Detected intent:", intent)  # Debug log
        return intent
    
    if any(k in t for k in ("delete", "remove", "get rid of", "eliminate")):
        intent = "delete_book"
        print("Detected intent:", intent)  # Debug log
        return intent
    
    if any(k in t for k in ("update", "change", "modify", "edit", "alter", "set")):
        intent = "update_book"
        print("Detected intent:", intent)  # Debug log
        return intent
    
    if any(k in t for k in ("issue", "borrow", "lend", "give", "assign", "check out")):
        intent = "issue_book"
        print("Detected intent:", intent)  # Debug log
        return intent
    
    # Check for return operations
    if any(k in t for k in ("return", "give back", "check in")):
        intent = "return_book"
        print("Detected intent:", intent)  # Debug log
        return intent
    
    print("Detected intent: None")  # Debug log
    return None


# ---------------------------------------------------------------------------
# Entity extraction
# ---------------------------------------------------------------------------

def _normalize_spaces(text: str) -> str:
    """Collapse multiple whitespace characters into a single space."""
    return " ".join(text.split())


def _extract_title_author(text: str) -> dict:
    """
    Extract title and author from text.

    Patterns recognised:
      "X by Y"   → title=X, author=Y
      "\"X\" by Y" → title=X, author=Y
    Returns only the keys that were actually found.
    """
    data: dict = {}
    # Normalise whitespace first to prevent ReDoS with many-space inputs
    text = _normalize_spaces(text)
    # Strip leading action words (add, delete, update, view etc.)
    clean = re.sub(
        r"^(add|insert|create|delete|remove|update|change|edit|view|show|list|get|new)"
        r"( a| the| an)? book ?",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()

    # "TITLE by AUTHOR" – split on literal " by " (single-space-normalised)
    lower = clean.lower()
    by_idx = lower.find(" by ")
    if by_idx != -1:
        data["title"] = clean[:by_idx].strip().strip('"').strip("'")
        data["author"] = clean[by_idx + 4:].strip().strip('"').strip("'")
        return data

    # Just a title without author
    if clean:
        data["title"] = clean.strip('"').strip("'")
    return data


def _extract_copies(text: str) -> Optional[int]:
    """Return an explicit copies count mentioned in the text."""
    # Normalise spaces first
    text = _normalize_spaces(text)
    m = re.search(r'\b(\d+) cop(?:y|ies)\b', text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    m = re.search(r'\bcopies? ?[=:] ?(\d+)\b', text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    # "set copies to N" – use split approach to avoid ReDoS
    lower = text.lower()
    if "set" in lower and "to" in lower:
        idx_to = lower.rfind(" to ")
        if idx_to != -1:
            tail = lower[idx_to + 4:].strip()
            m2 = re.match(r'^(\d+)\b', tail)
            if m2:
                return int(m2.group(1))
    return None


def _extract_entities(text: str, intent: str) -> dict:
    """Extract entities from natural language input with flexible patterns."""
    data = _extract_title_author(text)
    copies = _extract_copies(text)
    if copies is not None:
        data["copies"] = copies

    # Category: "category: X" or "category X" or "X books" (normalise spaces first)
    norm = _normalize_spaces(text)
    
    # Flexible category extraction
    m = re.search(r'\bcategory ?[=:] ?([A-Za-z][^\s,]{0,50})\b', norm, re.IGNORECASE)
    if not m:
        m = re.search(r'\bcategory ([A-Za-z][^\s,]{0,50})\b', norm, re.IGNORECASE)
    if not m:
        # Pattern: "AI books", "fiction books", "science books"
        m = re.search(r'\b([A-Za-z][^\s]{1,30})\s+books?\b', norm, re.IGNORECASE)
    if m:
        data["category"] = m.group(1).strip()

    # Flexible author extraction
    # "books by russell", "russell's books", "written by russell"
    m = re.search(r'\bby\s+([A-Za-z][^\s,]{0,50})\b', norm, re.IGNORECASE)
    if not m:
        m = re.search(r'\b([A-Za-z][^\s,]{1,30})\'?s?\s+books?\b', norm, re.IGNORECASE)
    if not m:
        m = re.search(r'\bwritten\s+by\s+([A-Za-z][^\s,]{0,50})\b', norm, re.IGNORECASE)
    if m:
        data["author"] = m.group(1).strip()

    # Flexible year extraction
    # "after 2020", "before 2020", "in 2020", "published 2020", "from 2020"
    m = re.search(r'\b(after|before|in|published|from)\s+(\d{4})\b', norm, re.IGNORECASE)
    if m:
        data["year"] = int(m.group(2))
        operator = m.group(1).lower()
        if operator in ["after", "from"]:
            data["year_operator"] = "after"
        elif operator == "before":
            data["year_operator"] = "before"
        else:
            data["year_operator"] = "in"

    # Student ID extraction for issue_book
    if intent == "issue_book":
        # Look for patterns like "student 123", "student id 123", "to student 123"
        m = re.search(r'\bstudent(?:\s+id)?\s+(\d+)\b', norm, re.IGNORECASE)
        if m:
            data["student_id"] = int(m.group(1))
        else:
            # Look for patterns like "to 123" or "for 123"
            m = re.search(r'\b(?:to|for)\s+(\d+)\b', norm, re.IGNORECASE)
            if m:
                data["student_id"] = int(m.group(1))

    # Extract sorting information
    if re.search(r'\bsort(?:ed)?\s+by\s+(\w+)', norm, re.IGNORECASE):
        m = re.search(r'\bsort(?:ed)?\s+by\s+(\w+)', norm, re.IGNORECASE)
        data["sort_by"] = m.group(1).lower()
    elif re.search(r'\border\s+by\s+(\w+)', norm, re.IGNORECASE):
        m = re.search(r'\border\s+by\s+(\w+)', norm, re.IGNORECASE)
        data["sort_by"] = m.group(1).lower()

    # Extract aggregation requests
    if re.search(r'\bhow\s+many\s+books?\b', norm, re.IGNORECASE):
        data["aggregate"] = "count"
        data["target"] = "books"
    elif re.search(r'\bhow\s+many\s+issued\s+books?\b', norm, re.IGNORECASE):
        data["aggregate"] = "count"
        data["target"] = "issued_books"
    elif re.search(r'\bcount\s+(?:the\s+)?books?\b', norm, re.IGNORECASE):
        data["aggregate"] = "count"
        data["target"] = "books"

    return data


# ---------------------------------------------------------------------------
# Dynamic SQL generation for complex queries
# ---------------------------------------------------------------------------

def _build_complex_query(data: dict, intent: str) -> dict:
    """Build SQL query based on extracted filters and conditions."""
    if data.get("aggregate") == "count":
        return _build_count_query(data)
    
    if intent in ["view_books", "show_books"]:
        return _build_select_query(data)
    
    return None

def _build_count_query(data: dict) -> dict:
    """Build COUNT query based on target table."""
    target = data.get("target", "books")
    
    if target == "issued_books":
        sql = "SELECT COUNT(*) as count FROM Issued WHERE return_date IS NULL"
        params = []
    else:
        sql = "SELECT COUNT(*) as count FROM Books"
        params = []
        where_clauses = []
        
        # Add WHERE conditions based on filters
        if data.get("author"):
            where_clauses.append("LOWER(author) = LOWER(?)")
            params.append(data["author"])
        
        if data.get("category"):
            where_clauses.append("LOWER(category) = LOWER(?)")
            params.append(data["category"])
        
        if data.get("year"):
            if data.get("year_operator") == "after":
                where_clauses.append("CAST(SUBSTR(id, 1, 4) AS INTEGER) > ?")
                params.append(data["year"])
            elif data.get("year_operator") == "before":
                where_clauses.append("CAST(SUBSTR(id, 1, 4) AS INTEGER) < ?")
                params.append(data["year"])
            else:  # "in"
                where_clauses.append("CAST(SUBSTR(id, 1, 4) AS INTEGER) = ?")
                params.append(data["year"])
        
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
    
    return {"sql": sql, "params": params, "type": "count"}

def _build_select_query(data: dict) -> dict:
    """Build SELECT query with filters and sorting."""
    sql = "SELECT id, title, author, category, total_copies, available_copies FROM Books"
    params = []
    where_clauses = []
    
    # Add WHERE conditions based on filters
    if data.get("author"):
        where_clauses.append("LOWER(author) = LOWER(?)")
        params.append(data["author"])
    
    if data.get("category"):
        where_clauses.append("LOWER(category) = LOWER(?)")
        params.append(data["category"])
    
    if data.get("year"):
        if data.get("year_operator") == "after":
            where_clauses.append("CAST(SUBSTR(id, 1, 4) AS INTEGER) > ?")
            params.append(data["year"])
        elif data.get("year_operator") == "before":
            where_clauses.append("CAST(SUBSTR(id, 1, 4) AS INTEGER) < ?")
            params.append(data["year"])
        else:  # "in"
            where_clauses.append("CAST(SUBSTR(id, 1, 4) AS INTEGER) = ?")
            params.append(data["year"])
    
    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)
    
    # Add ORDER BY clause
    if data.get("sort_by"):
        sort_field = data["sort_by"]
        if sort_field in ["title", "author", "category"]:
            sql += f" ORDER BY LOWER({sort_field})"
        elif sort_field in ["total_copies", "available_copies"]:
            sql += f" ORDER BY {sort_field}"
        else:
            sql += " ORDER BY title"
    else:
        sql += " ORDER BY title"
    
    sql += " LIMIT 100"
    
    return {"sql": sql, "params": params, "type": "select"}


# ---------------------------------------------------------------------------
# CRUD operations
# ---------------------------------------------------------------------------

def _view_books() -> dict:
    try:
        conn = get_db_connection(MAIN_DB)
        rows = conn.execute(
            "SELECT id, title, author, category, total_copies, available_copies "
            "FROM Books ORDER BY title LIMIT 100"
        ).fetchall()
        conn.close()
        books = [dict(r) for r in rows]
        if not books:
            return {"message": "No books found in library.", "action": "view", "data": []}
        return {
            "message": f"Found {len(books)} book(s).",
            "action": "view",
            "data": books,
        }
    except Exception as exc:
        logger.error("chat view_books error: %s", exc)
        return {"message": "Failed to retrieve books.", "action": "view", "data": []}


def _show_available_books(data: dict) -> dict:
    """Show only available books (with available_copies > 0)."""
    try:
        conn = get_db_connection(MAIN_DB)
        
        # Build query with filters if provided
        sql = "SELECT id, title, author, category, total_copies, available_copies FROM Books WHERE available_copies > 0"
        params = []
        where_clauses = []
        
        # Add filters
        if data.get("author"):
            where_clauses.append("LOWER(author) = LOWER(?)")
            params.append(data["author"])
        
        if data.get("category"):
            where_clauses.append("LOWER(category) = LOWER(?)")
            params.append(data["category"])
        
        if where_clauses:
            sql += " AND " + " AND ".join(where_clauses)
        
        # Add sorting
        if data.get("sort_by"):
            sort_field = data["sort_by"]
            if sort_field in ["title", "author", "category"]:
                sql += f" ORDER BY LOWER({sort_field})"
            else:
                sql += " ORDER BY title"
        else:
            sql += " ORDER BY title"
        
        sql += " LIMIT 100"
        
        rows = conn.execute(sql, params).fetchall()
        books = [dict(r) for r in rows]
        conn.close()
        
        if not books:
            return {"message": "No available books found.", "action": "view", "data": []}
        
        filter_desc = _build_filter_description(data)
        return {
            "message": f"Found {len(books)} available book(s){filter_desc}.",
            "action": "view",
            "data": books
        }
    except Exception as exc:
        logger.error("chat show_available error: %s", exc)
        return {"message": "Failed to retrieve available books.", "action": "view", "data": []}


def _return_book(data: dict) -> dict:
    """Handle book return operations."""
    title = data.get("title", "").strip()
    student_id = data.get("student_id")
    
    if not title:
        return {"message": "Book title is required to return a book.", "action": "return", "success": False}
    
    if student_id is None:
        return {"message": "Student ID is required to return a book.", "action": "return", "success": False}
    
    try:
        student_id = int(student_id)
    except (TypeError, ValueError):
        return {"message": "Invalid student ID format.", "action": "return", "success": False}

    try:
        conn = get_db_connection(MAIN_DB)
        
        # Find active issue record for this book and student
        issue = conn.execute(
            """SELECT i.id, i.book_id, b.title 
               FROM Issued i 
               JOIN Books b ON i.book_id = b.id 
               WHERE LOWER(b.title) = LOWER(?) AND i.student_id = ? AND i.return_date IS NULL""",
            (title, student_id)
        ).fetchone()
        
        if not issue:
            conn.close()
            return {"message": f'No active issue found for book "{title}" and student {student_id}.', "action": "return", "success": False}
        
        # Update the issue record
        from datetime import date
        return_date = date.today().isoformat()
        conn.execute(
            "UPDATE Issued SET return_date = ?, status = 'Returned' WHERE id = ?",
            (return_date, issue["id"])
        )
        
        # Increment available copies
        conn.execute(
            "UPDATE Books SET available_copies = available_copies + 1 WHERE id = ?",
            (issue["book_id"],)
        )
        
        conn.commit()
        conn.close()
        
        logger.info("[Chat] Book returned: title=%r, student_id=%d", title, student_id)
        return {
            "message": f'Book "{issue["title"]}" returned successfully by student {student_id}!',
            "action": "return",
            "success": True,
            "data": {"title": issue["title"], "student_id": student_id, "return_date": return_date},
        }
    except Exception as exc:
        logger.error("chat return_book error: %s", exc)
        return {"message": "Failed to return book due to a database error.", "action": "return", "success": False}


def _execute_complex_query(data: dict, intent: str) -> dict:
    """Execute complex query with filters, sorting, and aggregation."""
    try:
        query_info = _build_complex_query(data, intent)
        if not query_info:
            return {"message": "Unable to build query.", "action": None}
        
        conn = get_db_connection(MAIN_DB)
        
        if query_info["type"] == "count":
            result = conn.execute(query_info["sql"], query_info["params"]).fetchone()
            count = result["count"] if result else 0
            target = data.get("target", "books")
            conn.close()
            return {
                "message": f"Found {count} {target}.",
                "action": "count",
                "data": {"count": count, "target": target}
            }
        
        elif query_info["type"] == "select":
            rows = conn.execute(query_info["sql"], query_info["params"]).fetchall()
            books = [dict(r) for r in rows]
            conn.close()
            
            if not books:
                return {"message": "No books found matching your criteria.", "action": "view", "data": []}
            
            filter_desc = _build_filter_description(data)
            return {
                "message": f"Found {len(books)} book(s){filter_desc}.",
                "action": "view",
                "data": books
            }
        
        conn.close()
        return {"message": "Query completed.", "action": "view", "data": []}
        
    except Exception as exc:
        logger.error("chat complex query error: %s", exc)
        return {"message": "Failed to execute query.", "action": None}


def _build_filter_description(data: dict) -> str:
    """Build human-readable description of applied filters."""
    descriptions = []
    
    if data.get("author"):
        descriptions.append(f" by {data['author']}")
    
    if data.get("category"):
        descriptions.append(f" in category '{data['category']}'")
    
    if data.get("year"):
        op = data.get("year_operator", "in")
        descriptions.append(f" {op} {data['year']}")
    
    if data.get("sort_by"):
        descriptions.append(f" sorted by {data['sort_by']}")
    
    return " " + " ".join(descriptions) if descriptions else ""


def _add_book(data: dict) -> dict:
    title = data.get("title", "").strip()
    author = data.get("author", "").strip()
    category = data.get("category", "").strip()
    try:
        copies = int(data.get("copies", 1))
        if copies < 1:
            copies = 1
    except (TypeError, ValueError):
        copies = 1

    if not title or not author:
        return {"message": "Title and author are required to add a book.", "action": "add", "success": False}

    try:
        conn = get_db_connection(MAIN_DB)
        conn.execute(
            "INSERT INTO Books (title, author, category, total_copies, available_copies) VALUES (?, ?, ?, ?, ?)",
            (title, author, category, copies, copies),
        )
        conn.commit()
        conn.close()
        logger.info("[Chat] Book added: title=%r, author=%r, copies=%d", title, author, copies)
        return {
            "message": f'Book "{title}" by {author} added successfully!',
            "action": "add",
            "success": True,
            "data": {"title": title, "author": author, "category": category, "copies": copies},
        }
    except Exception as exc:
        logger.error("chat add_book error: %s", exc)
        return {"message": "Failed to add book due to a database error.", "action": "add", "success": False}


def _delete_book(data: dict) -> dict:
    title = data.get("title", "").strip()
    if not title:
        return {"message": "Book title is required to delete.", "action": "delete", "success": False}

    try:
        conn = get_db_connection(MAIN_DB)
        existing = conn.execute(
            "SELECT id, title FROM Books WHERE LOWER(title) = LOWER(?)", (title,)
        ).fetchone()
        if not existing:
            conn.close()
            return {"message": f'No book found with title "{title}".', "action": "delete", "success": False}
        conn.execute("DELETE FROM Books WHERE id = ?", (existing["id"],))
        conn.commit()
        conn.close()
        logger.info("[Chat] Book deleted: title=%r", title)
        return {
            "message": f'Book "{existing["title"]}" deleted successfully.',
            "action": "delete",
            "success": True,
            "data": {"title": existing["title"]},
        }
    except Exception as exc:
        logger.error("chat delete_book error: %s", exc)
        return {"message": "Failed to delete book due to a database error.", "action": "delete", "success": False}


def _update_book(data: dict) -> dict:
    title = data.get("title", "").strip()
    if not title:
        return {"message": "Book title is required to update.", "action": "update", "success": False}

    try:
        conn = get_db_connection(MAIN_DB)
        existing = conn.execute(
            "SELECT * FROM Books WHERE LOWER(title) = LOWER(?)", (title,)
        ).fetchone()
        if not existing:
            conn.close()
            return {"message": f'No book found with title "{title}".', "action": "update", "success": False}

        new_author = data.get("author", existing["author"])
        new_category = data.get("category", existing["category"])
        try:
            new_copies = int(data.get("copies", existing["total_copies"]))
        except (TypeError, ValueError):
            new_copies = existing["total_copies"]

        # Ensure at least one field is actually changing
        if (new_author == existing["author"] and
                new_category == existing["category"] and
                new_copies == existing["total_copies"]):
            conn.close()
            return {
                "message": (
                    f'No changes detected for "{existing["title"]}". '
                    "Please specify what you'd like to update (author, category, or copies)."
                ),
                "action": "update",
                "success": False,
            }

        diff = new_copies - existing["total_copies"]
        new_available = max(0, existing["available_copies"] + diff)

        conn.execute(
            "UPDATE Books SET author = ?, category = ?, total_copies = ?, available_copies = ? WHERE id = ?",
            (new_author, new_category, new_copies, new_available, existing["id"]),
        )
        conn.commit()
        conn.close()
        logger.info("[Chat] Book updated: title=%r", title)
        return {
            "message": f'Book "{existing["title"]}" updated successfully.',
            "action": "update",
            "success": True,
            "data": {"title": existing["title"], "author": new_author, "category": new_category, "copies": new_copies},
        }
    except Exception as exc:
        logger.error("chat update_book error: %s", exc)
        return {"message": "Failed to update book due to a database error.", "action": "update", "success": False}


def _issue_book(data: dict) -> dict:
    from datetime import date, timedelta
    
    title = data.get("title", "").strip()
    student_id = data.get("student_id")
    
    if not title:
        return {"message": "Book title is required to issue a book.", "action": "issue", "success": False}
    
    if student_id is None:
        return {"message": "Student ID is required to issue a book.", "action": "issue", "success": False}
    
    try:
        student_id = int(student_id)
    except (TypeError, ValueError):
        return {"message": "Invalid student ID format.", "action": "issue", "success": False}

    try:
        conn = get_db_connection(MAIN_DB)
        
        # Find the book
        book = conn.execute(
            "SELECT id, title, available_copies FROM Books WHERE LOWER(title) = LOWER(?)", (title,)
        ).fetchone()
        
        if not book:
            conn.close()
            return {"message": f'No book found with title "{title}".', "action": "issue", "success": False}
        
        if book["available_copies"] < 1:
            conn.close()
            return {"message": f'No copies available for "{book["title"]}".', "action": "issue", "success": False}
        
        # Check if student exists
        student = conn.execute("SELECT id FROM Students WHERE id = ?", (student_id,)).fetchone()
        if not student:
            conn.close()
            return {"message": f'Student with ID {student_id} not found.', "action": "issue", "success": False}
        
        # Issue the book using same logic as API
        issue_date = date.today().isoformat()
        due_date = (date.today() + timedelta(days=14)).isoformat()
        
        conn.execute(
            "INSERT INTO Issued (student_id, book_id, issue_date, due_date, status) VALUES (?, ?, ?, ?, 'Issued')",
            (student_id, book["id"], issue_date, due_date)
        )
        conn.execute(
            "UPDATE Books SET available_copies = available_copies - 1 WHERE id = ?", (book["id"],)
        )
        conn.commit()
        conn.close()
        
        logger.info("[Chat] Book issued: title=%r, student_id=%d", title, student_id)
        return {
            "message": f'Book "{book["title"]}" issued to student {student_id} successfully!',
            "action": "issue",
            "success": True,
            "data": {"title": book["title"], "student_id": student_id, "due_date": due_date},
        }
    except Exception as exc:
        logger.error("chat issue_book error: %s", exc)
        return {"message": "Failed to issue book due to a database error.", "action": "issue", "success": False}


# ---------------------------------------------------------------------------
# Clarification flow helpers
# ---------------------------------------------------------------------------

def _next_missing_field(intent: str, data: dict) -> Optional[str]:
    """Return the first required field that has not yet been collected."""
    for field in _REQUIRED.get(intent, []):
        if not data.get(field):
            return field
    return None


def _format_question(field: str, data: dict) -> str:
    q = _CLARIFICATION_QUESTIONS.get(field, f"Please provide the {field}:")
    return q.format(**data)


def _absorb_answer(answer: str, pending_field: str, data: dict) -> dict:
    """Store the user's plain answer into the correct field in data."""
    answer = answer.strip()
    skip_words = {"skip", "none", "n/a", "-", ""}

    if pending_field == "title":
        # Normalise spaces and strip leading action phrases if user re-stated the full command
        answer = _normalize_spaces(answer)
        clean = re.sub(
            r"^(add|insert|create|delete|remove|update|change|edit|view|show|list|get|new)"
            r"( a| the| an)? book ?",
            "",
            answer,
            flags=re.IGNORECASE,
        ).strip()
        # Also handle "by AUTHOR" if provided together with title in the answer
        lower = clean.lower()
        by_idx = lower.find(" by ")
        if by_idx != -1:
            data["title"] = clean[:by_idx].strip().strip('"').strip("'")
            if not data.get("author"):
                data["author"] = clean[by_idx + 4:].strip().strip('"').strip("'")
        elif clean:
            data["title"] = clean.strip('"').strip("'")
    elif pending_field in ("copies",):
        if answer.lower() in skip_words:
            data["copies"] = 1
        else:
            try:
                data["copies"] = int(re.sub(r"[^\d]", "", answer) or "1")
            except ValueError:
                data["copies"] = 1
    elif pending_field in ("category",):
        data["category"] = "" if answer.lower() in skip_words else answer
    else:
        if answer.lower() not in {"skip", "n/a", "-"}:
            data[pending_field] = answer
    return data


# ---------------------------------------------------------------------------
# Main chat endpoint
# ---------------------------------------------------------------------------

@require_roles("Librarian", "Administrator")
def chat():
    """
    Process a chat message and return a structured JSON response.
    
    Enhanced with improved intent recognition and ambiguity detection.
    
    Request body: { "message": "<user text>" }
    """
    body = request.get_json(silent=True) or {}
    user_text = (body.get("message") or "").strip()[:500]  # truncate to prevent ReDoS

    logger.debug("[Chat] User input: %r", user_text)

    if not user_text:
        return jsonify({"message": "Please type or say something.", "action": None})

    # Import enhanced chatbot
    from enhanced_chatbot import process_enhanced_query
    
    # Use enhanced query processing
    result = process_enhanced_query(user_text)
    
    # Add session management for context
    if result.get("status") == "success":
        session["last_query"] = user_text
        session["last_result"] = result.get("data", [])
    
    logger.debug("[Chat] Enhanced result: %r", result)
    session.pop("chat_data", None)
    session.pop("chat_pending_field", None)
    return jsonify(result)

    # ── Handle show_available queries ─────────────────────────────────────
    if current_intent == "show_available":
        result = _show_available_books(collected_data)
        session.pop("chat_intent", None)
        session.pop("chat_data", None)
        session.pop("chat_pending_field", None)
        return jsonify(result)

    # ── view_books – execute immediately ─────────────────────────────────────
    if current_intent == "view_books":
        session.pop("chat_intent", None)
        session.pop("chat_data", None)
        session.pop("chat_pending_field", None)
        return jsonify(_view_books())

    # ── Check for missing required fields ────────────────────────────────────
    missing = _next_missing_field(current_intent, collected_data)
    if missing:
        session["chat_intent"] = current_intent
        session["chat_data"] = collected_data
        session["chat_pending_field"] = missing
        question = _format_question(missing, collected_data)
        return jsonify({"message": question, "action": "clarify", "field": missing})

    # ── add_book – ask for optional fields if needed ─────────────────────
    if current_intent == "add_book":
        for opt in _ADD_OPTIONAL:
            if opt not in collected_data:
                session["chat_intent"] = current_intent
                session["chat_data"] = collected_data
                session["chat_pending_field"] = opt
                question = _format_question(opt, collected_data)
                return jsonify({"message": question, "action": "clarify", "field": opt})

    # ── delete requires confirmation ──────────────────────────────────────────
    if current_intent == "delete_book" and not session.get("chat_confirmed"):
        title = collected_data.get("title", "this book")
        session["chat_intent"] = current_intent
        session["chat_data"] = collected_data
        session["chat_pending_field"] = "confirm_delete"
        return jsonify({
            "message": f'Are you sure you want to delete "{title}"? (yes/no)',
            "action": "clarify",
            "field": "confirm_delete",
        })

    # ── Execute operation ─────────────────────────────────────────────────
    if current_intent == "add_book":
        result = _add_book(collected_data)
    elif current_intent == "delete_book":
        result = _delete_book(collected_data)
    elif current_intent == "update_book":
        result = _update_book(collected_data)
    elif current_intent == "issue_book":
        result = _issue_book(collected_data)
    elif current_intent == "return_book":
        result = _return_book(collected_data)
    else:
        result = {"message": "Unknown intent.", "action": None}

    # Clear session state after execution
    session.pop("chat_intent", None)
    session.pop("chat_data", None)
    session.pop("chat_pending_field", None)
    session.pop("chat_confirmed", None)

    return jsonify(result)


@chat_bp.route("/chat/reset", methods=["POST"])
@require_roles("Librarian", "Administrator")
def chat_reset():
    """Clear any pending chatbot conversation state."""
    session.pop("chat_intent", None)
    session.pop("chat_data", None)
    session.pop("chat_pending_field", None)
    session.pop("chat_confirmed", None)
    return jsonify({"message": "Conversation reset.", "action": "reset"})
