import sqlite3

conn = sqlite3.connect('library_main.db')
cursor = conn.cursor()

print("🔍 CHECKING DATABASE SCHEMA")
print("=" * 50)

# Check Books table structure
print("📚 Books table structure:")
cursor.execute('PRAGMA table_info(Books)')
books_columns = cursor.fetchall()
for col in books_columns:
    print(f"  {col[1]} ({col[2]})")

print("\n👥 Students table structure:")
cursor.execute('PRAGMA table_info(Students)')
students_columns = cursor.fetchall()
for col in students_columns:
    print(f"  {col[1]} ({col[2]})")

print("\n📤 Issued table structure:")
cursor.execute('PRAGMA table_info(Issued)')
issued_columns = cursor.fetchall()
for col in issued_columns:
    print(f"  {col[1]} ({col[2]})")

print("\n💰 Fines table structure:")
cursor.execute('PRAGMA table_info(Fines)')
fines_columns = cursor.fetchall()
for col in fines_columns:
    print(f"  {col[1]} ({col[2]})")

conn.close()
