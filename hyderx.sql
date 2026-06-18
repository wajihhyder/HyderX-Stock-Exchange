DROP TABLE IF EXISTS `admins`;
DROP TABLE IF EXISTS `discounts`;
DROP TABLE IF EXISTS `stocks`;
DROP TABLE IF EXISTS `transactions`;
DROP TABLE IF EXISTS `users`;
DROP TABLE IF EXISTS `portfolio`;


CREATE TABLE admins (
  'a_id' INTEGER PRIMARY KEY AUTOINCREMENT,
  'a_name' TEXT NOT NULL UNIQUE,
  'a_hash' TEXT NOT NULL,
  'a_email' TEXT NOT NULL
);

-- Table structure for table `discounts`
CREATE TABLE discounts (
  'd_id' INTEGER PRIMARY KEY AUTOINCREMENT,
  'd_code' TEXT NOT NULL,
  'd_percent' REAL NOT NULL,
  'valid' INTEGER NOT NULL DEFAULT 1
);

-- Table structure for table `stocks`
CREATE TABLE stocks (
  's_id' INTEGER PRIMARY KEY AUTOINCREMENT,
  'symbol' TEXT NOT NULL UNIQUE,
  'last_price' REAL NOT NULL,
  'company_name' TEXT NOT NULL
);

-- Table structure for table `users`
CREATE TABLE users (
  'u_id' INTEGER PRIMARY KEY AUTOINCREMENT,
  'u_name' TEXT NOT NULL UNIQUE,
  'u_hash' TEXT NOT NULL,
  'u_email' TEXT DEFAULT NULL UNIQUE CHECK (`u_email` REGEXP '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
  'u_balance' INTEGER NOT NULL DEFAULT 10000
);

-- Table structure for table `transactions`
CREATE TABLE transactions (
  't_id' INTEGER PRIMARY KEY AUTOINCREMENT,
  'u_id' INTEGER NOT NULL,
  'symbol' TEXT NOT NULL,
  'price' REAL NOT NULL,
  'shares' INTEGER NOT NULL,
  'type' TEXT NOT NULL,
  'timestamp' DATETIME NOT NULL,
  FOREIGN KEY (`u_id`) REFERENCES `users`(`u_id`) ON DELETE CASCADE
);

CREATE TABLE portfolio (
  'p_id' integer PRIMARY KEY AUTOINCREMENT,
  'u_id' INTEGER NOT NULL,
  'symbol' TEXT NOT NULL UNIQUE,
  'price' REAL NOT NULL,
  'shares' INTEGER NOT NULL,
  FOREIGN KEY (`u_id`) REFERENCES `users`(`u_id`) ON DELETE CASCADE
);