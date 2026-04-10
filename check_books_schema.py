import sqlite3

try:
    conn = sqlite3.connect('library_main.db')
    cursor = conn.cursor()
    
    # Check Books table structure
    cursor.execute('PRAGMA table_info(Books)')
    columns = cursor.fetchall()
    print('Books table columns:')
    for col in columns:
        print(f'  {col[1]} ({col[2]})')
    
    # Check sample books data to see what columns exist
    cursor.execute('SELECT * FROM Books LIMIT 3')
    books = cursor.fetchall()
    
    print('\nSample book records:')
    for book in books:
        print(f'  Book ID: {book[0]}, Title: {book[1]}')
        # Print all available data
        for i, col in enumerate(columns):
            if i < len(book):
                print(f'    {col[1]}: {book[i]}')
        print()
    
    conn.close()
    
except Exception as e:
    print(f'Error: {e}')
