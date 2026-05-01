-- 1. Сначала создаем независимые таблицы
CREATE TABLE IF NOT EXISTS groups (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

-- 2. Создаем основную таблицу контактов (если её нет)
CREATE TABLE IF NOT EXISTS contacts (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Добавляем новые колонки в contacts
-- Мы используем проверку, чтобы не было ошибок, если колонки уже есть
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS email VARCHAR(100);
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS birthday DATE;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS group_id INTEGER REFERENCES groups(id);

-- 4. Создаем таблицу телефонов (много телефонов на один контакт)
CREATE TABLE IF NOT EXISTS phones (
    id         SERIAL PRIMARY KEY,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    phone      VARCHAR(20)  NOT NULL,
    type       VARCHAR(10)  CHECK (type IN ('home', 'work', 'mobile'))
);