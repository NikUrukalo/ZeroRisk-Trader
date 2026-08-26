/* Permissions
 *
 * Run this as the OWNER of the tables, every time you add a table or a
 * sequence. GRANT ... ON ALL TABLES only touches tables the role running it
 * owns, so if both of you have created tables, both of you have to run it.
 * Data/check_access.py says whether it worked.
 */

-- allow connecting to the DB
GRANT CONNECT ON DATABASE sem2026_nejczi TO javnost;
GRANT CONNECT ON DATABASE sem2026_nejczi TO nikuru;

-- allow usage of the schema
GRANT USAGE ON SCHEMA public TO javnost;
GRANT USAGE ON SCHEMA public TO nikuru;

-- grant privileges on all existing tables in the schema
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO javnost;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO nikuru;

-- grant privileges on all existing sequences in the schema
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO javnost;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO nikuru;


/* The blocks above only cover tables that exist right now. A table created
 * afterwards has no privileges at all and the app dies with
 * "permission denied for table <name>". These say "and everything I create
 * from now on too". The rule belongs to the role that runs CREATE TABLE, so
 * there is one block per person.
 */

ALTER DEFAULT PRIVILEGES FOR ROLE nejczi IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO javnost, nikuru;
ALTER DEFAULT PRIVILEGES FOR ROLE nejczi IN SCHEMA public
    GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO javnost, nikuru;

ALTER DEFAULT PRIVILEGES FOR ROLE nikuru IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO javnost, nejczi;
ALTER DEFAULT PRIVILEGES FOR ROLE nikuru IN SCHEMA public
    GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO javnost, nejczi;
