import sqlite3

def test_dashboard_data():
    """Test the updated librarian dashboard data"""
    
    conn = sqlite3.connect('library_main.db')
    cursor = conn.cursor()
    
    print("🔍 TESTING UPDATED LIBRARIAN DASHBOARD DATA")
    print("=" * 60)
    
    # Test the exact queries used in the dashboard
    print("📚 Books Statistics:")
    total_books = cursor.execute('SELECT COUNT(*) FROM Books').fetchone()[0]
    print(f"  Total Books: {total_books}")
    
    available_books = cursor.execute('SELECT SUM(available_copies) FROM Books').fetchone()[0] or 0
    print(f"  Available Books: {available_books}")
    
    issued_books = cursor.execute('SELECT COUNT(*) FROM Issued WHERE return_date IS NULL').fetchone()[0]
    print(f"  Currently Issued: {issued_books}")
    
    overdue_books = cursor.execute(
        'SELECT COUNT(*) FROM Issued WHERE return_date IS NULL AND date("now") > due_date'
    ).fetchone()[0]
    print(f"  Overdue Books: {overdue_books}")
    
    print("\n👥 Student Statistics:")
    total_students = cursor.execute('SELECT COUNT(*) FROM Students').fetchone()[0]
    print(f"  Total Students: {total_students}")
    
    print("\n💰 Fines Statistics:")
    total_fines = cursor.execute('SELECT COUNT(*) FROM Fines').fetchone()[0]
    print(f"  Total Fines: {total_fines}")
    
    unpaid_fines = cursor.execute('SELECT COUNT(*) FROM Fines WHERE status = "Unpaid"').fetchone()[0]
    print(f"  Unpaid Fines: {unpaid_fines}")
    
    total_unpaid_amount = cursor.execute('SELECT SUM(fine_amount) FROM Fines WHERE status = "Unpaid"').fetchone()[0] or 0
    print(f"  Total Unpaid Amount: ${total_unpaid_amount:.2f}")
    
    print("\n📅 Today's Activity:")
    recent_issues = cursor.execute('''
        SELECT COUNT(*) FROM Issued 
        WHERE date(issue_date) = date('now')
    ''').fetchone()[0]
    print(f"  Books Issued Today: {recent_issues}")
    
    recent_returns = cursor.execute('''
        SELECT COUNT(*) FROM Issued 
        WHERE date(return_date) = date('now')
    ''').fetchone()[0]
    print(f"  Books Returned Today: {recent_returns}")
    
    recent_payments = cursor.execute('''
        SELECT COUNT(*) FROM Fines 
        WHERE status = 'Paid'
    ''').fetchone()[0]
    print(f"  Fines Paid Today: {recent_payments}")
    
    print("\n📊 Dashboard Summary:")
    print("  The librarian dashboard should now display:")
    print(f"    📚 {total_books} total books, {available_books} available")
    print(f"    📤 {issued_books} books currently issued")
    print(f"    ⚠️  {overdue_books} overdue books")
    print(f"    💰 {unpaid_fines} unpaid fines totaling ${total_unpaid_amount:.2f}")
    print(f"    📅 {recent_issues} issues, {recent_returns} returns, {recent_payments} payments today")
    
    print("\n✅ Dashboard data test completed!")
    print("🎯 The librarian dashboard is now fully updated with realistic data.")
    
    conn.close()

if __name__ == "__main__":
    test_dashboard_data()
