import sqlite3

try:
    conn = sqlite3.connect('library_main.db')
    cursor = conn.cursor()
    
    # Test the query "what are the books with highest cost"
    print("🔍 Testing query: 'what are the books with highest cost'")
    
    # Find books with highest cost
    cursor.execute('''
        SELECT title, author, price FROM Books 
        ORDER BY price DESC 
        LIMIT 5
    ''')
    
    expensive_books = cursor.fetchall()
    
    print("\n📚 Top 5 Most Expensive Books:")
    if expensive_books:
        for i, book in enumerate(expensive_books, 1):
            print(f"{i}. {book[0]} by {book[1]} - ${book[2]:.2f}")
    else:
        print("No books found")
    
    # Test another query - all books
    print("\n📚 All Books in Database:")
    cursor.execute('SELECT title, author, price FROM Books ORDER BY title')
    all_books = cursor.fetchall()
    
    for book in all_books:
        print(f"  - {book[0]} by {book[1]} - ${book[2]:.2f}")
    
    conn.close()
    print("\n✅ Query test completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
