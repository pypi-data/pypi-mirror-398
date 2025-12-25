from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from db import db

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
        from admin_window import AdminWindow
        from manager_window import ManagerWindow
        from client_window import ClientWindow
        
        login = self.login_edit.text()
        password = self.pass_edit.text()
        result = db.query("SELECT id, role_id FROM users WHERE login=%s AND password=%s", (login, password))
        if result:
            user_id, role_id = result[0]
            self.hide()
            if role_id == 1:
                self.main_window = AdminWindow(user_id)
            elif role_id == 2:
                self.main_window = ManagerWindow()
            else:
                self.main_window = ClientWindow(user_id)
            self.main_window.show()
        else:
            QMessageBox.warning(self, 'Ошибка', 'Неверный логин или пароль')

