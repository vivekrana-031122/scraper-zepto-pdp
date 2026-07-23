import os
import sqlite3

class SQLiteCursorWrapper:
    """Wrapper that intercepts execute/executemany calls and converts %s to ? for SQLite compatibility."""
    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, query, params=None):
        query = query.replace("%s", "?").replace("`", "")
        return self.cursor.execute(query, params)

    def executemany(self, query, params=None):
        query = query.replace("%s", "?").replace("`", "")
        return self.cursor.executemany(query, params)

    def __getattr__(self, name):
        return getattr(self.cursor, name)

class SQLiteConnectionWrapper:
    """Wrapper for SQLite connection returning wrapped SQLiteCursorWrapper objects."""
    def __init__(self, conn):
        self.conn = conn

    def cursor(self):
        return SQLiteCursorWrapper(self.conn.cursor())

    def __getattr__(self, name):
        return getattr(self.conn, name)

class DBAction:
    """
    Sanitized Database Action helper.
    Connects to MySQL if environment variables are configured.
    Otherwise, automatically falls back to local SQLite database (sqlite3)
    to enable zero-configuration local execution and testing.
    """
    def db_connection(self, db_name=None, env=None):
        db_host = os.getenv("DB_HOST")
        db_user = os.getenv("DB_USER")
        db_pass = os.getenv("DB_PASSWORD")
        db_port = os.getenv("DB_PORT", "3306")
        db_database = os.getenv("DB_DATABASE", db_name or "scraper_db")
        
        if db_host and db_user:
            try:
                import pymysql
                print(f"Connecting to MySQL database '{db_database}' at {db_host}:{db_port}...")
                conn = pymysql.connect(
                    host=db_host,
                    user=db_user,
                    password=db_pass,
                    port=int(db_port),
                    database=db_database
                )
                return conn
            except Exception as e:
                print(f"Failed to connect to MySQL ({e}). Falling back to local SQLite.")

        # Local SQLite Fallback
        db_file = f"{db_database}.db"
        print(f"SQLite Fallback: Using local SQLite database file '{db_file}'...")
        conn = sqlite3.connect(db_file)
        
        # Automatically create necessary tables if they don't exist yet
        try:
            cursor = conn.cursor()
            if db_name == "zepto" or "zepto" in str(db_database).lower():
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS zepto_crawl_pdp (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pf_id TEXT, crawl_id TEXT, sku_id TEXT, web_pid TEXT, pdp_title_value TEXT,
                        brand_id TEXT, brand_name TEXT, price_rp TEXT, price_sp TEXT,
                        pdp_rating_value TEXT, pdp_review_count TEXT, pdp_rating_count TEXT,
                        pdp_qa_count TEXT, pdp_desc_value TEXT, pdp_image_count TEXT,
                        pdp_image_url TEXT, pdp_image_url_all TEXT, osa TEXT, osa_remark TEXT,
                        pdp_page_url TEXT, pdp_discount_value TEXT, location_id TEXT,
                        location_name TEXT, pincode TEXT, created_by TEXT, created_on TEXT, status TEXT
                    )
                """)
            elif db_name == "myntra" or "myntra" in str(db_database).lower():
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS myntra_crawl_pdp (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pf_id TEXT, crawl_id TEXT, sku_id TEXT, web_pid TEXT, pdp_title_value TEXT,
                        brand_id TEXT, brand_name TEXT, price_rp TEXT, price_sp TEXT,
                        pdp_rating_value TEXT, pdp_review_count TEXT, pdp_rating_count TEXT,
                        pdp_qa_count TEXT, pdp_desc_value TEXT, pdp_image_count TEXT,
                        pdp_image_url TEXT, pdp_image_url_all TEXT, osa TEXT, osa_remark TEXT,
                        pdp_page_url TEXT, pdp_discount_value TEXT, location_id TEXT,
                        location_name TEXT, pincode TEXT, created_by TEXT, created_on TEXT, status TEXT
                    )
                """)
            conn.commit()
        except Exception as err:
            print(f"Error creating table: {err}")
            
        return SQLiteConnectionWrapper(conn)
