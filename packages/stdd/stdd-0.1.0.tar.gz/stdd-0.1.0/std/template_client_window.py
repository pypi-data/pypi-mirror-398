"""
Окно клиента
ИЗМЕНИТЬ: под свою предметную область
"""
from PyQt6.QtWidgets import *
from PyQt6.QtCore import QDate
from template_db import db
from config import TABLES, COLUMNS, ROLES, UI_TEXT

class ClientWindow(QMainWindow):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle(UI_TEXT['client_title'])
        self.setGeometry(100, 100, 900, 600)
        
        tab = QTabWidget()
        tab.addTab(self.create_items_tab(), 'Предметы')  # ИЗМЕНИТЬ: например, Товары, Услуги
        tab.addTab(self.create_order_tab(), 'Заказ')     # ИЗМЕНИТЬ: например, Бронирование, Заявка
        tab.addTab(self.create_messages_tab(), 'Сообщения')
        
        central = QWidget()
        central.setLayout(QVBoxLayout())
        central.layout().addWidget(tab)
        self.setCentralWidget(central)
    
    def create_items_tab(self):
        """Вкладка просмотра предметов - ИЗМЕНИТЬ"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        filter_layout = QHBoxLayout()
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate())
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate().addDays(7))
        filter_layout.addWidget(QLabel('С:'))
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(QLabel('По:'))
        filter_layout.addWidget(self.date_to)
        filter_layout.addWidget(QPushButton('Найти доступные', clicked=self.search_items))
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(3)
        self.items_table.setHorizontalHeaderLabels(['Название', 'Категория', 'Цена'])
        
        layout.addLayout(filter_layout)
        layout.addWidget(self.items_table)
        widget.setLayout(layout)
        return widget
    
    def create_order_tab(self):
        """Вкладка создания заказа - ИЗМЕНИТЬ под свою форму"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        form = QFormLayout()
        self.order_item_id = QSpinBox()
        self.order_date_from = QDateEdit()
        self.order_date_from.setDate(QDate.currentDate())
        self.order_date_to = QDateEdit()
        self.order_date_to.setDate(QDate.currentDate().addDays(1))
        # ИЗМЕНИТЬ: добавьте нужные поля
        self.order_field1 = QLineEdit()
        
        form.addRow('ID предмета:', self.order_item_id)
        form.addRow('Дата начала:', self.order_date_from)
        form.addRow('Дата конца:', self.order_date_to)
        form.addRow('Доп. поле:', self.order_field1)  # ИЗМЕНИТЬ
        
        self.order_status = QTextEdit()
        self.order_status.setReadOnly(True)
        
        layout.addLayout(form)
        layout.addWidget(QPushButton('Создать заказ', clicked=self.make_order))
        layout.addWidget(QLabel('Статусы заказов:'))
        layout.addWidget(self.order_status)
        widget.setLayout(layout)
        self.load_order_status()
        return widget
    
    def create_messages_tab(self):
        """Вкладка сообщений - обычно не требует изменений"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.message_edit = QTextEdit()
        self.message_edit.setPlaceholderText('Ваш вопрос...')
        self.messages_text = QTextEdit()
        self.messages_text.setReadOnly(True)
        
        layout.addWidget(QLabel('Ваш вопрос:'))
        layout.addWidget(self.message_edit)
        layout.addWidget(QPushButton('Отправить', clicked=self.send_message))
        layout.addWidget(QLabel('Переписка:'))
        layout.addWidget(self.messages_text)
        widget.setLayout(layout)
        self.load_messages()
        return widget
    
    def search_items(self):
        """Поиск доступных предметов - ИЗМЕНИТЬ SQL"""
        date_from = self.date_from.date().toString('yyyy-MM-dd')
        date_to = self.date_to.date().toString('yyyy-MM-dd')
        
        # ПРИМЕР SQL (ИЗМЕНИТЬ):
        # data = db.query(f"""
        #     SELECT i.name, c.name, i.price FROM {TABLES['items']} i
        #     JOIN {TABLES['categories']} c ON i.category_id=c.id
        #     WHERE i.status_id = 2 AND i.id NOT IN (
        #         SELECT item_id FROM {TABLES['orders']}
        #         WHERE (date_from <= %s AND (date_to >= %s OR date_to IS NULL))
        #         OR (date_from BETWEEN %s AND %s)
        #     )
        # """, (date_to, date_from, date_from, date_to))
        # 
        # self.items_table.setRowCount(len(data))
        # for i, row in enumerate(data):
        #     for j, val in enumerate(row):
        #         self.items_table.setItem(i, j, QTableWidgetItem(str(val)))
        pass
    
    def make_order(self):
        """Создание заказа - ИЗМЕНИТЬ под свою логику"""
        item_id = self.order_item_id.value()
        date_from = self.order_date_from.date().toString('yyyy-MM-dd')
        date_to = self.order_date_to.date().toString('yyyy-MM-dd')
        
        # ПРИМЕР (ИЗМЕНИТЬ):
        # db.query(f"INSERT INTO {TABLES['orders']}(client_id, item_id, date_from, date_to, status) VALUES (%s, %s, %s, %s, 'Новый')", 
        #          (self.user_id, item_id, date_from, date_to))
        # QMessageBox.information(self, 'Успех', 'Заказ создан')
        # self.load_order_status()
        pass
    
    def load_order_status(self):
        """Загрузка статусов заказов - ИЗМЕНИТЬ"""
        # data = db.query(f"SELECT o.id, i.name, o.date_from, o.date_to, o.status FROM {TABLES['orders']} o JOIN {TABLES['items']} i ON o.item_id=i.id WHERE o.client_id=%s", (self.user_id,))
        # text = "\n".join([f"Заказ #{row[0]}: {row[1]}, {row[2]} - {row[3]}, Статус: {row[4]}" for row in data])
        # self.order_status.setPlainText(text)
        pass
    
    def send_message(self):
        """Отправка сообщения - ИЗМЕНИТЬ название таблицы"""
        message = self.message_edit.toPlainText()
        if message:
            # db.query("INSERT INTO messages(user_id, message, date) VALUES (%s, %s, CURDATE())", (self.user_id, message))
            # QMessageBox.information(self, 'Успех', 'Сообщение отправлено')
            # self.message_edit.clear()
            # self.load_messages()
            pass
    
    def load_messages(self):
        """Загрузка сообщений - ИЗМЕНИТЬ название таблицы"""
        # data = db.query("SELECT message, response, date FROM messages WHERE user_id=%s ORDER BY date DESC", (self.user_id,))
        # text = "\n".join([f"[{date}] Вопрос: {msg}\n{'Ответ: ' + resp + chr(10) if resp else ''}" for msg, resp, date in data])
        # self.messages_text.setPlainText(text)
        pass

