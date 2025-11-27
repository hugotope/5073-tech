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
    created_at DATETIME NOT NULL DEFAULT (datetime('now')),
    account_type CHAR(20),
    role CHAR(20)
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

CREATE TABLE IF NOT EXISTS Direcciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    calle VARCHAR(50) NOT NULL,
    "portal/puerta" VARCHAR(10),
    codigo_postal INTEGER NOT NULL,
    ciudad VARCHAR(30) NOT NULL,
    pais CHAR(3) NOT NULL,
    FOREIGN KEY(user_id) REFERENCES UserAccount(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Wishlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY(user_id) REFERENCES UserAccount(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS CartProducts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wishlist_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    FOREIGN KEY(wishlist_id) REFERENCES Wishlist(id) ON DELETE CASCADE,
    FOREIGN KEY(product_id) REFERENCES Product(id) ON DELETE RESTRICT
);

-- Índexs útils
CREATE INDEX IF NOT EXISTS idx_order_user ON "Order"(user_id);
CREATE INDEX IF NOT EXISTS idx_orderitem_order ON OrderItem(order_id);
CREATE INDEX IF NOT EXISTS idx_orderitem_product ON OrderItem(product_id);
CREATE INDEX IF NOT EXISTS idx_direcciones_user ON Direcciones(user_id);
CREATE INDEX IF NOT EXISTS idx_wishlist_user ON Wishlist(user_id);
CREATE INDEX IF NOT EXISTS idx_cartproducts_wishlist ON CartProducts(wishlist_id);
