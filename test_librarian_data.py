import sqlite3

def test_librarian_data():
    """Test the librarian demo data"""
    
    conn = sqlite3.connect('library_main.db')
    cursor = conn.cursor()
    
    print("🔍 TESTING LIBRARIAN DEMO DATA")
    print("=" * 50)
    
    # Test Books
    print("📚 Sample Books:")
    cursor.execute('SELECT id, title, author, category, total_copies, available_copies FROM Books LIMIT 5')
    books = cursor.fetchall()
    for book in books:
        print(f"  [{book[0]}] {book[1]} by {book[2]} ({book[3]}) - Total: {book[4]}, Available: {book[5]}")
    
    # Test Issued Books
    print("\n📤 Sample Issued Books:")
    cursor.execute('''
        SELECT i.id, s.name, s.roll_number, b.title, i.issue_date, i.due_date, i.return_date
        FROM Issued i
        JOIN Students s ON i.student_id = s.id
        JOIN Books b ON i.book_id = b.id
        LIMIT 8
    ''')
    issued = cursor.fetchall()
    for record in issued:
        return_status = record[6] if record[6] else "Not Returned"
        print(f"  [{record[0]}] {record[3]} issued to {record[1]} ({record[2]})")
        print(f"      Issued: {record[4]}, Due: {record[5]}, Status: {return_status}")
    
    # Test Overdue Books
    print("\n⚠️  Overdue Books:")
    cursor.execute('''
        SELECT i.id, s.name, s.roll_number, b.title, i.due_date
        FROM Issued i
        JOIN Students s ON i.student_id = s.id
        JOIN Books b ON i.book_id = b.id
        WHERE i.return_date IS NULL AND date(i.due_date) < date('now')
    ''')
    overdue = cursor.fetchall()
    for record in overdue:
        print(f"  [{record[0]}] {record[3]} - {record[1]} ({record[2]})")
        print(f"      Due: {record[4]} - OVERDUE!")
    
    # Test Fines
    print("\n💰 Sample Fines:")
    cursor.execute('''
        SELECT f.id, s.name, s.roll_number, f.fine_amount, f.fine_type, f.status, f.issue_date
        FROM Fines f
        JOIN Students s ON f.student_id = s.id
        ORDER BY f.status, f.issue_date DESC
        LIMIT 8
    ''')
    fines = cursor.fetchall()
    for fine in fines:
        status_color = "🔴" if fine[5] == "Unpaid" else "🟢"
        print(f"  [{fine[0]}] {status_color} ${fine[3]:.2f} - {fine[1]} ({fine[2]})")
        print(f"      Type: {fine[4]}, Status: {fine[5]}, Date: {fine[6]}")
    
    # Test Unpaid Fines Summary
    print("\n📊 Unpaid Fines Summary:")
    cursor.execute('''
        SELECT COUNT(*) as count, SUM(fine_amount) as total
        FROM Fines WHERE status = 'Unpaid'
    ''')
    unpaid_summary = cursor.fetchone()
    print(f"  Total Unpaid Fines: {unpaid_summary[0]}")
    print(f"  Total Amount Due: ${unpaid_summary[1]:.2f}")
    
    # Test Student with Most Fines
    print("\n👥 Students with Fines:")
    cursor.execute('''
        SELECT s.name, s.roll_number, COUNT(f.id) as fine_count, SUM(f.fine_amount) as total_amount
        FROM Students s
        LEFT JOIN Fines f ON s.id = f.student_id
        WHERE f.status = 'Unpaid'
        GROUP BY s.id, s.name, s.roll_number
        HAVING fine_count > 0
        ORDER BY total_amount DESC
    ''')
    students_with_fines = cursor.fetchall()
    for student in students_with_fines:
        print(f"  {student[0]} ({student[1]}): {student[2]} fines, ${student[3]:.2f} total")
    
    # Test Books Availability
    print("\n📊 Books Availability:")
    cursor.execute('''
        SELECT category, 
               COUNT(*) as total_books,
               SUM(total_copies) as total_copies,
               SUM(available_copies) as available_copies
        FROM Books
        GROUP BY category
        ORDER BY total_books DESC
    ''')
    categories = cursor.fetchall()
    for cat in categories:
        utilization = ((cat[2] - cat[3]) / cat[2] * 100) if cat[2] > 0 else 0
        print(f"  {cat[0]}: {cat[1]} titles, {cat[3]}/{cat[2]} copies available ({utilization:.1f}% utilized)")
    
    print("\n✅ Librarian data test completed!")
    print("🎯 The librarian dashboard should now show realistic data for testing.")
    
    conn.close()

if __name__ == "__main__":
    test_librarian_data()
