# -*- coding: utf-8 -*-
"""
Mind Link -- SQLite to Supabase Migration Script
Run ONCE to import existing data from mind_link.db into Supabase PostgreSQL.

Usage:
    python migrate_to_supabase.py
"""

import os
import sys
import sqlite3
import psycopg2
from dotenv import load_dotenv

# Force UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

load_dotenv()

# -- Source: local SQLite
SQLITE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mind_link.db')

# -- Destination: Supabase PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL', '')
if 'sslmode' not in DATABASE_URL:
    sep = '&' if '?' in DATABASE_URL else '?'
    DATABASE_URL += sep + 'sslmode=require'


def migrate():
    print("=" * 60)
    print("  Mind Link -- SQLite to Supabase Migration")
    print("=" * 60)

    # -- Connect to both databases
    print("\n[1] Opening SQLite:", SQLITE_PATH)
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row

    print("[2] Connecting to Supabase...")
    pg_conn = psycopg2.connect(DATABASE_URL)
    pg_cursor = pg_conn.cursor()
    print("    Connected!\n")

    # -- Migrate appointments
    print("[3] Migrating appointments...")
    apts = sqlite_conn.execute("SELECT * FROM appointments ORDER BY id").fetchall()
    print("    Found %d appointments in SQLite" % len(apts))

    inserted_apts = 0
    skipped_apts = 0
    for row in apts:
        try:
            pg_cursor.execute('''
                INSERT INTO appointments
                    (id, name, email, phone, preferred_date, preferred_time,
                     service_type, message, status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            ''', (
                row['id'], row['name'], row['email'], row['phone'],
                row['preferred_date'], row['preferred_time'],
                row['service_type'], row['message'], row['status'],
                row['created_at'], row['updated_at']
            ))
            if pg_cursor.rowcount > 0:
                inserted_apts += 1
                print("    OK [%d] %s | %s | %s" % (
                    row['id'], row['name'], row['preferred_date'], row['status']))
            else:
                skipped_apts += 1
                print("    SKIP [%d] %s already exists" % (row['id'], row['name']))
        except Exception as e:
            print("    FAIL [%d] %s : %s" % (row['id'], row['name'], e))

    # -- Migrate inquiries
    print("\n[4] Migrating inquiries...")
    inqs = sqlite_conn.execute("SELECT * FROM inquiries ORDER BY id").fetchall()
    print("    Found %d inquiries in SQLite" % len(inqs))

    inserted_inqs = 0
    for row in inqs:
        try:
            pg_cursor.execute('''
                INSERT INTO inquiries (id, name, email, subject, message, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            ''', (row['id'], row['name'], row['email'],
                  row['subject'], row['message'], row['created_at']))
            if pg_cursor.rowcount > 0:
                inserted_inqs += 1
                print("    OK [%d] %s | %s" % (row['id'], row['name'], row['subject']))
        except Exception as e:
            print("    FAIL [%d] %s : %s" % (row['id'], row['name'], e))

    # -- Migrate admin users
    print("\n[5] Migrating admin users...")
    admins = sqlite_conn.execute("SELECT * FROM admin_users ORDER BY id").fetchall()
    print("    Found %d admin user(s) in SQLite" % len(admins))

    inserted_admins = 0
    for row in admins:
        try:
            pg_cursor.execute('''
                INSERT INTO admin_users (id, username, password_hash, created_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (username) DO NOTHING
            ''', (row['id'], row['username'], row['password_hash'], row['created_at']))
            if pg_cursor.rowcount > 0:
                inserted_admins += 1
                print("    OK [%d] %s" % (row['id'], row['username']))
            else:
                print("    SKIP [%d] %s already exists" % (row['id'], row['username']))
        except Exception as e:
            print("    FAIL [%d] %s : %s" % (row['id'], row['username'], e))

    # -- Reset sequences so next INSERT gets the right ID
    print("\n[6] Resetting PostgreSQL sequences...")
    for table in ['appointments', 'inquiries', 'admin_users']:
        pg_cursor.execute("""
            SELECT setval(
                pg_get_serial_sequence('%s', 'id'),
                COALESCE((SELECT MAX(id) FROM %s), 0) + 1,
                false
            )
        """ % (table, table))
        next_id = pg_cursor.fetchone()[0]
        print("    %s : next ID will be %d" % (table, next_id))

    # -- Commit everything
    pg_conn.commit()
    pg_cursor.close()
    pg_conn.close()
    sqlite_conn.close()

    print("\n" + "=" * 60)
    print("  Migration Complete!")
    print("  Appointments : %d inserted, %d skipped" % (inserted_apts, skipped_apts))
    print("  Inquiries    : %d inserted" % inserted_inqs)
    print("  Admin users  : %d inserted" % inserted_admins)
    print("=" * 60)
    print("\nNext: python app.py  -- verify the admin dashboard shows correct counts")


if __name__ == '__main__':
    migrate()
