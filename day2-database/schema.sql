CREATE TABLE IF NOT EXISTS leads (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    email       TEXT    NOT NULL UNIQUE,
    phone       TEXT,
    status      TEXT    NOT NULL DEFAULT 'new',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
