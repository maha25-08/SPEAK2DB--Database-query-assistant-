import sqlite3

try:
    conn = sqlite3.connect('library_main.db')
    cursor = conn.cursor()
    
    # Check if Students table has department column
    cursor.execute('PRAGMA table_info(Students)')
    columns = cursor.fetchall()
    print('Students table columns:')
    for col in columns:
        print(f'  {col[1]} ({col[2]})')
    
    # Check a sample student record to see what columns exist
    cursor.execute('SELECT * FROM Students LIMIT 1')
    student = cursor.fetchone()
    print('\nSample student record:')
    if student:
        # Get column names from the result
        cursor.execute('PRAGMA table_info(Students)')
        column_names = [col[1] for col in cursor.fetchall()]
        
        # Print student data with column names
        for i, value in enumerate(student):
            if i < len(column_names):
                print(f'  {column_names[i]}: {value}')
    
    conn.close()
except Exception as e:
    print(f'Error: {e}')
