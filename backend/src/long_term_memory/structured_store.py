# memory_sql_store.py
import sqlite3
from datetime import datetime
import uuid

class StructuredMemoryStore:
    def __init__(self, db_path="backend/src/long_term_memory/structured_memory.db", reset_on_init=False):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
        if reset_on_init:
            self.clear_all()
            
    def clear_all(self):
        self.conn.execute("DELETE FROM memories")
        self.conn.commit()
        
    def save(self, memory_id: str = None, content: str = "", tags=None):
        if not memory_id:
            memory_id = str(uuid.uuid4())
        tags_str = ",".join(tags or [])
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # local time

        self.conn.execute(
            "INSERT OR REPLACE INTO memories (id, content, tags, created_at) VALUES (?, ?, ?, ?)",
            (memory_id, content, tags_str, timestamp)
        )
        self.conn.commit()

    def search_by_content(self, keyword: str):
        cursor = self.conn.execute(
            "SELECT id, content, tags, created_at FROM memories WHERE content LIKE ?",
            (f"%{keyword}%",)
        )
        return cursor.fetchall()
    
    def search_by_tag(self, tag: str):
        cursor = self.conn.execute(
            "SELECT id, content, tags, created_at FROM memories WHERE tags LIKE ?",
            (f"%{tag}%",)
        )
        return cursor.fetchall()

    def list_all(self):
        cursor = self.conn.execute("SELECT * FROM memories ORDER BY created_at DESC")
        return cursor.fetchall()
    

if __name__ == "__main__":
    # Structured DB
    sql_store = StructuredMemoryStore(reset_on_init=True)
    sql_store.save(content="Martha's yoga class takes place every monday at 12.00 pm", tags=["sports"])
    sql_store.save(content="Martha loves yoga.", tags=["interest", "sports"])
    sql_store.save(content="Martha hates football.", tags=["interest", "sports"])
    sql_store.save(content="Martha is 27 years old.", tags=["user_info", "age"])
    sql_store.save(content="Martha is a software engineer.", tags=["user_info", "occupation"])
    sql_store.save(content="Martha's favorite color is blue.", tags=["user_info", "preferences", "color"])


    for row in sql_store.list_all():
        print(row)
        
    print("\nInterest Memories:")
    for memory in sql_store.search_by_tag("interest"):
        print(memory)

    print("\nYoga Memories:")
    for memory in sql_store.search_by_content("yoga"):
        print(memory)