# ============================================
# КОНФИГУРАЦИЯ ПРИЛОЖЕНИЯ
# ============================================
# Замените значения ниже на свои данные

# Параметры подключения к БД
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'your_database',  # ИЗМЕНИТЬ: название вашей БД
    'charset': 'utf8mb4'
}

# Названия таблиц в БД (ИЗМЕНИТЬ под свою структуру)
TABLES = {
    'users': 'users',           # таблица пользователей
    'roles': 'roles',           # таблица ролей
    'items': 'items',           # основная таблица предметов (например: rooms, products, services)
    'orders': 'orders',         # таблица заказов/бронирований (например: bookings, orders)
    'categories': 'categories', # таблица категорий
    'statuses': 'statuses',     # таблица статусов
    'services': 'services',     # дополнительные услуги/товары
    'payments': 'payments',     # платежи
    'invoices': 'invoices',     # счета
}

# Названия колонок (ИЗМЕНИТЬ под свою структуру)
COLUMNS = {
    # Таблица пользователей
    'user_id': 'id',
    'user_login': 'login',
    'user_password': 'password',
    'user_role_id': 'role_id',
    'user_name': 'name',
    'user_last_name': 'last_name',
    
    # Таблица заказов/бронирований
    'order_id': 'id',
    'order_client_id': 'client_id',
    'order_item_id': 'item_id',      # например: room_id, product_id
    'order_date_from': 'date_from',  # например: check_in, start_date
    'order_date_to': 'date_to',      # например: check_out, end_date
    'order_status': 'status',
    'order_discount': 'discount',
    
    # Таблица предметов
    'item_id': 'id',
    'item_number': 'number',         # например: number, code
    'item_category_id': 'category_id',
    'item_status_id': 'status_id',
    'item_price': 'price',
}

# Названия окон и интерфейса (ИЗМЕНИТЬ под свою предметную область)
UI_TEXT = {
    'app_title': 'Приложение',           # общее название
    'admin_title': 'Администратор',      # название окна администратора
    'manager_title': 'Руководитель',     # название окна руководителя
    'client_title': 'Клиент',            # название окна клиента
    
    # Названия вкладок (ИЗМЕНИТЬ)
    'tab_orders': 'Заказы',              # например: Бронирования, Заявки
    'tab_clients': 'Клиенты',            # например: Гости, Пользователи
    'tab_items': 'Предметы',             # например: Номера, Товары
    'tab_payments': 'Платежи',
    
    # Названия полей форм (ИЗМЕНИТЬ)
    'field_date_from': 'С:',
    'field_date_to': 'По:',
    'field_filter': 'Фильтровать',
    'field_show_all': 'Показать все',
}

# Роли пользователей (ID из таблицы roles)
ROLES = {
    'admin': 1,      # роль администратора
    'manager': 2,    # роль руководителя
    'client': 3,     # роль клиента
}

