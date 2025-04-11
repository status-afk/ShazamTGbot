# groups.py: Guruhlar bilan bog'liq operatsiyalar
from .database import Database
from datetime import datetime

class GroupDatabase(Database):
    def create_table_groups(self):
        sql = """
        CREATE TABLE IF NOT EXISTS Groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id BIGINT NOT NULL UNIQUE,
            group_name VARCHAR(255) NOT NULL,
            member_count INTEGER NOT NULL DEFAULT 0,
            joined_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_activity DATETIME NULL
        );
        """
        self.execute(sql, commit=True)

    def add_group(self, group_id: int, group_name: str, member_count: int):
        sql = """
          INSERT INTO Groups(group_id, group_name, member_count, joined_at)
          VALUES (?, ?, ?, ?)
          """
        joined_at = datetime.now().isoformat()
        self.execute(sql, parameters=(group_id, group_name, member_count, joined_at), commit=True)

    def update_group_member_count(self, group_id: int, member_count: int):
        sql = """
          UPDATE Groups
          SET member_count = ?, last_activity = ?
          WHERE group_id = ?
          """
        last_activity = datetime.now().isoformat()
        self.execute(sql, parameters=(member_count, last_activity, group_id), commit=True)

    def get_all_groups(self):
        sql = """
          SELECT * FROM Groups
          """
        return self.execute(sql, fetchall=True)

    def delete_group(self, group_id: int):
        sql = """
          DELETE FROM Groups WHERE group_id = ?
          """
        self.execute(sql, parameters=(group_id,), commit=True)
