# crawlerd_web/database.py
import sqlite3
import os

def get_db_path():
    """
    获取数据库路径。必须通过环境变量 CRAWLERD_DB_PATH 设置。
    """
    path = os.getenv("CRAWLERD_DB_PATH")
    if not path:
        raise RuntimeError(
            "CRITICAL ERROR: Database path is not configured.\n"
            "You must set the 'CRAWLERD_DB_PATH' environment variable or pass '--db-path' argument to start the application."
        )
    
    # 确保数据库文件的父目录存在
    db_dir = os.path.dirname(os.path.abspath(path))
    if db_dir and not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir, exist_ok=True)
        except OSError as e:
            raise RuntimeError(f"Failed to create directory for database at {db_dir}: {e}")
            
    return path

def get_db_connection():
    """建立并返回一个数据库连接对象"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    # 设置 Row Factory，这样查询结果可以像字典一样通过列名访问
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    """
    在数据库中创建所有必要的表（如果它们还不存在的话）。
    这个函数应该在应用启动时被调用。
    """
    print("Initializing database...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 开启外键约束支持
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 创建 'nodes' 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            alias TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # 尝试添加 alias 列（如果表已存在但没有该列）
    try:
        cursor.execute("ALTER TABLE nodes ADD COLUMN alias TEXT;")
    except sqlite3.OperationalError:
        # 列可能已存在
        pass

    print("Table 'nodes' is ready.")

    # 创建 'projects' 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    # 为 projects 表创建 updated_at 触发器
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_projects_updated_at
        AFTER UPDATE ON projects
        FOR EACH ROW
        BEGIN
            UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
        END;
    """)
    print("Table 'projects' is ready.")

    # 创建 'deployments' 表，连接 projects 和 nodes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deployments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            node_id INTEGER NOT NULL,
            initialized BOOLEAN NOT NULL DEFAULT 0,
            module_class_name TEXT,
            dataset_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
            FOREIGN KEY (node_id) REFERENCES nodes (id) ON DELETE CASCADE,
            UNIQUE (project_id, node_id)
        );
    """)
    
    # 尝试添加 dataset_name 列（针对已存在的表）
    try:
        cursor.execute("ALTER TABLE deployments ADD COLUMN dataset_name TEXT;")
    except sqlite3.OperationalError:
        pass

    # 为 deployments 表创建 updated_at 触发器
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_deployments_updated_at
        AFTER UPDATE ON deployments
        FOR EACH ROW
        BEGIN
            UPDATE deployments SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
        END;
    """)
    print("Table 'deployments' is ready.")
    
    conn.commit()
    conn.close()
    print("Database initialization complete.")

if __name__ == '__main__':
    # 如果直接运行此文件，则会初始化数据库
    create_tables()
