from PyQt6.QtWidgets import *
from PyQt6.QtCore import QDate
from db import db

class ClientWindow(QMainWindow):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle('Клиент')
        self.setGeometry(100, 100, 900, 600)
        
        tab = QTabWidget()
        tab.addTab(self.create_rooms_tab(), 'Номера')
        tab.addTab(self.create_booking_tab(), 'Бронирование')
        tab.addTab(self.create_messages_tab(), 'Сообщения')
        
        central = QWidget()
        central.setLayout(QVBoxLayout())
        central.layout().addWidget(tab)
        self.setCentralWidget(central)
    
    def create_rooms_tab(self):
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
        filter_layout.addWidget(QPushButton('Найти свободные номера', clicked=self.search_rooms))
        
        self.rooms_table = QTableWidget()
        self.rooms_table.setColumnCount(3)
        self.rooms_table.setHorizontalHeaderLabels(['Номер', 'Категория', 'Цена'])
        
        layout.addLayout(filter_layout)
        layout.addWidget(self.rooms_table)
        widget.setLayout(layout)
        return widget
    
    def create_booking_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        form = QFormLayout()
        self.booking_room = QSpinBox()
        self.booking_checkin = QDateEdit()
        self.booking_checkin.setDate(QDate.currentDate())
        self.booking_checkout = QDateEdit()
        self.booking_checkout.setDate(QDate.currentDate().addDays(1))
        self.booking_purpose = QComboBox()
        self.booking_purpose.addItems(['Отдых', 'Командировка', 'Лечение', 'Другое'])
        self.booking_passport = QLineEdit()
        self.booking_preferences = QTextEdit()
        self.booking_preferences.setMaximumHeight(80)
        
        for label, field in [('ID номера:', self.booking_room), ('Заезд:', self.booking_checkin), ('Выезд:', self.booking_checkout),
                            ('Цель:', self.booking_purpose), ('Паспорт:', self.booking_passport), ('Пожелания:', self.booking_preferences)]:
            form.addRow(label, field)
        
        self.booking_status = QTextEdit()
        self.booking_status.setReadOnly(True)
        
        layout.addLayout(form)
        layout.addWidget(QPushButton('Забронировать', clicked=self.make_booking))
        layout.addWidget(QLabel('Статусы бронирований:'))
        layout.addWidget(self.booking_status)
        widget.setLayout(layout)
        self.load_booking_status()
        self.load_user_data()
        return widget
    
    def create_messages_tab(self):
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
    
    def search_rooms(self):
        date_from = self.date_from.date().toString('yyyy-MM-dd')
        date_to = self.date_to.date().toString('yyyy-MM-dd')
        data = db.query("""
            SELECT r.number, c.category, c.price FROM rooms r
            JOIN categories c ON r.category_id=c.id
            WHERE r.status_id=2 AND r.id NOT IN (
                SELECT room_id FROM bookings
                WHERE (check_in <= %s AND (check_out >= %s OR check_out IS NULL))
                OR (check_in BETWEEN %s AND %s)
            )
        """, (date_to, date_from, date_from, date_to))
        self.rooms_table.setRowCount(len(data))
        for i, row in enumerate(data):
            for j, val in enumerate(row):
                self.rooms_table.setItem(i, j, QTableWidgetItem(str(val)))
        QMessageBox.information(self, 'Поиск', f'Найдено свободных номеров: {len(data)}')
    
    def make_booking(self):
        if not self.booking_passport.text():
            QMessageBox.warning(self, 'Ошибка', 'Укажите паспортные данные')
            return
        
        room_id = self.booking_room.value()
        check_in = self.booking_checkin.date().toString('yyyy-MM-dd')
        check_out = self.booking_checkout.date().toString('yyyy-MM-dd')
        
        if not db.is_room_available(room_id, check_in, check_out):
            QMessageBox.warning(self, 'Ошибка', 'Номер недоступен')
            return
        
        db.query("INSERT INTO bookings(client_id, room_id, check_in, check_out, status) VALUES (%s, %s, %s, %s, 'Бронирование')", (self.user_id, room_id, check_in, check_out))
        db.query("UPDATE users SET purpose=%s, passport=%s, preferences=%s WHERE id=%s", (self.booking_purpose.currentText(), self.booking_passport.text(), self.booking_preferences.toPlainText(), self.user_id))
        QMessageBox.information(self, 'Успех', 'Номер забронирован')
        self.load_booking_status()
    
    def load_booking_status(self):
        data = db.query("SELECT b.id, r.number, b.check_in, b.check_out, b.status FROM bookings b JOIN rooms r ON b.room_id=r.id WHERE b.client_id=%s", (self.user_id,))
        text = "\n".join([f"Бронирование #{row[0]}: Номер {row[1]}, {row[2]} - {row[3] if row[3] else 'не определено'}, Статус: {row[4]}" for row in data])
        self.booking_status.setPlainText(text)
    
    def load_user_data(self):
        user = db.query("SELECT passport, purpose, preferences FROM users WHERE id=%s", (self.user_id,))
        if user and user[0]:
            if user[0][0]:
                self.booking_passport.setText(user[0][0])
            if user[0][1]:
                index = self.booking_purpose.findText(user[0][1])
                if index >= 0:
                    self.booking_purpose.setCurrentIndex(index)
            if user[0][2]:
                self.booking_preferences.setPlainText(user[0][2])
    
    def send_message(self):
        message = self.message_edit.toPlainText()
        if message:
            db.query("INSERT INTO messages(user_id, message, date) VALUES (%s, %s, CURDATE())", (self.user_id, message))
            QMessageBox.information(self, 'Успех', 'Сообщение отправлено')
            self.message_edit.clear()
            self.load_messages()
    
    def load_messages(self):
        data = db.query("SELECT message, response, date FROM messages WHERE user_id=%s ORDER BY date DESC", (self.user_id,))
        text = "\n".join([f"[{date}] Вопрос: {msg}\n{'Ответ: ' + resp + chr(10) if resp else ''}" for msg, resp, date in data])
        self.messages_text.setPlainText(text)
