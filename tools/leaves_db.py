import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent / "employee_leaves.db"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_db() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS leave_balances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_name TEXT UNIQUE NOT NULL,
                leave_balance INTEGER NOT NULL
            )
            """
        )
        row = connection.execute(
            "SELECT COUNT(*) AS count FROM leave_balances"
        ).fetchone()
        if row is None or row["count"] == 0:
            connection.executemany(
                "INSERT INTO leave_balances (employee_name, leave_balance) VALUES (?, ?)",
                [("Alice", 12), ("Bob", 5), ("Charlie", 18)],
            )


def get_leave_balance(employee_name: str) -> str:
    initialize_db()
    with get_connection() as connection:
        row = connection.execute(
            "SELECT leave_balance FROM leave_balances "
            "WHERE LOWER(employee_name) = LOWER(?)",
            (employee_name.strip(),),
        ).fetchone()

    if row is None:
        return f"No leave balance record found for '{employee_name}'."
    return f"{employee_name.title()} has {row['leave_balance']} leave days remaining."