import sqlite3

def init_db():
    conn = sqlite3.connect('images.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS images (
            filename TEXT PRIMARY KEY,
            duplicate INTEGER DEFAULT 0,
            status TEXT DEFAULT 'all',
            hash TEXT
        )
    ''')
    conn.commit()
    conn.close()