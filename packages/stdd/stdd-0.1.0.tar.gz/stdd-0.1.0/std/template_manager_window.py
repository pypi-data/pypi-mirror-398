"""
Окно руководителя/менеджера
ИЗМЕНИТЬ: под свою предметную область
"""
from PyQt6.QtWidgets import *
from PyQt6.QtCore import QDate
from template_db import db
from config import TABLES, UI_TEXT

class ManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(UI_TEXT['manager_title'])
        self.setGeometry(100, 100, 1000, 700)
        
        tab = QTabWidget()
        tab.addTab(self.create_stats_tab(), 'Статистика')
        tab.addTab(self.create_staff_tab(), 'Персонал')  # ИЗМЕНИТЬ/УДАЛИТЬ если не нужно
        
        central = QWidget()
        central.setLayout(QVBoxLayout())
        central.layout().addWidget(tab)
        self.setCentralWidget(central)
    
    def create_stats_tab(self):
        """Вкладка статистики - ИЗМЕНИТЬ под свои метрики"""
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
        filter_layout.addWidget(QPushButton('Рассчитать', clicked=self.calculate_metric))
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        
        layout.addLayout(filter_layout)
        layout.addWidget(self.stats_text)
        layout.addWidget(QPushButton('Показать статистику', clicked=self.show_stats))
        widget.setLayout(layout)
        return widget
    
    def create_staff_tab(self):
        """Вкладка персонала - УДАЛИТЬ если не нужно"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.staff_table = QTableWidget()
        self.staff_table.setColumnCount(3)
        self.staff_table.setHorizontalHeaderLabels(['ID', 'ФИО', 'Должность'])
        
        layout.addWidget(self.staff_table)
        widget.setLayout(layout)
        self.load_staff()
        return widget
    
    def calculate_metric(self):
        """Расчет метрики - ИЗМЕНИТЬ под свои расчеты"""
        date_from = self.date_from.date().toString('yyyy-MM-dd')
        date_to = self.date_to.date().toString('yyyy-MM-dd')
        # ПРИМЕР: средний чек
        # result = db.get_value(f"SELECT AVG(amount) FROM {TABLES['payments']} WHERE payment_date BETWEEN %s AND %s", (date_from, date_to))
        # QMessageBox.information(self, 'Метрика', f'Средний чек: {result:.2f}')
        pass
    
    def show_stats(self):
        """Показать статистику - ИЗМЕНИТЬ под свои показатели"""
        date_from = self.date_from.date().toString('yyyy-MM-dd')
        date_to = self.date_to.date().toString('yyyy-MM-dd')
        
        # ПРИМЕР:
        # total_items = db.get_value(f"SELECT COUNT(*) FROM {TABLES['items']}") or 0
        # active_orders = db.get_value(f"SELECT COUNT(*) FROM {TABLES['orders']} WHERE status='active'") or 0
        # revenue = db.get_value(f"SELECT SUM(amount) FROM {TABLES['payments']} WHERE payment_date BETWEEN %s AND %s", (date_from, date_to)) or 0
        # 
        # text = f"Статистика за период {date_from} - {date_to}\n\n"
        # text += f"Всего предметов: {total_items}\nАктивных заказов: {active_orders}\nВыручка: {revenue:.2f}\n"
        # self.stats_text.setPlainText(text)
        pass
    
    def load_staff(self):
        """Загрузка персонала - УДАЛИТЬ если не нужно"""
        # data = db.query("SELECT id, name, position FROM staff")
        # self.staff_table.setRowCount(len(data))
        # for i, row in enumerate(data):
        #     for j, val in enumerate(row):
        #         self.staff_table.setItem(i, j, QTableWidgetItem(str(val)))
        pass

