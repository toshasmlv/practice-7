"""
PhoneBook Application — backed by PostgreSQL
=============================================
Usage:
    python phonebook.py

Requirements:
    pip install psycopg2-binary
    A database.ini file with [postgresql] section (see README below).

database.ini template
---------------------
[postgresql]
host=localhost
database=phonebook_db
user=postgres
password=yourpassword
"""

import csv
import psycopg2
from connect import connect
from config import load_config


# ─────────────────────────────────────────────
# 1. TABLE SETUP
# ─────────────────────────────────────────────

def create_table(conn):
    """Create the contacts table if it does not already exist."""
    sql = """
        CREATE TABLE IF NOT EXISTS contacts (
            id         SERIAL PRIMARY KEY,
            first_name VARCHAR(50)  NOT NULL,
            last_name  VARCHAR(50)  NOT NULL,
            phone      VARCHAR(20)  NOT NULL UNIQUE
        );
    """
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        print('Table "contacts" is ready.')
    except (Exception, psycopg2.DatabaseError) as error:
        conn.rollback()
        print(f'Error creating table: {error}')


# ─────────────────────────────────────────────
# 2. INSERT — from CSV file
# ─────────────────────────────────────────────

def insert_from_csv(conn, filepath='contacts.csv'):
    """
    Read a CSV file and bulk-insert all rows into the contacts table.
    Expected columns: first_name, last_name, phone
    Duplicate phone numbers are skipped (ON CONFLICT DO NOTHING).
    """
    sql = """
        INSERT INTO contacts (first_name, last_name, phone)
        VALUES (%s, %s, %s)
        ON CONFLICT (phone) DO NOTHING;
    """
    rows = []
    try:
        with open(filepath, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append((row['first_name'], row['last_name'], row['phone']))
    except FileNotFoundError:
        print(f'CSV file not found: {filepath}')
        return

    try:
        with conn.cursor() as cur:
            cur.executemany(sql, rows)
        conn.commit()
        print(f'Inserted {len(rows)} rows from "{filepath}" (duplicates skipped).')
    except (Exception, psycopg2.DatabaseError) as error:
        conn.rollback()
        print(f'Error inserting from CSV: {error}')


# ─────────────────────────────────────────────
# 3. INSERT — from console input
# ─────────────────────────────────────────────

def insert_from_console(conn):
    """Prompt the user for a contact and insert it into the database."""
    print('\n--- Add New Contact ---')
    first_name = input('First name : ').strip()
    last_name  = input('Last name  : ').strip()
    phone      = input('Phone      : ').strip()

    if not (first_name and last_name and phone):
        print('All fields are required. Aborting.')
        return

    sql = """
        INSERT INTO contacts (first_name, last_name, phone)
        VALUES (%s, %s, %s)
        ON CONFLICT (phone) DO NOTHING
        RETURNING id;
    """
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (first_name, last_name, phone))
            result = cur.fetchone()
        conn.commit()
        if result:
            print(f'Contact added with id={result[0]}.')
        else:
            print('Phone number already exists — contact not inserted.')
    except (Exception, psycopg2.DatabaseError) as error:
        conn.rollback()
        print(f'Error inserting contact: {error}')


# ─────────────────────────────────────────────
# 4. UPDATE — name or phone
# ─────────────────────────────────────────────

def update_contact(conn):
    """Update first name, last name, or phone for a contact found by current phone."""
    print('\n--- Update Contact ---')
    old_phone = input('Enter the current phone number to find the contact: ').strip()

    # Show what we found first
    contact = search_by_phone(conn, old_phone, print_results=True)
    if not contact:
        print('No contact found with that phone number.')
        return

    print('What would you like to update?')
    print('  1 - First name')
    print('  2 - Last name')
    print('  3 - Phone number')
    choice = input('Choice: ').strip()

    field_map = {'1': ('first_name', 'First name'), '2': ('last_name', 'Last name'), '3': ('phone', 'Phone')}
    if choice not in field_map:
        print('Invalid choice.')
        return

    column, label = field_map[choice]
    new_value = input(f'New {label}: ').strip()
    if not new_value:
        print('Value cannot be empty. Aborting.')
        return

    sql = f'UPDATE contacts SET {column} = %s WHERE phone = %s;'
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (new_value, old_phone))
            updated = cur.rowcount
        conn.commit()
        if updated:
            print(f'Contact updated successfully.')
        else:
            print('No rows updated.')
    except (Exception, psycopg2.DatabaseError) as error:
        conn.rollback()
        print(f'Error updating contact: {error}')


# ─────────────────────────────────────────────
# 5. QUERY — various filters
# ─────────────────────────────────────────────

