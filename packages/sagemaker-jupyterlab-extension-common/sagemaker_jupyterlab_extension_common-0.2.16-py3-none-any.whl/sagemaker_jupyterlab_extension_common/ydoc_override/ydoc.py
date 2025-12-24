from ypy_websocket.ystore import SQLiteYStore


class MySQLiteYStore(SQLiteYStore):
    db_path = "/opt/db/ystore.db"
