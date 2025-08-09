import os
import sqlite3
from typing import Tuple, Dict
import psycopg2


def ensure_sqlite_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tax_withholding_certificates (
            id INTEGER PRIMARY KEY,
            withholder_name TEXT NOT NULL,
            withholder_address TEXT NOT NULL,
            withholder_tax_id TEXT NOT NULL,
            withholder_type TEXT NOT NULL,
            withholdee_name TEXT NOT NULL,
            withholdee_address TEXT NOT NULL,
            withholdee_tax_id TEXT NOT NULL,
            withholdee_type TEXT NOT NULL,
            certificate_book_no TEXT,
            certificate_no TEXT,
            sequence_in_form INTEGER,
            form_type TEXT,
            income_type_1_amount REAL DEFAULT 0,
            income_type_1_tax REAL DEFAULT 0,
            income_type_2_amount REAL DEFAULT 0,
            income_type_2_tax REAL DEFAULT 0,
            income_type_3_amount REAL DEFAULT 0,
            income_type_3_tax REAL DEFAULT 0,
            income_type_4a_amount REAL DEFAULT 0,
            income_type_4a_tax REAL DEFAULT 0,
            income_type_4b_amount REAL DEFAULT 0,
            income_type_4b_tax REAL DEFAULT 0,
            dividend_credit_type TEXT,
            dividend_tax_rate REAL,
            income_type_5_amount REAL DEFAULT 0,
            income_type_5_tax REAL DEFAULT 0,
            income_type_6_amount REAL DEFAULT 0,
            income_type_6_tax REAL DEFAULT 0,
            income_type_6_description TEXT,
            total_income REAL DEFAULT 0,
            total_tax_withheld REAL DEFAULT 0,
            total_tax_withheld_text TEXT,
            provident_fund REAL DEFAULT 0,
            social_security_fund REAL DEFAULT 0,
            retirement_mutual_fund REAL DEFAULT 0,
            issue_type TEXT,
            issue_type_other TEXT,
            issue_date TEXT,
            signatory_name TEXT,
            company_seal INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY,
            table_name TEXT NOT NULL,
            operation TEXT NOT NULL,
            record_id INTEGER,
            old_values TEXT,
            new_values TEXT,
            user_info TEXT,
            timestamp TEXT
        );
        """
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_withholder_tax_id ON tax_withholding_certificates(withholder_tax_id);"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_withholdee_tax_id ON tax_withholding_certificates(withholdee_tax_id);"
    )
    conn.commit()


def backup_neon_to_sqlite(pg_connection_string: str, sqlite_path: str = "backup.db") -> Tuple[bool, str, Dict[str, int]]:
    """Backup Neon PostgreSQL data into a local SQLite database file.

    Returns: (ok, message, counts)
    """
    counts: Dict[str, int] = {"tax_withholding_certificates": 0, "audit_logs": 0}
    try:
        # Initialize SQLite
        if os.path.exists(sqlite_path):
            os.remove(sqlite_path)
        sconn = sqlite3.connect(sqlite_path)
        sconn.execute("PRAGMA journal_mode=WAL;")
        sconn.execute("PRAGMA synchronous=NORMAL;")
        ensure_sqlite_schema(sconn)
        scur = sconn.cursor()

        # Connect to Neon
        pconn = psycopg2.connect(pg_connection_string)
        pcur = pconn.cursor()

        # Copy certificates
        pcur.execute("SELECT * FROM tax_withholding_certificates ORDER BY id")
        rows = pcur.fetchall()
        if rows:
            pcur.execute(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'tax_withholding_certificates'
                ORDER BY ordinal_position
                """
            )
            columns = [r[0] for r in pcur.fetchall()]
            placeholders = ",".join(["?"] * len(columns))
            insert_sql = f"INSERT INTO tax_withholding_certificates ({','.join(columns)}) VALUES ({placeholders})"
            scur.executemany(insert_sql, rows)
            counts["tax_withholding_certificates"] = len(rows)

        # Copy audit logs if available
        try:
            pcur.execute("SELECT * FROM audit_logs ORDER BY id")
            arows = pcur.fetchall()
            if arows:
                pcur.execute(
                    """
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'audit_logs'
                    ORDER BY ordinal_position
                    """
                )
                acolumns = [r[0] for r in pcur.fetchall()]
                placeholders = ",".join(["?"] * len(acolumns))
                insert_sql = f"INSERT INTO audit_logs ({','.join(acolumns)}) VALUES ({placeholders})"
                scur.executemany(insert_sql, arows)
                counts["audit_logs"] = len(arows)
        except Exception:
            pass

        sconn.commit()
        scur.close(); sconn.close()
        pcur.close(); pconn.close()
        return True, f"Backup saved to {os.path.abspath(sqlite_path)}", counts
    except Exception as ex:
        return False, f"Backup failed: {ex}", counts


if __name__ == "__main__":
    # Optional CLI usage
    import argparse

    parser = argparse.ArgumentParser(description="Backup Neon PostgreSQL to SQLite")
    parser.add_argument("--pg", required=True, help="PostgreSQL connection string")
    parser.add_argument("--out", default="backup.db", help="SQLite output path")
    args = parser.parse_args()

    ok, msg, counts = backup_neon_to_sqlite(args.pg, args.out)
    print(("OK" if ok else "ERR"), msg, counts)


