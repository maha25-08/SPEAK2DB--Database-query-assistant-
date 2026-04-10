#!/usr/bin/env python3
"""
Initialize the library database with basic tables and sample data.
"""

import sqlite3
import os
from datetime import datetime

def create_database_schema():
    """Create the basic database schema for the library system."""
    db_path = 'library_main.db'
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🗄️ Creating database schema...")
    
    # Create Books table
    cursor.execute('''
        CREATE TABLE Books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT UNIQUE,
            publisher_id INTEGER,
            total_copies INTEGER DEFAULT 1,
            available_copies INTEGER DEFAULT 1,
            category TEXT,
            publication_year INTEGER,
            price REAL,
            created_date TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ Created Books table")
    
    # Create Students table
    cursor.execute('''
        CREATE TABLE Students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_number TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            branch TEXT,
            year TEXT,
            email TEXT UNIQUE,
            phone TEXT,
            role TEXT DEFAULT 'Student',
            gpa REAL DEFAULT 0.0,
            attendance INTEGER DEFAULT 0,
            created_date TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ Created Students table")
    
    # Create Issued table
    cursor.execute('''
        CREATE TABLE Issued (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            issue_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            return_date TEXT,
            FOREIGN KEY (student_id) REFERENCES Students(id),
            FOREIGN KEY (book_id) REFERENCES Books(id)
        )
    ''')
    print("✅ Created Issued table")
    
    # Create Fines table
    cursor.execute('''
        CREATE TABLE Fines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            fine_amount REAL NOT NULL,
            fine_type TEXT DEFAULT 'Overdue',
            status TEXT DEFAULT 'Unpaid',
            issue_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES Students(id)
        )
    ''')
    print("✅ Created Fines table")
    
    # Create Users table for authentication
    cursor.execute('''
        CREATE TABLE Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            email TEXT UNIQUE,
            created_date TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ Created Users table")
    
    # Create ActivityLogs table
    cursor.execute('''
        CREATE TABLE ActivityLogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            action TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ Created ActivityLogs table")
    
    conn.commit()
    conn.close()
    print("🎉 Database schema created successfully!")

def insert_sample_data():
    """Insert sample data into the database."""
    conn = sqlite3.connect('library_main.db')
    cursor = conn.cursor()
    
    print("\n📚 Inserting sample data...")
    
    # Insert sample books
    books = [
        ("Introduction to Algorithms", "Thomas H. Cormen", "978-0262033844", 1, 5, 3, "Computer Science", 2009, 89.99),
        ("Data Structures and Algorithms", "Mark Allen Weiss", "978-0132576277", 1, 4, 2, "Computer Science", 2012, 124.99),
        ("Database System Concepts", "Abraham Silberschatz", "978-0073523323", 1, 3, 1, "Computer Science", 2010, 156.99),
        ("Operating System Concepts", "Abraham Silberschatz", "978-0470128725", 1, 2, 0, "Computer Science", 2014, 189.99),
        ("Computer Networks", "Andrew S. Tanenbaum", "978-0132126958", 1, 4, 2, "Computer Science", 2010, 134.99),
        ("Digital Logic Design", "M. Morris Mano", "978-0131984260", 1, 3, 1, "Electronics", 2013, 199.99),
        ("Mechanical Engineering", "Hannah, R.C. & Stephens, R.C.", "978-0136074488", 1, 2, 1, "Mechanical", 2015, 224.99),
        ("Civil Engineering Materials", "Nevil, A.M. & Brooks, J.J.", "978-02737535401", 1, 1, 0, "Civil", 2010, 179.99),
        ("Business Statistics", "Anderson, D.R. & Sweeney, D.J.", "978-1111524915", 1, 2, 1, "Business", 2014, 89.99),
        ("General Mathematics", "Howard Anton", "978-0470458365", 1, 5, 3, "General", 2010, 159.99)
    ]
    
    cursor.executemany('''
        INSERT INTO Books (title, author, isbn, publisher_id, total_copies, available_copies, category, publication_year, price)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', books)
    print(f"✅ Inserted {len(books)} books")
    
    # Insert sample students
    students = [
        ("MT3001", "Alice Johnson", "Computer Science", "3", "alice@univ.in", "9876543210"),
        ("MT3002", "Bob Smith", "Electronics", "2", "bob@univ.in", "9876543211"),
        ("MT3003", "Charlie Brown", "Mechanical", "4", "charlie@univ.in", "9876543212"),
        ("MT3004", "Diana Wilson", "Civil", "3", "diana@univ.in", "9876543213"),
        ("MT3005", "Eva Davis", "Business", "2", "eva@univ.in", "9876543214")
    ]
    
    cursor.executemany('''
        INSERT INTO Students (roll_number, name, branch, year, email, phone)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', students)
    print(f"✅ Inserted {len(students)} students")
    
    # Insert sample users (librarians and students)
    users = [
        ("librarian", "hashed_password_123", "Librarian", "librarian@library.in"),
        ("admin", "hashed_password_456", "Admin", "admin@library.in"),
        ("MT3001", "hashed_password_789", "Student", "alice@univ.in")
    ]
    
    cursor.executemany('''
        INSERT INTO Users (username, password, role, email)
        VALUES (?, ?, ?, ?)
    ''', users)
    print(f"✅ Inserted {len(users)} users")
    
    # Insert some issued books
    issued = [
        (1, 1, "2026-03-15", "2026-03-29", None),  # Alice issued Algorithms
        (2, 2, "2026-03-10", "2026-03-24", None),  # Bob issued Data Structures
        (3, 3, "2026-03-20", "2026-04-03", None),  # Charlie issued Database Concepts
    ]
    
    cursor.executemany('''
        INSERT INTO Issued (student_id, book_id, issue_date, due_date, return_date)
        VALUES (?, ?, ?, ?, ?)
    ''', issued)
    print(f"✅ Inserted {len(issued)} issued books")
    
    # Insert some fines
    fines = [
        (3, 10.00, "Overdue", "Unpaid", "2026-04-01"),  # Charlie overdue
        (4, 15.00, "Damaged", "Unpaid", "2026-03-25"),  # Diana damaged book
        (1, 5.00, "Late Return", "Paid", "2026-03-28"),  # Alice paid fine
    ]
    
    cursor.executemany('''
        INSERT INTO Fines (student_id, fine_amount, fine_type, status, issue_date)
        VALUES (?, ?, ?, ?, ?)
    ''', fines)
    print(f"✅ Inserted {len(fines)} fines")
    
    conn.commit()
    conn.close()
    print("🎉 Sample data inserted successfully!")

if __name__ == "__main__":
    print("🚀 Initializing Library Database")
    print("=" * 50)
    
    create_database_schema()
    insert_sample_data()
    
    print("\n📊 Database Summary:")
    print("  - Books table: 10 sample books")
    print("  - Students table: 5 sample students")
    print("  - Users table: 3 users (librarian, admin, student)")
    print("  - Issued table: 3 issued books")
    print("  - Fines table: 3 fines (2 unpaid, 1 paid)")
    print("\n✅ Database is ready for use!")
    print("🔐 Login credentials:")
    print("  Librarian: librarian / password123")
    print("  Admin: admin / password456")
    print("  Student: MT3001 / password789")
