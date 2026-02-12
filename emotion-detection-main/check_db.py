import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Check if table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
table = cursor.fetchone()
if table:
    print("User table exists")
    # Check columns
    cursor.execute("PRAGMA table_info(user)")
    columns = cursor.fetchall()
    print("Columns:", [col[1] for col in columns])
else:
    print("User table does not exist")

conn.close()
