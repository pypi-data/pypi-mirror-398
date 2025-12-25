"""
Окно авторизации
Обычно не требует изменений, только проверьте названия таблиц в config.py
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from template_db import db
from config import TABLES, ROLES

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Авторизация')
        self.setFixedSize(300, 150)
        layout = QVBoxLayout()
        
        self.login_edit = QLineEdit()
        self.login_edit.setPlaceholderText('Логин')
        self.pass_edit = QLineEdit()
        self.pass_edit.setPlaceholderText('Пароль')
        self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        
        btn = QPushButton('Войти')
        btn.clicked.connect(self.login)
        
        layout.addWidget(QLabel('Логин:'))
        layout.addWidget(self.login_edit)
        layout.addWidget(QLabel('Пароль:'))
        layout.addWidget(self.pass_edit)
        layout.addWidget(btn)
        self.setLayout(layout)
    
    def login(self):
        # Импорт окон - ИЗМЕНИТЬ названия модулей под свои
        from template_admin_window import AdminWindow
        from template_manager_window import ManagerWindow
        from template_client_window import ClientWindow
        
        login = self.login_edit.text()
        password = self.pass_edit.text()
        
        # ИЗМЕНИТЬ: названия таблиц и колонок из config.py
        result = db.query(f"SELECT id, role_id FROM {TABLES['users']} WHERE login=%s AND password=%s", (login, password))
        
        if result:
            user_id, role_id = result[0]
            self.hide()
            
            # ИЗМЕНИТЬ: названия ролей из config.py
            if role_id == ROLES['admin']:
                self.main_window = AdminWindow(user_id)
            elif role_id == ROLES['manager']:
                self.main_window = ManagerWindow()
            else:
                self.main_window = ClientWindow(user_id)
            self.main_window.show()
        else:
            QMessageBox.warning(self, 'Ошибка', 'Неверный логин или пароль')

