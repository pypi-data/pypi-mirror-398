"""
Главный файл запуска приложения
ИЗМЕНИТЬ: название модуля login_window на свой
"""
import sys
from PyQt6.QtWidgets import QApplication
from template_login_window import LoginWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())

