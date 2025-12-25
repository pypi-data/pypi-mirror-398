# Шаблон приложения на PyQt6 + PyMySQL

Универсальный шаблон для создания приложений управления данными с ролевым доступом.

## Структура шаблона

```
shablon/
├── config.py                      # Конфигурация (НАЧНИТЕ ОТСЮДА!)
├── template_db.py                 # Модуль работы с БД
├── template_main.py               # Точка входа
├── template_login_window.py       # Окно авторизации
├── template_admin_window.py       # Окно администратора
├── template_manager_window.py     # Окно руководителя
├── template_client_window.py      # Окно клиента
├── example_database_structure.sql # Пример структуры БД
└── README_template.md             # Эта инструкция
```

## Быстрый старт

### 1. Настройте config.py

Откройте `config.py` и замените:

- **DB_CONFIG['database']** - название вашей БД
- **TABLES** - названия таблиц из вашей БД
- **COLUMNS** - названия колонок
- **UI_TEXT** - тексты интерфейса
- **ROLES** - ID ролей из таблицы roles

### 2. Переименуйте файлы

Уберите префикс `template_` и переименуйте:
- `template_db.py` → `db.py`
- `template_main.py` → `main.py`
- `template_login_window.py` → `login_window.py`
- и т.д.

### 3. Обновите импорты

Во всех файлах замените:
- `from template_db import db` → `from db import db`
- `from template_admin_window import AdminWindow` → `from admin_window import AdminWindow`
- и т.д.

### 4. Создайте БД

Создайте структуру БД согласно вашему проекту. Обязательные таблицы:
- `users` - пользователи (с полями: id, login, password, role_id)
- `roles` - роли (с полями: id, role)

### 5. Настройте окна

В каждом окне (admin, manager, client) раскомментируйте и измените SQL-запросы под свою структуру БД.

## Пример адаптации для новой предметной области

**Пример: Система аренды автомобилей**

1. **config.py:**
```python
TABLES = {
    'users': 'users',
    'roles': 'roles',
    'items': 'cars',           # автомобили
    'orders': 'rentals',       # аренды
    'categories': 'car_types', # типы авто
    'statuses': 'statuses',
    'services': 'services',
    'payments': 'payments',
}
```

2. **template_admin_window.py:**
   - Замените SQL запросы, используя `TABLES['cars']` вместо `TABLES['items']`
   - Измените названия колонок под свою структуру

3. **Создайте БД** с таблицами: users, roles, cars, rentals, car_types, statuses, payments

## Структура БД (минимальная)

Обязательные таблицы:
- **roles** (id, role) - роли пользователей
- **users** (id, login, password, role_id, ...) - пользователи

Рекомендуемые таблицы (в зависимости от предметной области):
- Основная сущность (items, products, rooms, cars и т.д.)
- Заказы/Бронирования (orders, bookings, rentals и т.д.)
- Категории (categories)
- Статусы (statuses)
- Платежи (payments)

## Настройка окон

### Администратор (template_admin_window.py)

Замените методы:
- `load_orders()` - загрузка заказов
- `load_clients()` - загрузка клиентов
- `load_items()` - загрузка предметов
- Добавьте свои методы при необходимости

### Руководитель (template_manager_window.py)

Настройте:
- `calculate_metric()` - расчет ваших метрик
- `show_stats()` - отображение статистики
- Удалите `create_staff_tab()` если не нужно

### Клиент (template_client_window.py)

Настройте:
- `search_items()` - поиск доступных предметов
- `make_order()` - создание заказа
- Формы ввода данных

## Важные замечания

1. Все SQL-запросы используют `%s` для параметров (защита от SQL-инъекций)
2. Используйте значения из `config.py` через `TABLES['table_name']`
3. Проверьте соответствие названий колонок в SQL и структуре БД
4. Тестируйте каждый метод после изменения

## Зависимости

```bash
pip install PyQt6 PyMySQL
```

## Пример запуска

```python
python main.py
```

---

**Вопросы?** Проверьте исходный код примера (файлы без префикса template_) для понимания работы функций.

