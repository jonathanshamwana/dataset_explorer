import sqlite3

def init_db():
    conn = sqlite3.connect('images.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS images (
            filename TEXT PRIMARY KEY,
            status TEXT DEFAULT 'all'
        )
    ''')
    conn.commit()
    conn.close()