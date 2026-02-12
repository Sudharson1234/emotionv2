import sqlite3

def add_missing_columns():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Check existing columns in user table
    cursor.execute("PRAGMA table_info(user)")
    columns = [row[1] for row in cursor.fetchall()]

    # Add created_at if missing
    if 'created_at' not in columns:
        try:
            cursor.execute("ALTER TABLE user ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
            print("Added created_at column")
        except sqlite3.OperationalError as e:
            print(f"Error adding created_at: {e}")

    # Add last_login if missing
    if 'last_login' not in columns:
        try:
            cursor.execute("ALTER TABLE user ADD COLUMN last_login DATETIME")
            print("Added last_login column")
        except sqlite3.OperationalError as e:
            print(f"Error adding last_login: {e}")

    # Add is_active if missing
    if 'is_active' not in columns:
        try:
            cursor.execute("ALTER TABLE user ADD COLUMN is_active BOOLEAN DEFAULT 1")
            print("Added is_active column")
        except sqlite3.OperationalError as e:
            print(f"Error adding is_active: {e}")

    conn.commit()
    conn.close()
    print("Database update complete")

if __name__ == '__main__':
    add_missing_columns()
