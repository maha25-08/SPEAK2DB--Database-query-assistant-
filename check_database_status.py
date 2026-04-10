import sqlite3
import os

try:
    # Check if database file exists
    db_path = 'library_main.db'
    if os.path.exists(db_path):
        print(f'Database file exists: {db_path}')
        print(f'Database size: {os.path.getsize(db_path)} bytes')
    else:
        print(f'Database file does not exist: {db_path}')
        exit(1)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f'\nTotal tables found: {len(tables)}')
    
    if not tables:
        print('No tables found - database may be empty')
        exit(1)
    
    print('Tables in database:')
    for table in tables:
        print(f'  {table[0]}')
        
        # Get row count for each table
        try:
            cursor.execute(f'SELECT COUNT(*) FROM {table[0]}')
            count = cursor.fetchone()[0]
            print(f'    Rows: {count}')
        except:
            print(f'    Could not get row count')
    
    # Try to find book-related data
    print('\nSearching for book-related data...')
    for table in tables:
        table_name = table[0].lower()
        if 'book' in table_name:
            print(f'Found book table: {table[0]}')
            cursor.execute(f'PRAGMA table_info({table[0]})')
            columns = cursor.fetchall()
            print(f'  Columns: {[col[1] for col in columns]}')
            
            # Get sample data
            try:
                cursor.execute(f'SELECT * FROM {table[0]} LIMIT 1')
                sample = cursor.fetchone()
                if sample:
                    print(f'  Sample data: {sample}')
            except:
                print(f'  Could not get sample data')
    
    conn.close()
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
