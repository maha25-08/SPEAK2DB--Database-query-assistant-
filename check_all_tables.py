import sqlite3

try:
    conn = sqlite3.connect('library_main.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print('All tables in database:')
    for table in tables:
        print(f'  {table[0]}')
    
    # Check if there are any book-related tables
    print('\nBook-related tables:')
    for table in tables:
        table_name = table[0].lower()
        if 'book' in table_name:
            print(f'  Found: {table[0]}')
            # Get columns for this table
            cursor.execute(f'PRAGMA table_info({table[0]})')
            columns = cursor.fetchall()
            print(f'    Columns:')
            for col in columns:
                print(f'      {col[1]} ({col[2]})')
    
    conn.close()
    
except Exception as e:
    print(f'Error: {e}')
