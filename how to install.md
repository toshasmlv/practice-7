# Practice7 — PhoneBook (PostgreSQL + Python)

## Setup

### 1. Install dependency
```bash
pip install psycopg2-binary
```

### 2. Create the database
```bash
psql -U postgres
```
```sql
CREATE DATABASE phonebook_db;
\q
```

### 3. Create `database.ini`
```ini
[postgresql]
host=localhost
database=phonebook_db
user=postgres
password=yourpassword
```
> ⚠️ Add `database.ini` to `.gitignore` — never commit credentials.

### 4. Run the app
```bash
python phonebook.py
```

## File Structure
```
Practice7/
├── phonebook.py     # Main application (menu + all CRUD operations)
├── config.py        # Reads database.ini connection parameters
├── connect.py       # Creates and tests the psycopg2 connection
├── contacts.csv     # Sample contacts for bulk import
└── database.ini     # ← you create this (not committed to git)
```

## Features
| # | Feature |
|---|---------|
| 1 | Load contacts from a CSV file (bulk insert, duplicates skipped) |
| 2 | Add a contact from console input |
| 3 | Update first name, last name, or phone |
| 4 | Search by name (partial, case-insensitive) |
| 5 | Search by phone prefix |
| 6 | List all contacts |
| 7 | Delete by phone number or full name |

## Key psycopg2 Concepts Covered
- `psycopg2.connect(**config)` — open connection
- `conn.cursor()` — create cursor for executing SQL
- `cur.execute(sql, params)` — parameterised query (safe from SQL injection)
- `cur.executemany(sql, list)` — bulk insert
- `cur.fetchone()` / `cur.fetchall()` — retrieve results
- `conn.commit()` / `conn.rollback()` — transaction control
- `ON CONFLICT (phone) DO NOTHING` — handle unique constraint gracefully
