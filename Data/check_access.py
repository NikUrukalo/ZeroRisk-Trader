"""
Checks what the app's own database account is allowed to do.

Run it from the project root, on the machine where the app runs. In a Binder
terminal:

    POSTGRES_PORT=443 python -m Data.check_access

It connects with exactly the credentials in Data/auth_public.py, so what it
prints is what the app itself would hit. A FAIL line names the table to fix.
"""

import os
import sys

import psycopg2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Data import auth_public as auth   # noqa: E402

TABLES = [
    'app_user',
    'portfolio',
    'asset_master',
    'asset',
    'position',
    'trade',
    'trivia_question',
    'trivia_attempt',
    'daily_bonus',
]

# tables the app writes to, and therefore needs the SERIAL sequence for
NEEDS_INSERT = TABLES


def main():
    print(f"connecting to {auth.db} on {auth.host} as {auth.user} ...")

    conn = psycopg2.connect(database=auth.db,
                            host=auth.host,
                            user=auth.user,
                            password=auth.password,
                            port=os.environ.get('POSTGRES_PORT', 5432),
                            connect_timeout=10)
    cur = conn.cursor()

    cur.execute("SELECT current_user, current_database()")
    who, where = cur.fetchone()
    print(f"connected as {who} to {where}\n")

    problems = []

    for table in TABLES:
        cur.execute("SELECT to_regclass(%s)", ('public.' + table,))
        if cur.fetchone()[0] is None:
            print(f"  MISSING   {table}")
            problems.append(f"{table} does not exist")
            continue

        cur.execute("""
            SELECT has_table_privilege(%s, 'SELECT'),
                   has_table_privilege(%s, 'INSERT'),
                   has_table_privilege(%s, 'UPDATE')
        """, (table, table, table))
        can_select, can_insert, can_update = cur.fetchone()

        cur.execute("""
            SELECT pg_get_serial_sequence(%s, column_name)
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
              AND column_default LIKE 'nextval%%'
            LIMIT 1
        """, ('public.' + table, table))
        row = cur.fetchone()
        sequence = row[0] if row else None

        missing = []
        if not can_select:
            missing.append('SELECT')
        if table in NEEDS_INSERT and not can_insert:
            missing.append('INSERT')
        if table in NEEDS_INSERT and not can_update:
            missing.append('UPDATE')

        if sequence:
            cur.execute("SELECT has_sequence_privilege(%s, 'USAGE')",
                        (sequence,))
            if not cur.fetchone()[0]:
                missing.append('USAGE on ' + sequence)

        if missing:
            print(f"  FAIL      {table}  -  missing {', '.join(missing)}")
            problems.append(f"{table}: {', '.join(missing)}")
        else:
            print(f"  OK        {table}")

    # count the quiz questions, since an empty table looks like a broken page
    cur.execute("SELECT to_regclass('public.trivia_question')")
    if cur.fetchone()[0] is not None:
        try:
            cur.execute("SELECT count(*) FROM trivia_question")
            n = cur.fetchone()[0]
            print(f"\n  trivia_question holds {n} question(s)")
            if n == 0:
                problems.append("trivia_question is empty")
        except psycopg2.Error:
            conn.rollback()

    print()
    if problems:
        print("PROBLEMS FOUND:")
        for p in problems:
            print("  - " + p)
        print("\nFix: run Data/migrations.sql and then Data/grants.sql on the")
        print("database. grants.sql only affects tables the role running it")
        print("owns, so if you and your partner both created tables, you both")
        print("have to run it.")
    else:
        print("All good - the app has everything it needs.")

    conn.close()
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
