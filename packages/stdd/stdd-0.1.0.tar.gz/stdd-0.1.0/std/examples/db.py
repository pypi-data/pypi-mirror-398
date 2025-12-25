import pymysql
from datetime import datetime

class DB:
    def __init__(self):
        self.conn = pymysql.connect(
            host='localhost',
            user='root',
            password='root',
            database='hotels',
            charset='utf8mb4'
        )
    
    def query(self, sql, params=None):
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
        result = self.query(sql, params)
        return result[0][0] if result and result[0][0] else None
    
    def calc_nights(self, check_in, check_out):
        if not check_in:
            return 1
        if isinstance(check_in, str):
            check_in = datetime.strptime(check_in, '%Y-%m-%d')
        if isinstance(check_out, str):
            check_out = datetime.strptime(check_out, '%Y-%m-%d') if check_out else None
        if check_out:
            nights = (check_out - check_in).days
            return max(1, nights)
        return 1
    
    def calc_booking_total(self, booking_id):
        booking = self.query("SELECT r.category_id, b.check_in, b.check_out, b.discount, c.price FROM bookings b JOIN rooms r ON b.room_id=r.id JOIN categories c ON r.category_id=c.id WHERE b.id=%s", (booking_id,))
        if not booking:
            return None
        cat_id, check_in, check_out, discount, room_price = booking[0]
        nights = self.calc_nights(check_in, check_out)
        services_price = self.get_value("SELECT COALESCE(SUM(s.price), 0) FROM bookings_services bs JOIN services s ON bs.service_id=s.id WHERE bs.booking_id=%s", (booking_id,)) or 0
        discount_val = float(discount) if discount else 0
        return (float(room_price) * nights + float(services_price)) * (1 - discount_val / 100)
    
    def is_room_available(self, room_id, check_in, check_out):
        result = self.query("""
            SELECT r.id FROM rooms r
            WHERE r.id = %s AND r.status_id = 2
            AND r.id NOT IN (
                SELECT room_id FROM bookings
                WHERE (check_in <= %s AND (check_out >= %s OR check_out IS NULL))
                OR (check_in BETWEEN %s AND %s)
            )
        """, (room_id, check_out, check_in, check_in, check_out))
        return bool(result)

db = DB()
