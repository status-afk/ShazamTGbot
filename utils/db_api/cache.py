from .database import Database

class MediaCacheDatabase(Database):
    def create_table_cache(self):
        """
        Media fayllar uchun jadvalni yaratish.
        """
        sql_cache = """
        CREATE TABLE IF NOT EXISTS MediaCache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,                -- Platforma nomi
            url TEXT NOT NULL UNIQUE,              -- Media URL
            file_id TEXT NOT NULL UNIQUE,          -- Telegram file_id
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP -- Yaratilgan vaqt
        );
        """
        self.execute(sql_cache, commit=True)

    def create_table_request_stats(self):
        """
        Platformalar bo'yicha statistikani kuzatish uchun jadvalni yaratish.
        """
        sql_stats = """
        CREATE TABLE IF NOT EXISTS RequestStats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,                
            request_count INTEGER DEFAULT 0,       
            created_at DATE DEFAULT CURRENT_DATE   
        );
        """
        self.execute(sql_stats, commit=True)

    # Media uchun funksiyalar
    def add_cache(self, platform: str, url: str, file_id: str):
        """
        Media faylni jadvalga qo'shish.
        """
        sql = """
        INSERT OR IGNORE INTO MediaCache (platform, url, file_id)
        VALUES (?, ?, ?)
        """
        self.execute(sql, parameters=(platform, url, file_id), commit=True)

    def get_file_id_by_url(self, url: str):
        """
        URL orqali file_id ni olish.
        """
        sql = "SELECT file_id FROM MediaCache WHERE url = ?"
        result = self.execute(sql, parameters=(url,), fetchone=True)
        return result[0] if result else None

    def get_all_cache(self):
        """
        Barcha media kechalarni olish.
        """
        sql = "SELECT * FROM MediaCache"
        return self.execute(sql, fetchall=True)

    def delete_cache_by_url(self, url: str):
        """
        URL orqali kechani o'chirish.
        """
        sql = "DELETE FROM MediaCache WHERE url = ?"
        self.execute(sql, parameters=(url,), commit=True)

    def clear_all_cache(self):
        """
        Barcha kechalarni tozalash.
        """
        sql = "DELETE FROM MediaCache"
        self.execute(sql, commit=True)

    def cache_exists(self, url: str) -> bool:
        """
        URL mavjudligini tekshirish.
        """
        sql = "SELECT 1 FROM MediaCache WHERE url = ?"
        result = self.execute(sql, parameters=(url,), fetchone=True)
        return result is not None

    def increment_request_count(self, platform: str):
        """
        Platforma bo'yicha so'rov sonini oshirish yoki yangi yozuv qo'shish.
        """
        sql_check = "SELECT id FROM RequestStats WHERE platform = ? AND created_at = CURRENT_DATE"
        existing = self.execute(sql_check, parameters=(platform,), fetchone=True)

        if existing:
            sql_update = """
               UPDATE RequestStats
               SET request_count = request_count + 1
               WHERE platform = ? AND created_at = CURRENT_DATE
               """
            self.execute(sql_update, parameters=(platform,), commit=True)
        else:
            sql_insert = """
               INSERT INTO RequestStats (platform, request_count)
               VALUES (?, 1)
               """
            self.execute(sql_insert, parameters=(platform,), commit=True)

    def get_daily_stats(self):
        sql = """
           SELECT platform, request_count 
           FROM RequestStats 
           WHERE created_at = CURRENT_DATE
           """
        return self.execute(sql, fetchall=True)

    def get_weekly_stats(self):
        sql = """
           SELECT platform, SUM(request_count) as total_requests
           FROM RequestStats
           WHERE created_at >= DATE('now', '-6 days')
           GROUP BY platform
           """
        return self.execute(sql, fetchall=True)

    def get_monthly_stats(self):
        sql = """
          SELECT platform, SUM(request_count) as total_requests
          FROM RequestStats
          WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
          GROUP BY platform
          """
        return self.execute(sql, fetchall=True)


