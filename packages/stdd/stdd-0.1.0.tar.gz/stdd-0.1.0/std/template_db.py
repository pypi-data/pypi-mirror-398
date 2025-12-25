"""
Универсальный модуль для работы с БД
Замените config.py своими параметрами подключения и названиями таблиц
"""
import pymysql
from datetime import datetime
from config import DB_CONFIG

class DB:
    def __init__(self):
        self.conn = pymysql.connect(**DB_CONFIG)
    
    def query(self, sql, params=None):
        """Выполнить SQL запрос"""
        cursor = self.conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        if sql.strip().upper().startswith('SELECT'):
            return cursor.fetchall()
        self.conn.commit()
        return cursor.rowcount
    
    def get_value(self, sql, params=None):
        """Получить одно значение из результата запроса"""
        result = self.query(sql, params)
        return result[0][0] if result and result[0][0] else None
    
    # ============================================
    # ДОБАВЬТЕ СВОИ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ЗДЕСЬ
    # ============================================
    # Например:
    # def calc_period_days(self, date_from, date_to):
    #     """Расчет количества дней между датами"""
    #     if not date_from:
    #         return 1
    #     if isinstance(date_from, str):
    #         date_from = datetime.strptime(date_from, '%Y-%m-%d')
    #     if isinstance(date_to, str):
    #         date_to = datetime.strptime(date_to, '%Y-%m-%d') if date_to else None
    #     if date_to:
    #         days = (date_to - date_from).days
    #         return max(1, days)
    #     return 1

db = DB()

