-- ============================================
-- ПРИМЕР СТРУКТУРЫ БД ДЛЯ ШАБЛОНА
-- ============================================
-- Это минимальный пример. Адаптируйте под свою предметную область.
-- Названия таблиц и полей должны соответствовать config.py

DROP DATABASE IF EXISTS your_database;
CREATE DATABASE your_database;
USE your_database;

-- Таблица ролей (ОБЯЗАТЕЛЬНА)
CREATE TABLE roles(
    id INT AUTO_INCREMENT PRIMARY KEY,
    role VARCHAR(50)
);

-- Таблица пользователей (ОБЯЗАТЕЛЬНА)
CREATE TABLE users(
    id INT AUTO_INCREMENT PRIMARY KEY,
    login VARCHAR(50),
    password VARCHAR(50),
    role_id INT,
    name VARCHAR(100),
    last_name VARCHAR(100),
    -- Добавьте свои поля
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

-- Таблица категорий (при необходимости)
CREATE TABLE categories(
    id INT AUTO_INCREMENT PRIMARY KEY,
    category VARCHAR(100),
    price DECIMAL(10,2)  -- если нужно
);

-- Таблица статусов (при необходимости)
CREATE TABLE statuses(
    id INT AUTO_INCREMENT PRIMARY KEY,
    status VARCHAR(50)
);

-- Основная таблица предметов (ИЗМЕНИТЬ название и поля)
-- Например: rooms, products, cars, services
CREATE TABLE items(
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    number INT,  -- номер/код
    category_id INT,
    status_id INT,
    price DECIMAL(10,2),
    FOREIGN KEY (category_id) REFERENCES categories(id),
    FOREIGN KEY (status_id) REFERENCES statuses(id)
);

-- Таблица заказов/бронирований (ИЗМЕНИТЬ название и поля)
-- Например: bookings, orders, rentals
CREATE TABLE orders(
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT,
    item_id INT,  -- например: room_id, product_id
    date_from DATE,  -- например: check_in, start_date
    date_to DATE,    -- например: check_out, end_date
    status VARCHAR(50),
    discount DECIMAL(5,2) DEFAULT 0,
    FOREIGN KEY (client_id) REFERENCES users(id),
    FOREIGN KEY (item_id) REFERENCES items(id)
);

-- Таблица платежей (при необходимости)
CREATE TABLE payments(
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT,
    amount DECIMAL(10,2),
    payment_date DATE,
    type VARCHAR(50),
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

-- Таблица сообщений (при необходимости)
CREATE TABLE messages(
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    message TEXT,
    response TEXT,
    date DATE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Заполнение начальных данных
INSERT INTO roles(role) VALUES 
('Админ'), 
('Руководитель'), 
('Клиент');

INSERT INTO users(login, password, role_id, name) VALUES
('admin', 'admin', 1, 'Администратор'),
('manager', 'manager', 2, 'Руководитель'),
('client', 'client', 3, 'Клиент');

-- ИЗМЕНИТЬ: добавьте свои начальные данные
INSERT INTO categories(category, price) VALUES
('Категория 1', 1000.00),
('Категория 2', 2000.00);

INSERT INTO statuses(status) VALUES
('Доступен'),
('Недоступен'),
('В обслуживании');

INSERT INTO items(name, number, category_id, status_id, price) VALUES
('Предмет 1', 101, 1, 1, 1000.00),
('Предмет 2', 102, 2, 1, 2000.00);

