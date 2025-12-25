from PyQt6.QtWidgets import *
from PyQt6.QtCore import QDate
from datetime import datetime
from db import db

class AdminWindow(QMainWindow):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle('Администратор')
        self.setGeometry(100, 100, 1000, 700)
        
        tab = QTabWidget()
        tab.addTab(self.create_bookings_tab(), 'Бронирования')
        tab.addTab(self.create_guests_tab(), 'Гости')
        tab.addTab(self.create_rooms_tab(), 'Номера')
        tab.addTab(self.create_payments_tab(), 'Платежи')
        
        central = QWidget()
        central.setLayout(QVBoxLayout())
        central.layout().addWidget(tab)
        self.setCentralWidget(central)
    
    def create_bookings_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        filter_layout = QHBoxLayout()
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate())
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate().addDays(30))
        filter_layout.addWidget(QLabel('С:'))
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(QLabel('По:'))
        filter_layout.addWidget(self.date_to)
        filter_layout.addWidget(QPushButton('Фильтровать', clicked=self.filter_bookings))
        filter_layout.addWidget(QPushButton('Показать все', clicked=self.load_bookings))
        
        self.bookings_table = QTableWidget()
        self.bookings_table.setColumnCount(8)
        self.bookings_table.setHorizontalHeaderLabels(['ID', 'Клиент', 'Номер', 'Заезд', 'Выезд', 'Статус', 'Скидка', 'Действие'])
        
        layout.addLayout(filter_layout)
        layout.addWidget(self.bookings_table)
        widget.setLayout(layout)
        self.load_bookings()
        return widget
    
    def create_guests_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        form = QFormLayout()
        self.guest_last = QLineEdit()
        self.guest_name = QLineEdit()
        self.guest_pat = QLineEdit()
        self.guest_passport = QLineEdit()
        self.guest_purpose = QLineEdit()
        self.guest_prefs = QLineEdit()
        self.guest_discount = QSpinBox()
        self.guest_discount.setMaximum(100)
        
        for label, field in [('Фамилия:', self.guest_last), ('Имя:', self.guest_name), ('Отчество:', self.guest_pat),
                            ('Паспорт:', self.guest_passport), ('Цель:', self.guest_purpose), ('Пожелания:', self.guest_prefs),
                            ('Скидка %:', self.guest_discount)]:
            form.addRow(label, field)
        
        search_layout = QHBoxLayout()
        self.search_guest_edit = QLineEdit()
        self.search_guest_edit.setPlaceholderText('Поиск по фамилии')
        search_layout.addWidget(self.search_guest_edit)
        search_layout.addWidget(QPushButton('Найти', clicked=self.search_guests))
        search_layout.addWidget(QPushButton('Показать всех', clicked=self.load_guests))
        
        self.guests_table = QTableWidget()
        self.guests_table.setColumnCount(6)
        self.guests_table.setHorizontalHeaderLabels(['ID', 'ФИО', 'Паспорт', 'Цель', 'Пожелания', 'Скидка'])
        
        layout.addLayout(form)
        layout.addWidget(QPushButton('Добавить гостя', clicked=self.add_guest))
        layout.addLayout(search_layout)
        layout.addWidget(self.guests_table)
        widget.setLayout(layout)
        self.load_guests()
        return widget
    
    def create_rooms_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QPushButton('Обновить статус "Назначен к уборке" → "Чистый"', clicked=self.update_room_status))
        
        self.rooms_table = QTableWidget()
        self.rooms_table.setColumnCount(5)
        self.rooms_table.setHorizontalHeaderLabels(['ID', 'Номер', 'Категория', 'Статус', 'Действие'])
        
        layout.addWidget(self.rooms_table)
        widget.setLayout(layout)
        self.load_rooms()
        return widget
    
    def create_payments_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        form = QFormLayout()
        self.pay_booking = QSpinBox()
        self.pay_booking.setMinimum(1)
        self.pay_type = QComboBox()
        self.pay_type.addItems(['Оплата', 'Возврат'])
        self.pay_amount_label = QLabel('0.00 руб.')
        
        form.addRow('ID бронирования:', self.pay_booking)
        form.addRow('Тип:', self.pay_type)
        form.addRow('Рассчитанная сумма:', self.pay_amount_label)
        
        layout.addLayout(form)
        layout.addWidget(QPushButton('Рассчитать сумму', clicked=self.calculate_payment_amount))
        layout.addWidget(QPushButton('Зарегистрировать платеж', clicked=self.register_payment))
        layout.addWidget(QPushButton('Сформировать счет', clicked=self.create_invoice))
        layout.addWidget(QPushButton('Разбить на 2 счета', clicked=self.create_split_invoice))
        
        tab_widget = QTabWidget()
        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(5)
        self.payments_table.setHorizontalHeaderLabels(['ID', 'Бронирование', 'Сумма', 'Дата', 'Тип'])
        tab_widget.addTab(self.payments_table, 'Платежи')
        
        self.invoices_table = QTableWidget()
        self.invoices_table.setColumnCount(5)
        self.invoices_table.setHorizontalHeaderLabels(['ID', 'Бронирование', 'Сумма', 'Дата', 'Выгрузить'])
        tab_widget.addTab(self.invoices_table, 'Счета')
        
        layout.addWidget(tab_widget)
        widget.setLayout(layout)
        self.load_payments()
        self.load_invoices()
        return widget
    
    def fill_table(self, table, data, action_col=None):
        table.setRowCount(len(data))
        for i, row in enumerate(data):
            for j, val in enumerate(row):
                table.setItem(i, j, QTableWidgetItem(str(val) if val else ''))
            if action_col is not None and len(row) > 0:
                btn = QPushButton(action_col[0])
                btn.clicked.connect(lambda checked, rid=row[0]: action_col[1](rid))
                table.setCellWidget(i, table.columnCount() - 1, btn)
    
    def load_bookings(self):
        data = db.query("SELECT b.id, CONCAT(u.last_name, ' ', u.name), r.number, b.check_in, b.check_out, b.status, b.discount FROM bookings b JOIN users u ON b.client_id=u.id JOIN rooms r ON b.room_id=r.id")
        self.fill_table(self.bookings_table, data, ('Изменить', self.change_booking))
    
    def filter_bookings(self):
        date_from = self.date_from.date().toString('yyyy-MM-dd')
        date_to = self.date_to.date().toString('yyyy-MM-dd')
        data = db.query("SELECT b.id, CONCAT(u.last_name, ' ', u.name), r.number, b.check_in, b.check_out, b.status, b.discount FROM bookings b JOIN users u ON b.client_id=u.id JOIN rooms r ON b.room_id=r.id WHERE b.check_in BETWEEN %s AND %s", (date_from, date_to))
        self.fill_table(self.bookings_table, data, ('Изменить', self.change_booking))
    
    def change_booking(self, booking_id):
        booking = db.query("SELECT b.room_id, b.check_in, b.check_out, b.status, b.discount FROM bookings b WHERE b.id=%s", (booking_id,))
        if not booking:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle('Изменить параметры размещения')
        form = QFormLayout()
        
        room_combo = QComboBox()
        rooms = db.query("SELECT r.id, r.number FROM rooms r")
        current_room = booking[0][0]
        for rid, rnum in rooms:
            room_combo.addItem(f"Номер {rnum}", rid)
            if rid == current_room:
                room_combo.setCurrentIndex(room_combo.count() - 1)
        
        check_in_edit = QDateEdit()
        check_in_edit.setCalendarPopup(True)
        check_in_edit.setDate(QDate.fromString(str(booking[0][1]), 'yyyy-MM-dd') if booking[0][1] else QDate.currentDate())
        
        check_out_edit = QDateEdit()
        check_out_edit.setCalendarPopup(True)
        check_out_edit.setDate(QDate.fromString(str(booking[0][2]), 'yyyy-MM-dd') if booking[0][2] else QDate.currentDate().addDays(1))
        
        status_edit = QLineEdit()
        status_edit.setText(booking[0][3] if booking[0][3] else '')
        discount_spin = QDoubleSpinBox()
        discount_spin.setMaximum(100)
        discount_spin.setValue(float(booking[0][4]) if booking[0][4] else 0)
        
        form.addRow('Номер:', room_combo)
        form.addRow('Заезд:', check_in_edit)
        form.addRow('Выезд:', check_out_edit)
        form.addRow('Статус:', status_edit)
        form.addRow('Скидка %:', discount_spin)
        form.addRow(QPushButton('Изменить', clicked=lambda: self.save_booking_change(booking_id, room_combo.currentData(), check_in_edit.date().toString('yyyy-MM-dd'), check_out_edit.date().toString('yyyy-MM-dd'), status_edit.text(), discount_spin.value(), dialog)))
        
        dialog.setLayout(form)
        dialog.exec()
    
    def save_booking_change(self, booking_id, room_id, check_in, check_out, status, discount, dialog):
        db.query("UPDATE bookings SET room_id=%s, check_in=%s, check_out=%s, status=%s, discount=%s WHERE id=%s", (room_id, check_in, check_out, status, discount, booking_id))
        QMessageBox.information(self, 'Успех', 'Параметры изменены')
        self.load_bookings()
        dialog.close()
    
    def add_guest(self):
        max_id = db.get_value("SELECT COALESCE(MAX(id), 0) + 1 FROM users")
        login = f"guest{max_id}"
        db.query("INSERT INTO users(last_name, name, patronymic, login, password, role_id, passport, purpose, preferences) VALUES (%s, %s, %s, %s, %s, 3, %s, %s, %s)",
                 (self.guest_last.text(), self.guest_name.text(), self.guest_pat.text(), login, 'pass', 
                  self.guest_passport.text(), self.guest_purpose.text(), self.guest_prefs.text()))
        QMessageBox.information(self, 'Успех', 'Гость добавлен')
        self.load_guests()
    
    def load_guests(self):
        data = db.query("SELECT id, CONCAT(last_name, ' ', name, ' ', patronymic), passport, purpose, preferences, 0 FROM users WHERE role_id=3")
        self.fill_table(self.guests_table, data)
    
    def search_guests(self):
        search = self.search_guest_edit.text()
        data = db.query("SELECT id, CONCAT(last_name, ' ', name, ' ', patronymic), passport, purpose, preferences, 0 FROM users WHERE role_id=3 AND last_name LIKE %s", (f'%{search}%',))
        self.fill_table(self.guests_table, data)
    
    def load_rooms(self):
        data = db.query("SELECT r.id, r.number, c.category, s.statuss FROM rooms r JOIN categories c ON r.category_id=c.id JOIN statuss s ON r.status_id=s.id")
        self.fill_table(self.rooms_table, data, ('Изменить', self.change_room))
    
    def change_room(self, room_id):
        room = db.query("SELECT category_id, status_id FROM rooms WHERE id=%s", (room_id,))
        if not room:
            return
        
        dialog = QDialog(self)
        form = QFormLayout()
        
        category_combo = QComboBox()
        categories = db.query("SELECT id, category FROM categories")
        for cat_id, cat_name in categories:
            category_combo.addItem(cat_name, cat_id)
            if cat_id == room[0][0]:
                category_combo.setCurrentIndex(category_combo.count() - 1)
        
        status_combo = QComboBox()
        statuses = db.query("SELECT id, statuss FROM statuss")
        for stat_id, stat_name in statuses:
            status_combo.addItem(stat_name, stat_id)
            if stat_id == room[0][1]:
                status_combo.setCurrentIndex(status_combo.count() - 1)
        
        form.addRow('Категория:', category_combo)
        form.addRow('Статус:', status_combo)
        form.addRow(QPushButton('Изменить', clicked=lambda: self.save_room_change(room_id, category_combo.currentData(), status_combo.currentData(), dialog)))
        
        dialog.setLayout(form)
        dialog.exec()
    
    def save_room_change(self, room_id, cat_id, stat_id, dialog):
        db.query("UPDATE rooms SET category_id=%s, status_id=%s WHERE id=%s", (cat_id, stat_id, room_id))
        QMessageBox.information(self, 'Успех', 'Номер изменен')
        self.load_rooms()
        dialog.close()
    
    def update_room_status(self):
        db.query("UPDATE rooms SET status_id=2 WHERE status_id=3")
        QMessageBox.information(self, 'Успех', 'Статусы обновлены')
        self.load_rooms()
    
    def calculate_payment_amount(self):
        booking_id = self.pay_booking.value()
        total = db.calc_booking_total(booking_id)
        if total:
            self.calculated_amount = total
            self.pay_amount_label.setText(f'{total:.2f} руб.')
            QMessageBox.information(self, 'Расчет выполнен', f'Сумма: {total:.2f} руб.')
        else:
            QMessageBox.warning(self, 'Ошибка', 'Бронирование не найдено')
    
    def register_payment(self):
        if not hasattr(self, 'calculated_amount'):
            QMessageBox.warning(self, 'Ошибка', 'Сначала рассчитайте сумму')
            return
        
        booking_id = self.pay_booking.value()
        amount = -self.calculated_amount if self.pay_type.currentText() == 'Возврат' else self.calculated_amount
        db.query("INSERT INTO payments(booking_id, amount, payment_date, type) VALUES (%s, %s, CURDATE(), %s)", (booking_id, amount, self.pay_type.currentText()))
        QMessageBox.information(self, 'Успех', 'Платеж зарегистрирован')
        self.pay_amount_label.setText('0.00 руб.')
        delattr(self, 'calculated_amount')
        self.load_payments()
    
    def create_invoice(self):
        booking_id = self.pay_booking.value()
        total = db.calc_booking_total(booking_id)
        if not total:
            QMessageBox.warning(self, 'Ошибка', 'Бронирование не найдено')
            return
        
        db.query("INSERT INTO invoices(booking_id, total, date) VALUES (%s, %s, CURDATE())", (booking_id, total))
        invoice_id = db.get_value("SELECT MAX(id) FROM invoices")
        if invoice_id:
            self.save_invoice_to_file(invoice_id, booking_id)
            QMessageBox.information(self, 'Счет сформирован', f'Сумма: {total:.2f} руб.')
        self.load_invoices()
    
    def create_split_invoice(self):
        booking_id = self.pay_booking.value()
        booking = db.query("SELECT r.category_id, b.check_in, b.check_out, b.discount FROM bookings b JOIN rooms r ON b.room_id=r.id WHERE b.id=%s", (booking_id,))
        if not booking:
            return
        
        cat_id, check_in, check_out, discount = booking[0]
        nights = db.calc_nights(check_in, check_out)
        room_price = db.get_value("SELECT price FROM categories WHERE id=%s", (cat_id,)) or 0
        services_price = db.get_value("SELECT COALESCE(SUM(s.price), 0) FROM bookings_services bs JOIN services s ON bs.service_id=s.id WHERE bs.booking_id=%s", (booking_id,)) or 0
        discount_val = float(discount) if discount else 0
        
        room_total = float(room_price) * nights * (1 - discount_val / 100)
        services_total = float(services_price) * (1 - discount_val / 100)
        
        db.query("INSERT INTO invoices(booking_id, total, date) VALUES (%s, %s, CURDATE())", (booking_id, room_total))
        invoice1_id = db.get_value("SELECT MAX(id) FROM invoices")
        self.save_invoice_to_file(invoice1_id, booking_id, "за номер")
        
        db.query("INSERT INTO invoices(booking_id, total, date) VALUES (%s, %s, CURDATE())", (booking_id, services_total))
        invoice2_id = db.get_value("SELECT MAX(id) FROM invoices")
        self.save_invoice_to_file(invoice2_id, booking_id, "за услуги")
        
        QMessageBox.information(self, 'Счета созданы', f'№{invoice1_id}: {room_total:.2f} руб.\n№{invoice2_id}: {services_total:.2f} руб.')
        self.load_invoices()
    
    def save_invoice_to_file(self, invoice_id, booking_id, suffix=""):
        info = db.query("SELECT CONCAT(u.last_name, ' ', u.name), r.number, b.check_in, b.check_out FROM bookings b JOIN users u ON b.client_id=u.id JOIN rooms r ON b.room_id=r.id WHERE b.id=%s", (booking_id,))
        if not info:
            return
        
        booking = db.query("SELECT r.category_id, b.check_in, b.check_out, b.discount FROM bookings b JOIN rooms r ON b.room_id=r.id WHERE b.id=%s", (booking_id,))[0]
        nights = db.calc_nights(booking[1], booking[2])
        room_price = (db.get_value("SELECT price FROM categories WHERE id=%s", (booking[0],)) or 0) * nights
        services_price = db.get_value("SELECT COALESCE(SUM(s.price), 0) FROM bookings_services bs JOIN services s ON bs.service_id=s.id WHERE bs.booking_id=%s", (booking_id,)) or 0
        discount = float(booking[3]) if booking[3] else 0
        
        filename = f"invoice_{invoice_id}{'_' + suffix.replace(' ', '_') if suffix else ''}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"СЧЕТ №{invoice_id}\nДата: {datetime.now().strftime('%d.%m.%Y')}\n")
            f.write(f"Клиент: {info[0][0]}\nНомер: {info[0][1]}\nПериод: {info[0][2]} - {info[0][3]}\n\n")
            f.write("Наименование\tСумма, руб.\n")
            if room_price > 0:
                f.write(f"Проживание\t{room_price:.2f}\n")
            if services_price > 0:
                f.write(f"Услуги\t{services_price:.2f}\n")
            if discount > 0:
                f.write(f"Скидка {discount}%\t-{(room_price + services_price) * discount / 100:.2f}\n")
            f.write(f"\nИТОГО\t{db.get_value('SELECT total FROM invoices WHERE id=%s', (invoice_id,)):.2f}\n")
    
    def load_payments(self):
        data = db.query("SELECT p.id, p.booking_id, p.amount, p.payment_date, p.type FROM payments p ORDER BY p.payment_date DESC, p.id DESC")
        self.fill_table(self.payments_table, data)
    
    def load_invoices(self):
        data = db.query("SELECT i.id, i.booking_id, i.total, i.date FROM invoices i ORDER BY i.date DESC, i.id DESC")
        self.fill_table(self.invoices_table, data, ('Выгрузить', self.export_invoice))
    
    def export_invoice(self, invoice_id):
        booking_id = db.get_value("SELECT booking_id FROM invoices WHERE id=%s", (invoice_id,))
        if booking_id:
            self.save_invoice_to_file(invoice_id, booking_id)
            QMessageBox.information(self, 'Выгружено', f'Счет сохранен в файл invoice_{invoice_id}.txt')
