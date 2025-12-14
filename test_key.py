import os
from dotenv import load_dotenv

# 1. Try loading .env normally
print("--- Loading .env ---")
loaded = load_dotenv() 
print(f"Did .env file load? {loaded}")

# 2. Check the key
key = os.getenv("OPENAI_API_KEY")
if key:
    print(f"✅ Success! Found key starting with: {key[:8]}...")
    
    # Check for hidden spaces (common error)
    if key.startswith(" "):
        print("❌ WARNING: Your key has a leading space! Delete the space after '=' in .env")
    if key.endswith(" "):
        print("❌ WARNING: Your key has a trailing space!")
else:
    print("❌ ERROR: Key is None. Python cannot see the variable.")

# 3. Print current directory to check where we are
print(f"Current working directory: {os.getcwd()}")
print("Files in this directory:")
print(os.listdir(os.getcwd()))