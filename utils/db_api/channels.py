from .database import Database

class ChannelDatabase(Database):
    def create_table_channels(self):
        # Kanallar jadvali
        sql_channels = """
        CREATE TABLE IF NOT EXISTS Channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id BIGINT UNIQUE,
            title VARCHAR(255),
            invite_link VARCHAR(255) NOT NULL
        );
        """
        self.execute(sql_channels, commit=True)

    # Kanallar bilan ishlash
    def add_channel(self, channel_id: int, title: str, invite_link: str):
        sql = """
        INSERT INTO Channels (channel_id, title, invite_link)
        VALUES (?, ?, ?)
        """
        self.execute(sql, parameters=(channel_id, title, invite_link), commit=True)

    def remove_channel(self, channel_id: int):
        sql = "DELETE FROM Channels WHERE channel_id = ?"
        self.execute(sql, parameters=(channel_id,), commit=True)

    def get_all_channels(self):
        sql = "SELECT * FROM Channels"
        return self.execute(sql, fetchall=True)

    def get_channel_by_id(self, channel_id: int):
        sql = "SELECT * FROM Channels WHERE channel_id = ?"
        return self.execute(sql, parameters=(channel_id,), fetchone=True)

    def get_channel_by_invite_link(self, invite_link: str):
        sql = "SELECT * FROM Channels WHERE invite_link = ?"
        return self.execute(sql, parameters=(invite_link,), fetchone=True)

    def update_channel_invite_link(self, channel_id: int, new_invite_link: str):
        sql = """
        UPDATE Channels
        SET invite_link = ?
        WHERE channel_id = ?
        """
        self.execute(sql, parameters=(new_invite_link, channel_id), commit=True)

    def channel_exists(self, channel_id: int) -> bool:
        sql = "SELECT 1 FROM Channels WHERE channel_id = ?"
        result = self.execute(sql, parameters=(channel_id,), fetchone=True)
        return result is not None

    def count_channels(self):
        sql = "SELECT COUNT(*) FROM Channels;"
        return self.execute(sql, fetchone=True)[0]
