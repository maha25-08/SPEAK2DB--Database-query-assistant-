import sqlite3
from datetime import datetime, timedelta
import random

def populate_librarian_data():
    """Populate database with sample data for librarian operations"""
    
    conn = sqlite3.connect('library_main.db')
    cursor = conn.cursor()
    
    print("📚 POPULATING LIBRARIAN DEMO DATA")
    print("=" * 50)
    
    # Sample books data
    books_data = [
        ("The Great Gatsby", "F. Scott Fitzgerald", "Fiction", 1, 5, 3),
        ("To Kill a Mockingbird", "Harper Lee", "Fiction", 1, 3, 2),
        ("1984", "George Orwell", "Science Fiction", 1, 4, 2),
        ("Pride and Prejudice", "Jane Austen", "Romance", 1, 2, 1),
        ("The Catcher in the Rye", "J.D. Salinger", "Fiction", 1, 3, 1),
        ("Animal Farm", "George Orwell", "Political Fiction", 1, 6, 4),
        ("Brave New World", "Aldous Huxley", "Science Fiction", 1, 4, 2),
        ("The Hobbit", "J.R.R. Tolkien", "Fantasy", 1, 7, 5),
        ("Harry Potter and the Sorcerer's Stone", "J.K. Rowling", "Fantasy", 1, 8, 6),
        ("The Da Vinci Code", "Dan Brown", "Mystery", 1, 5, 3),
        ("The Alchemist", "Paulo Coelho", "Fiction", 1, 4, 2),
        ("The Little Prince", "Antoine de Saint-Exupéry", "Fiction", 1, 3, 2),
        ("The Kite Runner", "Khaled Hosseini", "Fiction", 1, 2, 1),
        ("Life of Pi", "Yann Martel", "Adventure", 1, 3, 2),
        ("The Book Thief", "Markus Zusak", "Historical Fiction", 1, 4, 3),
        ("The Hunger Games", "Suzanne Collins", "Young Adult", 1, 6, 4),
        ("Divergent", "Veronica Roth", "Young Adult", 1, 5, 3),
        ("The Fault in Our Stars", "John Green", "Young Adult", 1, 4, 2),
        ("Wonder", "R.J. Palacio", "Children's Fiction", 1, 3, 2),
        ("The Giver", "Lois Lowry", "Young Adult", 1, 5, 4)
    ]
    
    # Insert books if they don't exist
    print("📖 Adding Books...")
    for book in books_data:
        cursor.execute('''
            INSERT OR IGNORE INTO Books (title, author, category, publisher_id, total_copies, available_copies)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', book)
    
    # Get book IDs for issuing
    cursor.execute('SELECT id, title FROM Books ORDER BY id LIMIT 10')
    books = cursor.fetchall()
    
    # Get student IDs for issuing
    cursor.execute('SELECT id, name, roll_number FROM Students ORDER BY id LIMIT 8')
    students = cursor.fetchall()
    
    if not books or not students:
        print("❌ No books or students found in database!")
        conn.close()
        return
    
    print(f"📚 Found {len(books)} books and {len(students)} students")
    
    # Clear existing issued records to avoid conflicts
    cursor.execute('DELETE FROM Issued')
    cursor.execute('DELETE FROM Fines')
    
    # Sample issued books data
    issued_data = []
    current_date = datetime.now()
    
    # Create some issued books (both returned and not returned)
    for i in range(15):
        student = random.choice(students)
        book = random.choice(books)
        issue_date = current_date - timedelta(days=random.randint(1, 30))
        due_date = issue_date + timedelta(days=14)
        
        # Some books are returned, some are not
        if i < 10:  # First 10 are returned
            return_date = issue_date + timedelta(days=random.randint(1, 20))
        else:  # Last 5 are not returned
            return_date = None
        
        issued_data.append((
            student[0],  # student_id
            book[0],     # book_id
            issue_date.strftime('%Y-%m-%d'),
            due_date.strftime('%Y-%m-%d'),
            return_date.strftime('%Y-%m-%d') if return_date else None
        ))
    
    # Insert issued books
    print("📤 Adding Issued Books...")
    for issued in issued_data:
        cursor.execute('''
            INSERT INTO Issued (student_id, book_id, issue_date, due_date, return_date)
            VALUES (?, ?, ?, ?, ?)
        ''', issued)
    
    # Get issued book IDs for creating fines
    cursor.execute('SELECT id, student_id, book_id, issue_date, return_date FROM Issued')
    issued_records = cursor.fetchall()
    
    # Create some fines (both paid and unpaid)
    fines_data = []
    for i, issued in enumerate(issued_records[:8]):  # Create fines for first 8 issued books
        issued_id, student_id, book_id, issue_date, return_date = issued
        
        # Create fines for overdue books
        if return_date:
            issue_dt = datetime.strptime(issue_date, '%Y-%m-%d')
            return_dt = datetime.strptime(return_date, '%Y-%m-%d')
            due_dt = issue_dt + timedelta(days=14)
            
            if return_dt > due_dt:  # Overdue
                days_overdue = (return_dt - due_dt).days
                fine_amount = days_overdue * 0.50  # $0.50 per day
                
                # Mix of paid and unpaid fines
                if i < 5:  # First 5 are paid
                    status = 'Paid'
                    payment_date = return_dt + timedelta(days=random.randint(1, 5))
                    payment_method = random.choice(['Cash', 'Card', 'Online'])
                else:  # Last 3 are unpaid
                    status = 'Unpaid'
                    payment_date = None
                    payment_method = None
                
                fines_data.append((
                    student_id,
                    fine_amount,
                    "Overdue",
                    status,
                    issue_dt.strftime('%Y-%m-%d')
                ))
        else:  # Not returned yet - create unpaid fine
            issue_dt = datetime.strptime(issue_date, '%Y-%m-%d')
            due_dt = issue_dt + timedelta(days=14)
            days_overdue = (current_date - due_dt).days
            
            if days_overdue > 0:
                fine_amount = days_overdue * 0.50
                fines_data.append((
                    student_id,
                    fine_amount,
                    "Overdue",
                    'Unpaid',
                    issue_dt.strftime('%Y-%m-%d')
                ))
    
    # Insert fines
    print("💰 Adding Fines...")
    for fine in fines_data:
        cursor.execute('''
            INSERT INTO Fines (student_id, fine_amount, fine_type, status, issue_date)
            VALUES (?, ?, ?, ?, ?)
        ''', fine)
    
    # Add some general fines (not tied to specific books)
    general_fines = [
        (students[0][0], 5.00, "Damage", 'Unpaid', (current_date - timedelta(days=10)).strftime('%Y-%m-%d')),
        (students[1][0], 2.50, "Late Return", 'Paid', (current_date - timedelta(days=5)).strftime('%Y-%m-%d')),
        (students[2][0], 7.50, "Lost Book", 'Unpaid', (current_date - timedelta(days=15)).strftime('%Y-%m-%d')),
    ]
    
    for fine in general_fines:
        cursor.execute('''
            INSERT INTO Fines (student_id, fine_amount, fine_type, status, issue_date)
            VALUES (?, ?, ?, ?, ?)
        ''', fine)
    
    conn.commit()
    
    # Display summary
    print("\n📊 DATA POPULATION SUMMARY")
    print("=" * 50)
    
    cursor.execute('SELECT COUNT(*) FROM Books')
    books_count = cursor.fetchone()[0]
    print(f"📚 Total Books: {books_count}")
    
    cursor.execute('SELECT COUNT(*) FROM Students')
    students_count = cursor.fetchone()[0]
    print(f"👥 Total Students: {students_count}")
    
    cursor.execute('SELECT COUNT(*) FROM Issued')
    issued_count = cursor.fetchone()[0]
    print(f"📤 Total Issued Records: {issued_count}")
    
    cursor.execute('SELECT COUNT(*) FROM Issued WHERE return_date IS NULL')
    not_returned_count = cursor.fetchone()[0]
    print(f"⏳ Books Not Returned: {not_returned_count}")
    
    cursor.execute('SELECT COUNT(*) FROM Fines')
    fines_count = cursor.fetchone()[0]
    print(f"💰 Total Fines: {fines_count}")
    
    cursor.execute('SELECT COUNT(*) FROM Fines WHERE status = "Unpaid"')
    unpaid_fines_count = cursor.fetchone()[0]
    print(f"⚠️  Unpaid Fines: {unpaid_fines_count}")
    
    cursor.execute('SELECT SUM(fine_amount) FROM Fines WHERE status = "Unpaid"')
    total_unpaid = cursor.fetchone()[0] or 0
    print(f"💸 Total Unpaid Amount: ${total_unpaid:.2f}")
    
    print("\n✅ Data population completed successfully!")
    print("🎯 You can now test the librarian dashboard with realistic data.")
    
    conn.close()

if __name__ == "__main__":
    populate_librarian_data()
