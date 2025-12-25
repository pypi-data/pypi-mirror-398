"""
Окно администратора
ИЗМЕНИТЬ: названия таблиц, полей и тексты под свою предметную область
Используйте значения из config.py для названий таблиц
"""
from PyQt6.QtWidgets import *
from PyQt6.QtCore import QDate
from datetime import datetime
from template_db import db
from config import TABLES, COLUMNS, UI_TEXT

class AdminWindow(QMainWindow):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle(UI_TEXT['admin_title'])
        self.setGeometry(100, 100, 1000, 700)
        
        tab = QTabWidget()
        # ИЗМЕНИТЬ: создайте нужные вам вкладки
        tab.addTab(self.create_orders_tab(), UI_TEXT['tab_orders'])
        tab.addTab(self.create_clients_tab(), UI_TEXT['tab_clients'])
        tab.addTab(self.create_items_tab(), UI_TEXT['tab_items'])
        tab.addTab(self.create_payments_tab(), UI_TEXT['tab_payments'])
        
        central = QWidget()
        central.setLayout(QVBoxLayout())
        central.layout().addWidget(tab)
        self.setCentralWidget(central)
    
    def create_orders_tab(self):
        """Вкладка заказов/бронирований - ИЗМЕНИТЬ под свою структуру"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        filter_layout = QHBoxLayout()
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate())
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate().addDays(30))
        filter_layout.addWidget(QLabel(UI_TEXT['field_date_from']))
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(QLabel(UI_TEXT['field_date_to']))
        filter_layout.addWidget(self.date_to)
        filter_layout.addWidget(QPushButton(UI_TEXT['field_filter'], clicked=self.filter_orders))
        filter_layout.addWidget(QPushButton(UI_TEXT['field_show_all'], clicked=self.load_orders))
        
        self.orders_table = QTableWidget()
        # ИЗМЕНИТЬ: количество колонок и их названия
        self.orders_table.setColumnCount(8)
        self.orders_table.setHorizontalHeaderLabels(['ID', 'Клиент', 'Предмет', 'Дата начала', 'Дата конца', 'Статус', 'Скидка', 'Действие'])
        
        layout.addLayout(filter_layout)
        layout.addWidget(self.orders_table)
        widget.setLayout(layout)
        self.load_orders()
        return widget
    
    def create_clients_tab(self):
        """Вкладка клиентов - ИЗМЕНИТЬ под свою структуру"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # ИЗМЕНИТЬ: добавьте нужные поля формы
        form = QFormLayout()
        self.client_name = QLineEdit()
        self.client_field1 = QLineEdit()  # пример дополнительного поля
        
        form.addRow('Имя:', self.client_name)
        form.addRow('Поле 1:', self.client_field1)  # ИЗМЕНИТЬ
        
        search_layout = QHBoxLayout()
        self.search_client_edit = QLineEdit()
        self.search_client_edit.setPlaceholderText('Поиск')
        search_layout.addWidget(self.search_client_edit)
        search_layout.addWidget(QPushButton('Найти', clicked=self.search_clients))
        search_layout.addWidget(QPushButton('Показать всех', clicked=self.load_clients))
        
        self.clients_table = QTableWidget()
        # ИЗМЕНИТЬ: колонки таблицы
        self.clients_table.setColumnCount(3)
        self.clients_table.setHorizontalHeaderLabels(['ID', 'Имя', 'Поле'])
        
        layout.addLayout(form)
        layout.addWidget(QPushButton('Добавить клиента', clicked=self.add_client))
        layout.addLayout(search_layout)
        layout.addWidget(self.clients_table)
        widget.setLayout(layout)
        self.load_clients()
        return widget
    
    def create_items_tab(self):
        """Вкладка предметов (товары, номера и т.д.) - ИЗМЕНИТЬ"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.items_table = QTableWidget()
        # ИЗМЕНИТЬ: колонки таблицы
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(['ID', 'Название', 'Категория', 'Статус'])
        
        layout.addWidget(self.items_table)
        widget.setLayout(layout)
        self.load_items()
        return widget
    
    def create_payments_tab(self):
        """Вкладка платежей - ИЗМЕНИТЬ под свои нужды"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        form = QFormLayout()
        self.pay_order_id = QSpinBox()
        self.pay_order_id.setMinimum(1)
        self.pay_type = QComboBox()
        self.pay_type.addItems(['Оплата', 'Возврат'])
        self.pay_amount_label = QLabel('0.00 руб.')
        
        form.addRow('ID заказа:', self.pay_order_id)
        form.addRow('Тип:', self.pay_type)
        form.addRow('Сумма:', self.pay_amount_label)
        
        layout.addLayout(form)
        layout.addWidget(QPushButton('Зарегистрировать платеж', clicked=self.register_payment))
        
        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(4)
        self.payments_table.setHorizontalHeaderLabels(['ID', 'Заказ', 'Сумма', 'Дата'])
        
        layout.addWidget(self.payments_table)
        widget.setLayout(layout)
        self.load_payments()
        return widget
    
    def fill_table(self, table, data, action_col=None):
        """Универсальная функция заполнения таблицы"""
        table.setRowCount(len(data))
        for i, row in enumerate(data):
            for j, val in enumerate(row):
                table.setItem(i, j, QTableWidgetItem(str(val) if val else ''))
            if action_col is not None and len(row) > 0:
                btn = QPushButton(action_col[0])
                btn.clicked.connect(lambda checked, rid=row[0]: action_col[1](rid))
                table.setCellWidget(i, table.columnCount() - 1, btn)
    
    def load_orders(self):
        """Загрузка заказов - ИЗМЕНИТЬ SQL запрос под свои таблицы"""
        # ПРИМЕР SQL (ИЗМЕНИТЬ):
        # data = db.query(f"SELECT o.id, u.name, i.name, o.date_from, o.date_to, o.status, o.discount FROM {TABLES['orders']} o JOIN {TABLES['users']} u ON o.client_id=u.id JOIN {TABLES['items']} i ON o.item_id=i.id")
        # self.fill_table(self.orders_table, data, ('Изменить', self.change_order))
        pass
    
    def filter_orders(self):
        """Фильтрация заказов по дате - ИЗМЕНИТЬ"""
        date_from = self.date_from.date().toString('yyyy-MM-dd')
        date_to = self.date_to.date().toString('yyyy-MM-dd')
        # ИЗМЕНИТЬ: SQL запрос
        pass
    
    def load_clients(self):
        """Загрузка клиентов - ИЗМЕНИТЬ"""
        from config import ROLES
        # data = db.query(f"SELECT id, name, field1 FROM {TABLES['users']} WHERE role_id={ROLES['client']}")
        # self.fill_table(self.clients_table, data)
        pass
    
    def search_clients(self):
        """Поиск клиентов - ИЗМЕНИТЬ"""
        search = self.search_client_edit.text()
        # data = db.query(f"SELECT id, name FROM {TABLES['users']} WHERE name LIKE %s", (f'%{search}%',))
        # self.fill_table(self.clients_table, data)
        pass
    
    def add_client(self):
        """Добавление клиента - ИЗМЕНИТЬ"""
        # db.query(f"INSERT INTO {TABLES['users']}(name, field1, role_id) VALUES (%s, %s, %s)", (self.client_name.text(), self.client_field1.text(), ROLES['client']))
        pass
    
    def load_items(self):
        """Загрузка предметов - ИЗМЕНИТЬ"""
        # data = db.query(f"SELECT i.id, i.name, c.name, s.name FROM {TABLES['items']} i JOIN {TABLES['categories']} c ON i.category_id=c.id JOIN {TABLES['statuses']} s ON i.status_id=s.id")
        # self.fill_table(self.items_table, data)
        pass
    
    def load_payments(self):
        """Загрузка платежей - ИЗМЕНИТЬ"""
        # data = db.query(f"SELECT id, order_id, amount, payment_date FROM {TABLES['payments']} ORDER BY payment_date DESC")
        # self.fill_table(self.payments_table, data)
        pass
    
    def register_payment(self):
        """Регистрация платежа - ИЗМЕНИТЬ"""
        # order_id = self.pay_order_id.value()
        # amount = 1000.0  # ИЗМЕНИТЬ: рассчитайте сумму
        # db.query(f"INSERT INTO {TABLES['payments']}(order_id, amount, payment_date, type) VALUES (%s, %s, CURDATE(), %s)", (order_id, amount, self.pay_type.currentText()))
        pass

