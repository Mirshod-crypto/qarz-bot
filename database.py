import sqlite3
import os
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "qarz_daftar.db")

class Database:
    def __init__(self):
        self.db_path = DB_PATH
        self.init_db()

    def get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.get_conn()
        c = conn.cursor()

        # Users (xodimlar)
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            telegram_id INTEGER UNIQUE,
            name TEXT,
            username TEXT,
            lang TEXT DEFAULT 'latin',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')

        # Debtors (qarzdorlar)
        c.execute('''CREATE TABLE IF NOT EXISTS debtors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            name_original TEXT,
            phone TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )''')

        # Debt transactions
        c.execute('''CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            debtor_id INTEGER,
            type TEXT,  -- 'debt' or 'payment'
            amount REAL,
            description TEXT,
            due_date TEXT,
            date TEXT DEFAULT CURRENT_TIMESTAMP,
            added_by INTEGER,
            FOREIGN KEY (debtor_id) REFERENCES debtors(id)
        )''')

        # Financial transactions (kirim/chiqim)
        c.execute('''CREATE TABLE IF NOT EXISTS financial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,  -- 'income' or 'expense'
            amount REAL,
            description TEXT,
            date TEXT DEFAULT CURRENT_TIMESTAMP
        )''')

        conn.commit()
        conn.close()

    # ======= USER METHODS =======
    def add_user(self, telegram_id, name, username):
        conn = self.get_conn()
        conn.execute('''INSERT OR IGNORE INTO users (telegram_id, name, username)
                       VALUES (?, ?, ?)''', (telegram_id, name, username))
        conn.commit()
        conn.close()

    def get_user_lang(self, telegram_id) -> str:
        conn = self.get_conn()
        row = conn.execute('SELECT lang FROM users WHERE telegram_id = ?', (telegram_id,)).fetchone()
        conn.close()
        return row['lang'] if row else 'latin'

    def set_user_lang(self, telegram_id, lang):
        conn = self.get_conn()
        conn.execute('UPDATE users SET lang = ? WHERE telegram_id = ?', (lang, telegram_id))
        conn.commit()
        conn.close()

    # ======= DEBTOR METHODS =======
    def add_debtor(self, name: str, phone: str = '') -> int:
        """Yangi qarzdor qo'shish. Dublikat tekshiruvi bilan."""
        # Avval mavjudligini tekshir (ism bo'yicha)
        existing = self.search_debtor(name)
        if existing:
            # Agar bir xil ism bo'lsa, birinchisini qaytarish
            for d in existing:
                if d['name'].lower().strip() == name.lower().strip():
                    return d['id']

        conn = self.get_conn()
        cursor = conn.execute(
            'INSERT INTO debtors (name, name_original, phone) VALUES (?, ?, ?)',
            (name, name, phone)
        )
        debtor_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return debtor_id

    def get_debtor(self, debtor_id: int):
        conn = self.get_conn()
        row = conn.execute('SELECT * FROM debtors WHERE id = ?', (debtor_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def search_debtor(self, query: str):
        conn = self.get_conn()
        rows = conn.execute('''
            SELECT d.*, 
                   COALESCE(SUM(CASE WHEN t.type='debt' THEN t.amount ELSE 0 END), 0) as total_debt,
                   COALESCE(SUM(CASE WHEN t.type='payment' THEN t.amount ELSE 0 END), 0) as total_paid
            FROM debtors d
            LEFT JOIN transactions t ON d.id = t.debtor_id
            WHERE d.is_active = 1 AND (d.name LIKE ? OR d.phone LIKE ?)
            GROUP BY d.id
        ''', (f'%{query}%', f'%{query}%')).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_all_debtors_with_balance(self):
        conn = self.get_conn()
        rows = conn.execute('''
            SELECT d.*,
                   COALESCE(SUM(CASE WHEN t.type='debt' THEN t.amount ELSE 0 END), 0) as total_debt,
                   COALESCE(SUM(CASE WHEN t.type='payment' THEN t.amount ELSE 0 END), 0) as total_paid
            FROM debtors d
            LEFT JOIN transactions t ON d.id = t.debtor_id
            WHERE d.is_active = 1
            GROUP BY d.id
            HAVING total_debt > total_paid
            ORDER BY (total_debt - total_paid) DESC
        ''').fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_overdue_debtors(self):
        conn = self.get_conn()
        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        rows = conn.execute('''
            SELECT d.*,
                   COALESCE(SUM(CASE WHEN t.type='debt' THEN t.amount ELSE 0 END), 0) as total_debt,
                   COALESCE(SUM(CASE WHEN t.type='payment' THEN t.amount ELSE 0 END), 0) as total_paid,
                   MIN(t.due_date) as earliest_due,
                   CAST((julianday('now') - julianday(MIN(t.due_date))) AS INTEGER) as days_overdue
            FROM debtors d
            JOIN transactions t ON d.id = t.debtor_id
            WHERE d.is_active = 1 AND t.type = 'debt' AND t.due_date IS NOT NULL AND t.due_date < ?
            GROUP BY d.id
            HAVING total_debt > total_paid
            ORDER BY days_overdue DESC
        ''', (today,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def delete_debtor(self, debtor_id: int):
        conn = self.get_conn()
        conn.execute('UPDATE debtors SET is_active = 0 WHERE id = ?', (debtor_id,))
        conn.commit()
        conn.close()

    # ======= TRANSACTION METHODS =======
    def add_debt(self, debtor_id: int, amount: float, description: str, due_date=None, added_by=None):
        conn = self.get_conn()
        conn.execute('''INSERT INTO transactions (debtor_id, type, amount, description, due_date, added_by)
                       VALUES (?, 'debt', ?, ?, ?, ?)''',
                    (debtor_id, amount, description, due_date, added_by))
        conn.commit()
        conn.close()

    def add_payment(self, debtor_id: int, amount: float, added_by=None):
        conn = self.get_conn()
        conn.execute("""INSERT INTO transactions (debtor_id, type, amount, description, added_by)
                       VALUES (?, 'payment', ?, 'Tolov', ?)""",
                    (debtor_id, amount, added_by))
        conn.commit()
        conn.close()

    def get_debtor_transactions(self, debtor_id: int):
        conn = self.get_conn()
        rows = conn.execute('''SELECT * FROM transactions WHERE debtor_id = ?
                              ORDER BY date ASC''', (debtor_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_debtor_balance(self, debtor_id: int):
        conn = self.get_conn()
        row = conn.execute('''
            SELECT COALESCE(SUM(CASE WHEN type='debt' THEN amount ELSE 0 END), 0) as total_debt,
                   COALESCE(SUM(CASE WHEN type='payment' THEN amount ELSE 0 END), 0) as total_paid
            FROM transactions WHERE debtor_id = ?
        ''', (debtor_id,)).fetchone()
        conn.close()
        return dict(row) if row else {'total_debt': 0, 'total_paid': 0}

    # ======= FINANCIAL METHODS =======
    def add_transaction(self, type: str, amount: float, description: str):
        conn = self.get_conn()
        conn.execute('INSERT INTO financial (type, amount, description) VALUES (?, ?, ?)',
                    (type, amount, description))
        conn.commit()
        conn.close()

    def get_financial_report(self):
        conn = self.get_conn()

        fin = conn.execute('''SELECT
            COALESCE(SUM(CASE WHEN type='income' THEN amount ELSE 0 END), 0) as total_income,
            COALESCE(SUM(CASE WHEN type='expense' THEN amount ELSE 0 END), 0) as total_expense
            FROM financial''').fetchone()

        debt_info = conn.execute('''SELECT
            COALESCE(SUM(CASE WHEN type='debt' THEN amount ELSE 0 END), 0) as total_debt,
            COALESCE(SUM(CASE WHEN type='payment' THEN amount ELSE 0 END), 0) as total_paid
            FROM transactions''').fetchone()

        total_debtors = conn.execute("SELECT COUNT(*) as cnt FROM debtors WHERE is_active=1").fetchone()['cnt']

        conn.close()

        # Overdue count
        overdue = self.get_overdue_debtors()

        return {
            'total_income': fin['total_income'],
            'total_expense': fin['total_expense'],
            'total_debt': debt_info['total_debt'],
            'total_paid': debt_info['total_paid'],
            'total_debtors': total_debtors,
            'overdue_count': len(overdue)
        }
