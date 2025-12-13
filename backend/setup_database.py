# CORRECTED FILE: backend/setup_database.py
import sqlite3
import random
import faker

fake = faker.Faker('en_IN')

def setup_mock_db():
    conn = sqlite3.connect('mock_bank.db')
    # REMOVED: conn._init_db()  <-- This was the error
    c = conn.cursor()
    
    # Create Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            pan TEXT PRIMARY KEY,
            name TEXT,
            credit_score INTEGER,
            pre_approved_limit INTEGER,
            address TEXT,
            phone TEXT
        )
    ''')
    
    # ... (Rest of your code remains exactly the same) ...

    edge_cases = [
        ("ABCDE1000F", "Aarush Luthra", 850, 500000, "123, Tech Park, Bangalore", "9999999990"),
        ("ABCDE2000F", "Rohan Das", 600, 100000, "45, Old City, Delhi", "9999999991"),
        ("ABCDE3000F", "Priya Sharma", 750, 200000, "78, Sea Link, Mumbai", "9999999992"),
        ("ABCDE4000F", "Unknown User", 700, 200000, "00, Nowhere", "9999999993"),
        ("ABCDE5000F", "Vikram Singh", 720, 300000, "12, Fort Road, Jaipur", "9999999994"),
    ]
    
    c.executemany('INSERT OR REPLACE INTO customers VALUES (?,?,?,?,?,?)', edge_cases)
    
    print("Generating 1000 random users...")
    random_users = []
    for _ in range(1000):
        pan = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=5)) + \
            str(random.randint(1000, 9999)) + \
            random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        
        name = fake.name()
        score = random.randint(300, 900)
        limit = random.choice([50000, 100000, 200000, 500000, 1000000])
        address = fake.address().replace('\n', ', ')
        phone = f"9{random.randint(100000000, 999999999)}"
        
        random_users.append((pan, name, score, limit, address, phone))
        
    c.executemany('INSERT OR IGNORE INTO customers VALUES (?,?,?,?,?,?)', random_users)
    
    conn.commit()
    conn.close()
