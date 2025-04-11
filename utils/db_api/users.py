from .database import Database
from datetime import datetime, timedelta

class UserDatabase(Database):
    def create_table_users(self):
        # Foydalanuvchilar jadvali
        sql_users = """
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id BIGINT NOT NULL UNIQUE,
            username VARCHAR(255) NULL,
            last_active DATETIME NULL,
            is_active BOOLEAN DEFAULT TRUE,
            is_blocked BOOLEAN DEFAULT FALSE,  -- Yangi ustun bloklangan foydalanuvchilar uchun
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
        self.execute(sql_users, commit=True)

        sql_admins = """
         CREATE TABLE IF NOT EXISTS Admins (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             user_id INTEGER NOT NULL,
             name VARCHAR(255) NOT NULL,
             is_super_admin BOOLEAN DEFAULT FALSE,
             created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
             FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE
         );
         """
        self.execute(sql_admins, commit=True)

    def user_exists(self, telegram_id: int):
        sql = "SELECT 1 FROM Users WHERE telegram_id = ?"
        result = self.execute(sql, parameters=(telegram_id,), fetchone=True)
        return result is not None

    def add_user(self, telegram_id: int, username: str, created_at=None):
        self.create_table_users()
        if not self.user_exists(telegram_id):
            sql = """
            INSERT INTO Users (telegram_id, username, created_at)
            VALUES (?, ?, ?)
            """
            if created_at is None:
                created_at = datetime.now().isoformat()
            self.execute(sql, parameters=(telegram_id, username, created_at), commit=True)
        else:
            print(f"User with telegram_id {telegram_id} already exists.")

    def select_user(self, **kwargs):
        sql = "SELECT * FROM Users WHERE "
        sql, parameters = self.format_args(sql, kwargs)
        return self.execute(sql, parameters=parameters, fetchone=True)

    def count_users(self):
        return self.execute("SELECT COUNT(*) FROM Users;", fetchone=True)[0]

    def delete_users(self):
        self.execute("DELETE FROM Users WHERE TRUE", commit=True)

    def update_user_last_active(self, telegram_id: int):
        sql = """
                UPDATE Users
                SET last_active = ?
                WHERE telegram_id = ?
                """
        last_active = datetime.now().isoformat()
        self.execute(sql, parameters=(last_active, telegram_id), commit=True)

    def deactivate_user(self, telegram_id: int):
        sql = """
        UPDATE Users
        SET is_active = FALSE
        WHERE telegram_id = ?
        """
        self.execute(sql, parameters=(telegram_id,), commit=True)

    def activate_user(self, telegram_id: int):
        sql = """
        UPDATE Users
        SET is_active = TRUE
        WHERE telegram_id = ?
        """
        self.execute(sql, parameters=(telegram_id,), commit=True)

    def mark_user_as_blocked(self, telegram_id: int):
        sql = """
        UPDATE Users
        SET is_blocked = TRUE, is_active = FALSE
        WHERE telegram_id = ?
        """
        self.execute(sql, parameters=(telegram_id,), commit=True)

    def get_active_users(self):
        sql = "SELECT * FROM Users WHERE is_active = TRUE"
        return self.execute(sql, fetchall=True)

    def get_inactive_users(self):
        sql = "SELECT * FROM Users WHERE is_active = FALSE"
        return self.execute(sql, fetchall=True)

    def get_blocked_users(self):
        sql = "SELECT * FROM Users WHERE is_blocked = TRUE"
        return self.execute(sql, fetchall=True)

    # Statistikalar
    def count_active_users(self):
        sql = "SELECT COUNT(*) FROM Users WHERE is_active = TRUE;"
        return self.execute(sql, fetchone=True)[0]

    def count_blocked_users(self):
        sql = "SELECT COUNT(*) FROM Users WHERE is_blocked = TRUE;"
        return self.execute(sql, fetchone=True)[0]

    def count_users_last_12_hours(self):
        time_threshold = (datetime.now() - timedelta(hours=12)).isoformat()
        sql = "SELECT COUNT(*) FROM Users WHERE created_at >= ?;"
        return self.execute(sql, parameters=(time_threshold,), fetchone=True)[0]

    def count_users_today(self):
        today = datetime.now().date().isoformat()
        sql = "SELECT COUNT(*) FROM Users WHERE DATE(created_at) = ?;"
        return self.execute(sql, parameters=(today,), fetchone=True)[0]

    def count_users_this_week(self):
        start_of_week = (datetime.now() - timedelta(days=datetime.now().weekday())).date().isoformat()
        sql = "SELECT COUNT(*) FROM Users WHERE DATE(created_at) >= ?;"
        return self.execute(sql, parameters=(start_of_week,), fetchone=True)[0]

    def count_users_this_month(self):
        start_of_month = datetime.now().replace(day=1).date().isoformat()
        sql = "SELECT COUNT(*) FROM Users WHERE DATE(created_at) >= ?;"
        return self.execute(sql, parameters=(start_of_month,), fetchone=True)[0]

        # Adminlar bilan ishlash

    def add_admin(self, user_id: int, name: str, is_super_admin: bool = False):
        if not self.check_if_admin(user_id):
            sql = """
               INSERT INTO Admins (user_id, name, is_super_admin)
               VALUES (?, ?, ?)
               """
            self.execute(sql, parameters=(user_id, name, is_super_admin), commit=True)
        else:
            print(f"User with user_id {user_id} is already an admin.")

    def remove_admin(self, user_id: int):
        sql = "DELETE FROM Admins WHERE user_id = ?"
        self.execute(sql, parameters=(user_id,), commit=True)

    def get_all_admins(self):
        sql = """
        SELECT Admins.user_id, Users.telegram_id, Admins.name, Admins.is_super_admin
        FROM Admins
        JOIN Users ON Admins.user_id = Users.id
        """
        result = self.execute(sql, fetchall=True)

        if not result:
            return []

        admins = []
        for row in result:
            admins.append({
                "user_id": row[0],  # Users jadvalidagi id (user_id)
                "telegram_id": row[1],  # Telegram ID
                "name": row[2],  # Adminning ismi
                "is_super_admin": row[3]  # Super admin yoki yo'q
            })
        return admins

    def check_if_admin(self, user_id: int) -> bool:
        sql = "SELECT 1 FROM Admins WHERE user_id = ?"
        result = self.execute(sql, parameters=(user_id,), fetchone=True)
        return result is not None

    def update_admin_status(self, user_id: int, is_super_admin: bool):
        sql = """
        UPDATE Admins
        SET is_super_admin = ?
        WHERE user_id = ?
        """
        self.execute(sql, parameters=(is_super_admin, user_id), commit=True)


