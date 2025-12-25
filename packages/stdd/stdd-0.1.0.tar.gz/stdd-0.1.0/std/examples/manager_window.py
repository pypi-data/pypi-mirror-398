from PyQt6.QtWidgets import *
from PyQt6.QtCore import QDate
from db import db

class ManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Руководитель')
        self.setGeometry(100, 100, 1000, 700)
        
        tab = QTabWidget()
        tab.addTab(self.create_stats_tab(), 'Статистика')
        tab.addTab(self.create_staff_tab(), 'Персонал')
        
        central = QWidget()
        central.setLayout(QVBoxLayout())
        central.layout().addWidget(tab)
        self.setCentralWidget(central)
    
    def create_stats_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        filter_layout = QHBoxLayout()
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        filter_layout.addWidget(QLabel('С:'))
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(QLabel('По:'))
        filter_layout.addWidget(self.date_to)
        filter_layout.addWidget(QPushButton('Рассчитать ADR', clicked=self.calculate_adr))
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        
        layout.addLayout(filter_layout)
        layout.addWidget(self.stats_text)
        layout.addWidget(QPushButton('Показать статистику', clicked=self.show_stats))
        widget.setLayout(layout)
        return widget
    
    def create_staff_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.staff_table = QTableWidget()
        self.staff_table.setColumnCount(4)
        self.staff_table.setHorizontalHeaderLabels(['ID', 'ФИО', 'Должность', 'Отработано часов'])
        
        layout.addWidget(self.staff_table)
        widget.setLayout(layout)
        self.load_staff()
        return widget
    
    def calculate_adr(self):
        date_from = self.date_from.date().toString('yyyy-MM-dd')
        date_to = self.date_to.date().toString('yyyy-MM-dd')
        adr = db.get_value("SELECT COALESCE(SUM(p.amount) / NULLIF(COUNT(DISTINCT b.room_id), 0), 0) FROM payments p JOIN bookings b ON p.booking_id=b.id WHERE p.payment_date BETWEEN %s AND %s AND p.type='Оплата'", (date_from, date_to))
        if adr and adr > 0:
            QMessageBox.information(self, 'ADR', f'ADR за период: {adr:.2f} руб.')
        else:
            QMessageBox.warning(self, 'Ошибка', 'Нет данных за период')
    
    def show_stats(self):
        date_from = self.date_from.date().toString('yyyy-MM-dd')
        date_to = self.date_to.date().toString('yyyy-MM-dd')
        
        total_rooms = db.get_value("SELECT COUNT(*) FROM rooms") or 0
        occupied = db.get_value("SELECT COUNT(DISTINCT room_id) FROM bookings WHERE check_in <= %s AND (check_out >= %s OR check_out IS NULL)", (date_to, date_from)) or 0
        revenue = db.get_value("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE payment_date BETWEEN %s AND %s AND type='Оплата'", (date_from, date_to)) or 0
        occupancy = (occupied / total_rooms * 100) if total_rooms > 0 else 0
        
        text = f"Статистика за период {date_from} - {date_to}\n\n"
        text += f"Всего номеров: {total_rooms}\nЗанято номеров: {occupied}\nПроцент загрузки: {occupancy:.1f}%\nВыручка: {revenue:.2f} руб.\n"
        self.stats_text.setPlainText(text)
    
    def load_staff(self):
        data = db.query("SELECT id, name, position, hours_worked FROM staff")
        self.staff_table.setRowCount(len(data))
        for i, row in enumerate(data):
            for j, val in enumerate(row):
                self.staff_table.setItem(i, j, QTableWidgetItem(str(val)))
