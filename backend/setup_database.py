import sqlite3
import random
import faker  # You might need to pip install faker, or just use random strings if you prefer

# If you don't want to install faker, remove the import and use this simple generator:
# def fake_name(): return f"User_{random.randint(1000,9999)}"

fake = faker.Faker('en_IN') # Indian names

def setup_mock_db():
    conn = sqlite3.connect('mock_bank.db')
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
    
    # --- 1. INSERT SPECIFIC EDGE CASE USERS (The "Cheat Sheet") ---
    # Use these PANs during your demo to trigger specific flows
    
    edge_cases = [
        # Case A: The "Golden User" (Perfect Profile)
        ("ABCDE1000F", "Aarush Luthra", 850, 500000, "123, Tech Park, Bangalore", "9999999990"),
        
        # Case B: The "Reject" (Low Credit Score)
        ("ABCDE2000F", "Rohan Das", 600, 100000, "45, Old City, Delhi", "9999999991"),
        
        # Case C: The "Salary Slip" Case (High Limit needed, Good Score)
        # Limit is low (2L), so asking for 3L will trigger salary check
        ("ABCDE3000F", "Priya Sharma", 750, 200000, "78, Sea Link, Mumbai", "9999999992"),
        
        # Case D: The "Data Mismatch" (Name in DB is unexpected)
        ("ABCDE4000F", "Unknown User", 700, 200000, "00, Nowhere", "9999999993"),
        
        # Case E: The "Edge of Limit" (Exact Limit)
        ("ABCDE5000F", "Vikram Singh", 720, 300000, "12, Fort Road, Jaipur", "9999999994"),
    ]
    
    c.executemany('INSERT OR REPLACE INTO customers VALUES (?,?,?,?,?,?)', edge_cases)
    
    # --- 2. GENERATE 1000 RANDOM USERS ---
    print("Generating 1000 random users...")
    random_users = []
    for _ in range(1000):
        # Generate a random PAN like ABCDE1234F
        pan = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=5)) + \
              str(random.randint(1000, 9999)) + \
              random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        
        name = fake.name()
        score = random.randint(300, 900) # Full range
        limit = random.choice([50000, 100000, 200000, 500000, 1000000])
        address = fake.address().replace('\n', ', ')
        phone = f"9{random.randint(100000000, 999999999)}"
        
        random_users.append((pan, name, score, limit, address, phone))
        
    c.executemany('INSERT OR IGNORE INTO customers VALUES (?,?,?,?,?,?)', random_users)
    
    conn.commit()
    conn.close()
    print("✅ Database 'mock_bank.db' created with 1000+ records.")

if __name__ == "__main__":
    setup_mock_db()