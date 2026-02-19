-- SQLite schema for TechShop
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Category (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    slug VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS Subcategory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(80) NOT NULL,
    slug VARCHAR(80) NOT NULL,
    category_id INTEGER NOT NULL,
    FOREIGN KEY(category_id) REFERENCES Category(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_subcategory_category ON Subcategory(category_id);

CREATE TABLE IF NOT EXISTS Product (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL CHECK(price >= 0),
    stock INTEGER NOT NULL CHECK(stock >= 0),
    category_id INTEGER NOT NULL DEFAULT 1,
    subcategory_id INTEGER REFERENCES Subcategory(id),
    FOREIGN KEY(category_id) REFERENCES Category(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_product_category ON Product(category_id);
CREATE INDEX IF NOT EXISTS idx_product_subcategory ON Product(subcategory_id);

CREATE TABLE IF NOT EXISTS UserAccount (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(20) NOT NULL UNIQUE CHECK(length(username) BETWEEN 4 AND 20),
    password_hash VARCHAR(60) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    segment VARCHAR(50) DEFAULT 'Aficionat',
    created_at DATETIME NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS "Order" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    total DECIMAL(10,2) NOT NULL CHECK(total >= 0),
    created_at DATETIME NOT NULL DEFAULT (datetime('now')),
    user_id INTEGER NOT NULL,
    shipping_city VARCHAR(100),
    shipping_province VARCHAR(100),
    shipping_country VARCHAR(100),
    FOREIGN KEY(user_id) REFERENCES UserAccount(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS OrderItem (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    FOREIGN KEY(order_id) REFERENCES "Order"(id) ON DELETE CASCADE,
    FOREIGN KEY(product_id) REFERENCES Product(id) ON DELETE RESTRICT
);

-- Índexs útils
CREATE INDEX IF NOT EXISTS idx_order_user ON "Order"(user_id);
CREATE INDEX IF NOT EXISTS idx_orderitem_order ON OrderItem(order_id);
CREATE INDEX IF NOT EXISTS idx_orderitem_product ON OrderItem(product_id);
