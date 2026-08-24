/* Permissions */

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