def _print_contacts(rows):
    """Pretty-print a list of contact rows."""
    if not rows:
        print('  (no results)')
        return
    print(f'\n  {"ID":<5} {"First Name":<15} {"Last Name":<15} {"Phone":<20}')
    print('  ' + '-' * 57)
    for row in rows:
        print(f'  {row[0]:<5} {row[1]:<15} {row[2]:<15} {row[3]:<20}')
    print()


def search_by_name(conn, name_fragment):
    """Return all contacts whose first OR last name contains the given fragment."""
    sql = """
        SELECT id, first_name, last_name, phone
        FROM contacts
        WHERE first_name ILIKE %s OR last_name ILIKE %s
        ORDER BY last_name, first_name;
    """
    pattern = f'%{name_fragment}%'
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (pattern, pattern))
            rows = cur.fetchall()
        _print_contacts(rows)
        return rows
    except (Exception, psycopg2.DatabaseError) as error:
        print(f'Error querying by name: {error}')
        return []


def search_by_phone(conn, phone_fragment, print_results=False):
    """Return contacts whose phone starts with the given prefix."""
    sql = """
        SELECT id, first_name, last_name, phone
        FROM contacts
        WHERE phone LIKE %s
        ORDER BY phone;
    """
    pattern = f'{phone_fragment}%'
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (pattern,))
            rows = cur.fetchall()
        if print_results:
            _print_contacts(rows)
        return rows
    except (Exception, psycopg2.DatabaseError) as error:
        print(f'Error querying by phone: {error}')
        return []


def list_all(conn):
    """Retrieve and display every contact."""
    sql = 'SELECT id, first_name, last_name, phone FROM contacts ORDER BY last_name, first_name;'
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
        print(f'\n--- All Contacts ({len(rows)} total) ---')
        _print_contacts(rows)
    except (Exception, psycopg2.DatabaseError) as error:
        print(f'Error listing contacts: {error}')


# ─────────────────────────────────────────────
# 6. DELETE — by username or phone
# ─────────────────────────────────────────────

def delete_contact(conn):
    """Delete a contact by username (first+last) or phone number."""
    print('\n--- Delete Contact ---')
    print('  1 - Delete by phone number')
    print('  2 - Delete by full name (first + last)')
    choice = input('Choice: ').strip()

    try:
        with conn.cursor() as cur:
            if choice == '1':
                phone = input('Phone number: ').strip()
                cur.execute('DELETE FROM contacts WHERE phone = %s;', (phone,))
            elif choice == '2':
                first = input('First name: ').strip()
                last  = input('Last name : ').strip()
                cur.execute(
                    'DELETE FROM contacts WHERE first_name ILIKE %s AND last_name ILIKE %s;',
                    (first, last)
                )
            else:
                print('Invalid choice.')
                return

            deleted = cur.rowcount
        conn.commit()
        print(f'{deleted} contact(s) deleted.')
    except (Exception, psycopg2.DatabaseError) as error:
        conn.rollback()
        print(f'Error deleting contact: {error}')


# ─────────────────────────────────────────────
# 7. MAIN MENU
# ─────────────────────────────────────────────

MENU = """
╔══════════════════════════════════════╗
║         PhoneBook Application        ║
╠══════════════════════════════════════╣
║  1  Load contacts from CSV           ║
║  2  Add contact (console input)      ║
║  3  Update a contact                 ║
║  4  Search by name                   ║
║  5  Search by phone prefix           ║
║  6  List all contacts                ║
║  7  Delete a contact                 ║
║  0  Exit                             ║
╚══════════════════════════════════════╝
"""


def main():
    config = load_config()
    conn = connect(config)
    if conn is None:
        print('Could not connect to the database. Check database.ini.')
        return

    create_table(conn)

    while True:
        print(MENU)
        choice = input('Select an option: ').strip()

        if choice == '1':
            path = input('CSV file path [contacts.csv]: ').strip() or 'contacts.csv'
            insert_from_csv(conn, path)

        elif choice == '2':
            insert_from_console(conn)

        elif choice == '3':
            update_contact(conn)

        elif choice == '4':
            fragment = input('Enter name (or fragment) to search: ').strip()
            search_by_name(conn, fragment)

        elif choice == '5':
            prefix = input('Enter phone prefix to search: ').strip()
            rows = search_by_phone(conn, prefix, print_results=False)
            print(f'\n--- Results for prefix "{prefix}" ---')
            _print_contacts(rows)

        elif choice == '6':
            list_all(conn)

        elif choice == '7':
            delete_contact(conn)

        elif choice == '0':
            print('Goodbye!')
            break

        else:
            print('Unknown option. Please try again.')

    conn.close()


if __name__ == '__main__':
    main()