-- SQLite schema for TechShop
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Product (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL CHECK(price >= 0),
    stock INTEGER NOT NULL CHECK(stock >= 0)
);

CREATE TABLE IF NOT EXISTS UserAccount (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(20) NOT NULL UNIQUE CHECK(length(username) BETWEEN 4 AND 20),
    password_hash VARCHAR(60) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    created_at DATETIME NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS "Order" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    total DECIMAL(10,2) NOT NULL CHECK(total >= 0),
    created_at DATETIME NOT NULL DEFAULT (datetime('now')),
    user_id INTEGER NOT NULL,
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
