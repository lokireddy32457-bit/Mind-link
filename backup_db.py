"""
Mind Link — Manual Database Backup Script
==========================================
Exports all critical tables to a timestamped SQL dump file.
Run this periodically to keep a local backup of your Supabase data.

Usage:
    python backup_db.py

Output:
    backups/mindlink_backup_YYYYMMDD_HHMMSS.sql
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

DATABASE_URL = os.environ.get("DATABASE_URL", "")
DATABASE_SSL_MODE = os.environ.get("DATABASE_SSL_MODE", "require")

TABLES = ["admin_users", "appointments", "inquiries", "site_settings"]


def get_connection():
    url = DATABASE_URL
    if not url:
        raise RuntimeError("DATABASE_URL is not set in your .env file.")
    if "sslmode" not in url:
        sep = "&" if "?" in url else "?"
        url += sep + f"sslmode={DATABASE_SSL_MODE}"
    return psycopg2.connect(url, connect_timeout=15)


def quote_value(val):
    """Safely quote a value for SQL insertion."""
    if val is None:
        return "NULL"
    val_str = str(val).replace("'", "''")
    return f"'{val_str}'"


def dump_table(cursor, table_name):
    """Generate INSERT statements for all rows in a table."""
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    col_names = [desc[0] for desc in cursor.description]

    lines = [f"\n-- Table: {table_name} ({len(rows)} rows)"]
    lines.append(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE;")

    for row in rows:
        cols = ", ".join(col_names)
        vals = ", ".join(quote_value(v) for v in row)
        lines.append(f"INSERT INTO {table_name} ({cols}) VALUES ({vals});")

    return "\n".join(lines)


def main():
    os.makedirs("backups", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backups/mindlink_backup_{timestamp}.sql"

    print("Connecting to database...")
    try:
        conn = get_connection()
    except psycopg2.OperationalError as e:
        err = str(e)
        print(f"[ERROR] Connection failed: {err}")
        if "password authentication" in err.lower():
            print()
            print("  The database password is incorrect or has changed.")
            print("  To fix:")
            print("    1. Go to https://supabase.com/dashboard")
            print("    2. Open your project -> Settings -> Database")
            print("    3. Copy the new connection string (URI)")
            print("    4. Update DATABASE_URL in your .env file")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        sys.exit(1)

    cursor = conn.cursor()

    print(f"Exporting tables: {', '.join(TABLES)}")
    output_lines = [
        "-- Mind Link Database Backup",
        f"-- Created: {datetime.now().isoformat()}",
        "-- To restore: paste this into the Supabase SQL Editor\n",
        "BEGIN;",
    ]

    for table in TABLES:
        try:
            output_lines.append(dump_table(cursor, table))
            print(f"  [OK] {table}")
        except Exception as e:
            print(f"  [SKIP] {table}: {e}")

    output_lines.append("\nCOMMIT;")

    cursor.close()
    conn.close()

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    size_kb = os.path.getsize(filename) / 1024
    print(f"\n[DONE] Backup saved to: {filename}  ({size_kb:.1f} KB)")
    print("       Store this file somewhere safe (Google Drive, email, etc.)")


if __name__ == "__main__":
    main()
