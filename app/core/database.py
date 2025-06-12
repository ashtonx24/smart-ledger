from app.core.config import DB_DRIVER, DB_SERVER

def build_conn_str(db_name: str) -> str:
    return (
        f"Driver={{{DB_DRIVER}}};"
        f"Server={DB_SERVER};"
        f"Database={db_name};"
        "Trusted_Connection=yes;"
    )
