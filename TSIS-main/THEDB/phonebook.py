import psycopg2
import json

# Настройки подключения (лучше вынести в config.py, но оставим здесь для наглядности)
conn = psycopg2.connect(
    dbname="suppliers",
    user="postgres",
    password="Alim1234",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

# HELPER: GET OR CREATE GROUP (Процедура move_to_group сделает это в БД, но для Python оставим так)
def get_group_id(group_name):
    if not group_name: return None
    cur.execute("SELECT id FROM groups WHERE name=%s", (group_name,))
    res = cur.fetchone()
    if res:
        return res[0]
    else:
        cur.execute("INSERT INTO groups(name) VALUES (%s) RETURNING id", (group_name,))
        gid = cur.fetchone()[0]
        conn.commit()
        return gid

# 1. ADD CONTACT (С учетом новой схемы)
def add_contact():
    name = input("Name: ")
    email = input("Email: ")
    birthday = input("Birthday (YYYY-MM-DD): ")
    group_name = input("Group (Family/Work/etc): ")
    phone = input("Phone: ")
    phone_type = input("Type (home/work/mobile): ")

    gid = get_group_id(group_name)

    cur.execute("SELECT id FROM contacts WHERE name=%s", (name,))
    existing = cur.fetchone()

    if existing:
        choice = input("Contact exists. Overwrite? (yes/no): ")
        if choice.lower() != "yes":
            print("Skipped")
            return
        
        # Обновляем основные данные
        cur.execute("""
            UPDATE contacts 
            SET email=%s, birthday=%s, group_id=%s 
            WHERE name=%s
        """, (email, birthday, gid, name))
        print("Contact updated.")
    else:
        # Создаем новый контакт
        cur.execute("""
            INSERT INTO contacts(name, email, birthday, group_id) 
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (name, email, birthday, gid))
        contact_id = cur.fetchone()[0]
        
        # Добавляем телефон в таблицу phones
        cur.execute("""
            INSERT INTO phones(contact_id, phone, type) 
            VALUES (%s, %s, %s)
        """, (contact_id, phone, phone_type))
        print("Contact and phone added!")
    
    conn.commit()

# 2. ADD PHONE (Через процедуру add_phone)
def add_phone():
    name = input("Contact Name: ")
    phone = input("New phone: ")
    p_type = input("Type (home/work/mobile): ")

    try:
        cur.execute("CALL add_phone(%s, %s, %s)", (name, phone, p_type))
        conn.commit()
        print("Phone added via procedure!")
    except Exception as e:
        conn.rollback()
        print("Error:", e)

# 3. FILTER BY GROUP
def filter_group():
    group_name = input("Group name to filter: ")
    cur.execute("""
        SELECT c.name, c.email, g.name
        FROM contacts c
        JOIN groups g ON c.group_id = g.id
        WHERE g.name = %s
    """, (group_name,))
    
    rows = cur.fetchall()
    for row in rows:
        print(f"Name: {row[0]}, Email: {row[1]}, Group: {row[2]}")

# 4. SEARCH (Через функцию search_contacts)
def search():
    q = input("Search (name/email/phone): ")
    cur.execute("SELECT * FROM search_contacts(%s)", (q,))
    rows = cur.fetchall()
    
    if not rows:
        print("No results")
    else:
        print("\nResults (Name, Email, Phone, Type):")
        for row in rows:
            print(row)

# 5. SORT
def sort_contacts():
    print("Sort by: 1. name, 2. birthday, 3. created_at")
    choice = input("Choice: ")
    fields = {"1": "name", "2": "birthday", "3": "created_at"}
    field = fields.get(choice, "name")

    cur.execute(f"""
        SELECT name, email, birthday 
        FROM contacts 
        ORDER BY {field}
    """)
    for row in cur.fetchall():
        print(row)

# 6. PAGINATION
def paginate():
    limit = 3
    offset = 0
    while True:
        cur.execute("""
            SELECT name, email FROM contacts 
            ORDER BY name LIMIT %s OFFSET %s
        """, (limit, offset))
        rows = cur.fetchall()
        
        if not rows and offset > 0:
            print("No more data")
            offset -= limit
            continue
        elif not rows:
            print("List is empty")
            break

        print(f"\n--- Page (Offset: {offset}) ---")
        for r in rows:
            print(r)

        cmd = input("\n[n]ext / [p]rev / [q]uit: ").lower()
        if cmd == "n":
            offset += limit
        elif cmd == "p":
            offset = max(0, offset - limit)
        else:
            break

# 7. EXPORT JSON
def export_json():
    cur.execute("""
        SELECT c.name, c.email, c.birthday, g.name, 
               array_agg(p.phone || ' (' || p.type || ')')
        FROM contacts c
        LEFT JOIN groups g ON c.group_id = g.id
        LEFT JOIN phones p ON c.id = p.contact_id
        GROUP BY c.id, g.name
    """)
    
    data = []
    for row in cur.fetchall():
        data.append({
            "name": row[0],
            "email": row[1],
            "birthday": str(row[2]),
            "group": row[3],
            "phones": row[4]
        })

    with open("contacts.json", "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print("Exported to contacts.json!")

# 8. IMPORT JSON
def import_json():
    try:
        with open("contacts.json", "r", encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("File not found")
        return

    for c in data:
        gid = get_group_id(c["group"])
        cur.execute("SELECT id FROM contacts WHERE name=%s", (c["name"],))
        if cur.fetchone():
            choice = input(f"Contact {c['name']} exists. [s]kip or [o]verwrite? ").lower()
            if choice == 's': continue
            cur.execute("DELETE FROM contacts WHERE name=%s", (c["name"],))

        cur.execute("""
            INSERT INTO contacts(name, email, birthday, group_id) 
            VALUES (%s, %s, %s, %s)
        """, (c["name"], c["email"], c["birthday"], gid))
    
    conn.commit()
    print("Import completed!")

# 9. DELETE (Процедура из практики 8)
def delete_contact():
    name = input("Name to delete: ")
    try:
        cur.execute("CALL delete_contact(%s)", (name,))
        conn.commit()
        print("Deleted!")
    except Exception as e:
        conn.rollback()
        print("Error (make sure procedure delete_contact exists):", e)

# MAIN MENU
def menu():
    while True:
        print("\n--- PhoneBook Advanced ---")
        print("1. Add Contact & Phone")
        print("2. Add Phone to existing (Proc)")
        print("3. Filter by Group")
        print("4. Advanced Search (Func)")
        print("5. Sort Contacts")
        print("6. Paginated View")
        print("7. Export JSON")
        print("8. Import JSON")
        print("9. Delete Contact")
        print("0. Exit")

        ch = input("\nChoose: ")
        if ch == "1": add_contact()
        elif ch == "2": add_phone()
        elif ch == "3": filter_group()
        elif ch == "4": search()
        elif ch == "5": sort_contacts()
        elif ch == "6": paginate()
        elif ch == "7": export_json()
        elif ch == "8": import_json()
        elif ch == "9": delete_contact()
        elif ch == "0": break
        else: print("Invalid choice")




        

if __name__ == "__main__":
    menu()