"""
Checks what the app's own database account can actually do.

Two ways to run it:

    python -m Data.check_access          from the project root
    <app url>/diag                       in the browser, no login needed

It connects with exactly the credentials in Data/auth_public.py, on its own
connection with short timeouts, so a table that is missing, forbidden or
locked shows up as a line in the report instead of a page that never loads.
"""

import os
import sys

import psycopg2
import psycopg2.errors

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

PROBE_TIMEOUT_MS = 5000

HINTS = [
    "MISSING  ->  run Data/create_database.sql, then Data/migrations.sql",
    "             and Data/trivia_questions.sql on the database.",
    "FAIL     ->  run Data/grants.sql as the OWNER of that table. It only",
    "             affects tables the role running it owns, so if you both",
    "             created tables, you both have to run it.",
    "LOCKED   ->  a psql or pgAdmin window has an open transaction on that",
    "             table. COMMIT it or close the window. An unfinished",
    "             ALTER TABLE blocks every read of that table.",
]


def collect():
    """Returns (lines, problems)."""
    lines = []
    problems = []

    port = os.environ.get('POSTGRES_PORT', 5432)
    lines.append(f"database {auth.db} on {auth.host}:{port} as {auth.user}")

    try:
        conn = psycopg2.connect(
            database=auth.db, host=auth.host, user=auth.user,
            password=auth.password, port=port, connect_timeout=10,
            options=(f'-c statement_timeout={PROBE_TIMEOUT_MS} '
                     f'-c lock_timeout={PROBE_TIMEOUT_MS}'))
    except Exception as exc:
        lines.append(f"  CANNOT CONNECT  {type(exc).__name__}: {exc}")
        problems.append("the app cannot reach the database at all")
        return lines, problems

    cur = conn.cursor()
    cur.execute("SELECT current_user, current_database()")
    who, where = cur.fetchone()
    lines.append(f"connected as {who} to {where}")
    lines.append("")

    for table in TABLES:
        try:
            line, problem = _probe(cur, table)
        except (psycopg2.errors.QueryCanceled,
                psycopg2.errors.LockNotAvailable):
            conn.rollback()
            line = (f"  LOCKED    {table}  -  another session is holding a "
                    f"lock on it")
            problem = f"{table} is locked by another session"
        except Exception as exc:
            conn.rollback()
            line = f"  FAIL      {table}  -  {type(exc).__name__}: {exc}"
            problem = f"{table}: {type(exc).__name__}"

        lines.append(line)
        if problem:
            problems.append(problem)

    lines.append("")
    if problems:
        lines.append("PROBLEMS FOUND:")
        lines.extend("  - " + p for p in problems)
        lines.append("")
        lines.extend(HINTS)
    else:
        lines.append("All good - the app has everything it needs.")

    conn.close()
    return lines, problems


def _probe(cur, table):
    """One table -> (line, problem or None). May raise; collect() handles it."""
    cur.execute("SELECT to_regclass(%s)", ('public.' + table,))
    if cur.fetchone()[0] is None:
        return f"  MISSING   {table}", f"{table} does not exist"

    cur.execute("""
        SELECT has_table_privilege(%s, 'SELECT'),
               has_table_privilege(%s, 'INSERT'),
               has_table_privilege(%s, 'UPDATE')
    """, (table, table, table))
    can_select, can_insert, can_update = cur.fetchone()

    missing = [name for name, ok in (('SELECT', can_select),
                                     ('INSERT', can_insert),
                                     ('UPDATE', can_update)) if not ok]

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

    if sequence:
        cur.execute("SELECT has_sequence_privilege(%s, 'USAGE')", (sequence,))
        if not cur.fetchone()[0]:
            missing.append('USAGE on ' + sequence)

    if missing:
        return (f"  FAIL      {table}  -  missing {', '.join(missing)}",
                f"{table}: missing {', '.join(missing)}")

    # Privileges can be fine while the table is still unreachable, because an
    # open transaction elsewhere holds a lock on it. That is the case that
    # hangs a page instead of erroring, so read the table for real.
    cur.execute(f"SELECT count(*) FROM {table}")
    return f"  OK        {table}  ({cur.fetchone()[0]} rows)", None


def main():
    lines, problems = collect()
    print('\n'.join(lines))
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
